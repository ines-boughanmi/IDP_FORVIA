"""
Chatbot router — clean, resilient, always returns {answer, results}.

Flow:
  1. RAG vector search  → top-5 relevant records
  2. Deterministic fallback (EnterpriseApiService) if RAG returns nothing
  3. Ollama LLM (llama3.2:1b) for natural-language answer
  4. Structured deterministic answer if Ollama is unavailable
"""
from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List

import requests
from fastapi import APIRouter, Request
from pydantic import BaseModel

from ..services.chatbot_service import ChatbotService
from ..services.data_loader import DataLoaderService
from ..services.enterprise_service import EnterpriseApiService
from ..services.rag_service import RAGService

router = APIRouter()
logger = logging.getLogger(__name__)


# ── helpers ───────────────────────────────────────────────────────────────────

def _ollama(prompt: str) -> str:
    """Call local Ollama and return text, or '' on any failure."""
    url     = os.getenv("OLLAMA_URL",   "http://127.0.0.1:11434/api/generate")
    model   = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
    try:
        resp = requests.post(
            url,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=15,
        )
        if not resp.ok:
            logger.warning("Ollama HTTP %s", resp.status_code)
            return ""
        data = resp.json()
        # Ollama non-stream: {"response": "..."}
        return str(data.get("response") or data.get("text") or data.get("output") or "")
    except Exception as exc:
        logger.info("Ollama unavailable (%s) — using deterministic fallback", exc)
        return ""


def _deterministic_answer(question: str, results: List[Dict]) -> str:
    """Build a concise structured answer from retrieved records."""
    q = question.lower()
    suppliers    = [r["metadata"] for r in results if r["metadata"].get("type") == "supplier"]
    transactions = [r["metadata"] for r in results if r["metadata"].get("type") == "transaction"]

    lines: List[str] = []

    if suppliers:
        lines.append("**Top risk suppliers identified:**")
        for s in sorted(suppliers, key=lambda x: float(x.get("risk_score") or 0), reverse=True)[:5]:
            sid   = s.get("supplier_id", "N/A")
            name  = s.get("supplier_name", "")
            score = s.get("risk_score", "N/A")
            level = s.get("risk_level", "N/A")
            cluster = s.get("cluster_label", "")
            line = f"• Supplier {sid}"
            if name:
                line += f" ({name})"
            line += f" — Risk Score: {score}, Level: {level}"
            if cluster:
                line += f", Cluster: {cluster}"
            lines.append(line)

    if transactions:
        lines.append("\n**Top risk transactions identified:**")
        for t in sorted(transactions, key=lambda x: float(x.get("risk_score") or 0), reverse=True)[:5]:
            tid   = t.get("transaction_id", "N/A")
            score = t.get("risk_score", "N/A")
            level = t.get("risk_level", "N/A")
            amt   = t.get("amount", "N/A")
            anom  = t.get("anomaly_classification") or ""
            line  = f"• Transaction {tid} — Risk Score: {score}, Level: {level}, Amount: {amt}"
            if anom:
                line += f", Anomaly: {anom}"
            lines.append(line)

    if not lines:
        # generic executive summary
        lines.append(
            "Based on the SAP P2P risk dataset, no specific records matched your query. "
            "Please try asking about 'high risk suppliers', 'critical transactions', "
            "'anomalies detected', or 'overall risk summary'."
        )

    return "\n".join(lines)


def _build_prompt(question: str, results: List[Dict]) -> str:
    context_lines = []
    for r in results[:5]:
        m = r["metadata"]
        doc = r.get("document", "")
        context_lines.append(doc)

    context = "\n".join(context_lines) if context_lines else "No specific records retrieved."

    return (
        "You are an expert SAP Procure-to-Pay (P2P) Risk Analyst.\n"
        "Answer in professional business English using procurement and risk management terminology.\n\n"
        f"Relevant data context:\n{context}\n\n"
        f"User question: {question}\n\n"
        "Instructions:\n"
        "- Give a concise, structured answer (3-5 sentences max).\n"
        "- Reference specific risk scores, levels, or anomaly types from the context when available.\n"
        "- If context shows critical or high-risk items, highlight them explicitly.\n"
        "- End with one actionable recommendation if appropriate.\n"
    )


# ── deterministic fallback from EnterpriseApiService ─────────────────────────

