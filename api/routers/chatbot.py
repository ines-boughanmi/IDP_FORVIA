from __future__ import annotations

import json
import logging
import threading
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from ..auth.dependencies import get_current_user
from ..auth.schemas import User
from ..db.session import SessionLocal
from ..db import crud
from ..services.groq_service import generate_answer

router = APIRouter()
logger = logging.getLogger(__name__)

_NO_INFO = (
    "I do not have enough information in the available datasets to answer that question."
)


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def _user_from_request(request: Request) -> Optional[User]:
    """Extract and verify the JWT from the Authorization header directly."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        logger.debug("_user_from_request: no Bearer token in header")
        return None
    token = auth[7:].strip()
    if not token:
        return None
    try:
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        user = get_current_user(creds)
        logger.debug("_user_from_request: authenticated as %s (id=%d)", user.username, user.id)
        return user
    except Exception as exc:
        logger.warning("_user_from_request: auth failed — %s", exc)
        return None


def _required_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
) -> User:
    try:
        return get_current_user(credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication required")


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_engine(request: Request):
    return getattr(request.app.state, "rag_engine", None)


def _deterministic_fallback(results: List[Dict[str, Any]]) -> str:
    if not results:
        return _NO_INFO
    lines: List[str] = []
    for r in results[:5]:
        meta = r.get("metadata", {})
        doc = r.get("document", "")
        if meta.get("transaction_id"):
            lines.append(
                f"Transaction {meta['transaction_id']}: "
                f"Supplier {meta.get('supplier_id', 'N/A')} — "
                f"Risk Score {meta.get('risk_score', 'N/A')}, "
                f"Risk Level {meta.get('risk_level', 'N/A')}, "
                f"Amount {meta.get('amount', 'N/A')}"
            )
        elif meta.get("supplier_id"):
            lines.append(
                f"Supplier {meta['supplier_id']} "
                f"({meta.get('supplier_name', '')}) — "
                f"Risk Score {meta.get('risk_score', 'N/A')}, "
                f"Risk Level {meta.get('risk_level', 'N/A')}, "
                f"Cluster {meta.get('cluster_label', 'N/A')}"
            )
        elif doc:
            lines.append(doc[:300])
    return "\n".join(lines) if lines else _NO_INFO


def _serialize_conv(conv, include_messages: bool = False) -> Dict:
    data: Dict[str, Any] = {
        "id":            conv.id,
        "title":         conv.title,
        "created_at":    conv.created_at.isoformat() if conv.created_at else None,
        "updated_at":    conv.updated_at.isoformat() if conv.updated_at else None,
        "message_count": len(conv.messages),
    }
    if include_messages:
        data["messages"] = [
            {
                "id":         m.id,
                "role":       m.role,
                "content":    m.content,
                "sources":    json.loads(m.sources or "[]"),
                "confidence": m.confidence or 0.0,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in conv.messages
        ]
    return data


# ---------------------------------------------------------------------------
# Status / query / reindex
# ---------------------------------------------------------------------------

@router.get("/chatbot/status")
def chatbot_status(request: Request):
    engine = _get_engine(request)
    if engine is None:
        return {"ready": False, "building": False, "documents": 0, "sources": []}
    return engine.status()


@router.post("/chatbot/query")
def query_chat(payload: ChatRequest, request: Request):
    current_user = _user_from_request(request)
    q = (payload.question or "").strip()
    if not q:
        return {
            "answer": "Please enter a question.",
            "sources": [], "confidence": 0.0, "conversation_id": None,
        }

    engine = _get_engine(request)
    if engine is None:
        return {
            "answer": (
                "The AI assistant has not been initialised yet. "
                "Please restart the server or call /api/chatbot/reindex."
            ),
            "sources": [], "confidence": 0.0, "conversation_id": None,
        }

    if not engine.is_ready():
        msg = (
            "The assistant is currently indexing the datasets. "
            "This typically takes 2–5 minutes. Please try again shortly."
            if engine._building else
            "The assistant index is not ready. "
            "Please call POST /api/chatbot/reindex to build the index."
        )
        return {"answer": msg, "sources": [], "confidence": 0.0, "conversation_id": None}

    retrieval  = engine.query(q, top_k=10)
    context    = retrieval.get("context", "")
    sources    = retrieval.get("sources", [])
    confidence = retrieval.get("confidence", 0.0)

    if not context.strip():
        answer     = _NO_INFO
        sources    = []
        confidence = 0.0
    else:
        answer = generate_answer(context, q)
        if not answer:
            logger.warning("LLM unavailable — using deterministic fallback")
            answer = _deterministic_fallback(retrieval.get("results", []))

    # Persist to history when authenticated
    conv_id: Optional[int] = None
    if current_user is not None:
        logger.info("Saving conversation for user %s (id=%d)", current_user.username, current_user.id)
        db = SessionLocal()
        try:
            conv_id = payload.conversation_id
            if conv_id is not None:
                conv = crud.get_conversation(db, conv_id, current_user.id)
                if not conv:
                    logger.warning("conversation_id=%d not found for user %d — creating new", conv_id, current_user.id)
                    conv_id = None
            if conv_id is None:
                title = q[:80] + ("…" if len(q) > 80 else "")
                conv = crud.create_conversation(db, current_user.id, title)
                conv_id = conv.id
                logger.info("Created conversation %d: %r", conv_id, title)
            crud.add_message(db, conv_id, "user", q)
            crud.add_message(
                db, conv_id, "assistant", answer,
                sources=sources, confidence=float(confidence),
            )
            conv = crud.get_conversation(db, conv_id, current_user.id)
            if conv:
                crud.touch_conversation(db, conv)
            logger.info("Conversation %d saved (%d messages)", conv_id, len(conv.messages) if conv else -1)
        except Exception:
            logger.exception("Failed to save conversation history")
            conv_id = None
        finally:
            db.close()
    else:
        logger.warning("query_chat: no authenticated user — conversation not saved")

    return {
        "answer":          answer,
        "sources":         sources,
        "confidence":      confidence,
        "conversation_id": conv_id,
    }


@router.post("/chatbot/reindex")
def reindex(request: Request):
    engine = _get_engine(request)
    if engine is None:
        return {"status": "error", "message": "RAG engine not available on app state"}
    if engine._building:
        return {"status": "already_running", "message": "Index rebuild is already in progress"}

    def _rebuild():
        try:
            engine.build_index(force=True)
            logger.info("Reindex complete — %d documents", engine._doc_count)
        except Exception:
            logger.exception("Reindex failed")

    threading.Thread(target=_rebuild, daemon=True, name="rag-reindex").start()
    return {"status": "rebuilding", "message": "Index rebuild started in background"}


# ---------------------------------------------------------------------------
# Conversation history
# ---------------------------------------------------------------------------

@router.get("/chatbot/conversations")
def list_conversations(current_user: User = Depends(_required_user)):
    db = SessionLocal()
    try:
        convs = crud.get_conversations(db, current_user.id)
        return [_serialize_conv(c) for c in convs]
    finally:
        db.close()


@router.get("/chatbot/conversations/{conv_id}")
def get_conversation_detail(conv_id: int, current_user: User = Depends(_required_user)):
    db = SessionLocal()
    try:
        conv = crud.get_conversation(db, conv_id, current_user.id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return _serialize_conv(conv, include_messages=True)
    finally:
        db.close()


@router.delete("/chatbot/conversations")
def delete_all_conversations(current_user: User = Depends(_required_user)):
    db = SessionLocal()
    try:
        count = crud.delete_all_conversations(db, current_user.id)
        return {"deleted": count}
    finally:
        db.close()


@router.delete("/chatbot/conversations/{conv_id}")
def delete_conversation(conv_id: int, current_user: User = Depends(_required_user)):
    db = SessionLocal()
    try:
        ok = crud.delete_conversation(db, conv_id, current_user.id)
        if not ok:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"deleted": conv_id}
    finally:
        db.close()