def _enterprise_fallback(
    q: str,
    data_loader: DataLoaderService,
    enterprise: EnterpriseApiService,
) -> List[Dict]:
    """Return a structured results list from deterministic queries."""
    q_lower = q.lower()
    results: List[Dict] = []

    try:
        if any(w in q_lower for w in ("supplier", "fournisseur", "vendor")):
            m = re.search(r"\b(\d{1,6})\b", q)
            if m:
                overview = enterprise.supplier_overview(int(m.group(1)))
                if overview:
                    results.append({"document": "supplier_overview",
                                    "metadata": {**overview.get("supplier_profile", {}), "type": "supplier"}})
            else:
                for sup in enterprise.top_risk_suppliers(limit=5):
                    results.append({"document": "top_supplier",
                                    "metadata": {**sup, "type": "supplier"}})

        elif any(w in q_lower for w in ("transaction", "txn", "invoice", "po")):
            m = re.search(r"\b(\d{4,12})\b", q)
            if m:
                overview = enterprise.transaction_overview(int(m.group(1)))
                if overview:
                    results.append({"document": "transaction_overview",
                                    "metadata": {**overview.get("transaction_profile", {}), "type": "transaction"}})
            else:
                for txn in data_loader.get_high_risk_transactions(limit=5):
                    results.append({"document": "top_transaction",
                                    "metadata": {**txn, "type": "transaction"}})

        elif any(w in q_lower for w in ("anomal", "anomalie", "detect")):
            summary = enterprise.anomaly_summary()
            results.append({"document": "anomaly_summary", "metadata": summary})
            for txn in data_loader.get_high_risk_transactions(limit=3):
                results.append({"document": "anomalous_txn",
                                "metadata": {**txn, "type": "transaction"}})

        else:
            # executive / general
            dashboard = enterprise.executive_dashboard()
            results.append({"document": "executive_dashboard", "metadata": dashboard})
            for sup in enterprise.top_risk_suppliers(limit=3):
                results.append({"document": "top_supplier",
                                "metadata": {**sup, "type": "supplier"}})

    except Exception:
        logger.exception("Enterprise fallback error")

    return results


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.get("/chatbot/status")
def chatbot_status(request: Request):
    rag = getattr(request.app.state, "rag_service", None)
    ready     = rag.is_ready()    if rag else False
    doc_count = rag._doc_count    if rag else 0
    return {"ready": ready, "doc_count": doc_count}


@router.get("/chatbot/debug-columns")
def debug_columns(request: Request):
    dl  = request.app.state.data_loader
    rag = getattr(request.app.state, "rag_service", None)

    sup_info = txn_info = None
    try:
        if dl.suppliers_df is not None:
            sup_info = {"shape": list(dl.suppliers_df.shape), "columns": list(dl.suppliers_df.columns)}
    except Exception as e:
        sup_info = {"error": str(e)}
    try:
        if dl.transactions_df is not None:
            txn_info = {"shape": list(dl.transactions_df.shape), "columns": list(dl.transactions_df.columns)}
    except Exception as e:
        txn_info = {"error": str(e)}

    return {
        "suppliers":    sup_info,
        "transactions": txn_info,
        "rag": {
            "exists":      rag is not None,
            "ready":       rag.is_ready()   if rag else False,
            "doc_count":   rag._doc_count   if rag else 0,
            "built_once":  rag._built_once  if rag else False,
        },
    }


class ChatRequest(BaseModel):
    question: str


@router.post("/chatbot/query")
def query_chat(payload: ChatRequest, request: Request):
    q = (payload.question or "").strip()
    if not q:
        return {"answer": "Please enter a question.", "results": []}

    dl         = request.app.state.data_loader
    enterprise = EnterpriseApiService(dl)

    # ensure rag_service exists on app state
    if not getattr(request.app.state, "rag_service", None):
        request.app.state.rag_service = RAGService(dl)
    rag: RAGService = request.app.state.rag_service

    try:
        # ── 1. RAG retrieval ──────────────────────────────────────────────────
        results: List[Dict] = []
        try:
            results = rag.query(q, top_k=5)
        except Exception:
            logger.exception("RAG query error")

        # ── 2. Deterministic fallback if RAG returned nothing ─────────────────
        if not results:
            logger.info("RAG returned 0 results — using enterprise fallback")
            results = _enterprise_fallback(q, dl, enterprise)

        # ── 3. Build prompt & call Ollama ─────────────────────────────────────
        answer = _ollama(_build_prompt(q, results))

        # ── 4. Deterministic answer if Ollama unavailable ─────────────────────
        if not answer:
            answer = _deterministic_answer(q, results)

        return {"answer": answer, "results": results}

    except Exception as exc:
        logger.exception("Unhandled chatbot error: %s", exc)
        return {
            "answer": "An internal error occurred. Please try again.",
            "results": [],
        }


@router.post("/chatbot/rebuild")
def rebuild_rag(request: Request):
    rag = getattr(request.app.state, "rag_service", None)
    if rag is None:
        dl  = request.app.state.data_loader
        rag = RAGService(dl)
        request.app.state.rag_service = rag
    try:
        rag.build_collection(limit_suppliers=500, limit_transactions=1000)
        return {"status": "ok", "doc_count": rag._doc_count, "ready": rag.is_ready()}
    except Exception as exc:
        logger.exception("Rebuild failed: %s", exc)
        return {"status": "error", "message": str(exc)}