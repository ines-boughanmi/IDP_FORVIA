"""
RAG service — pure NumPy in-memory vector store.

Replaces ChromaDB entirely to eliminate all insertion/version errors.
Uses cosine similarity over a float32 matrix.  Build time < 15 s for 1 500 docs.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# ── tunables ──────────────────────────────────────────────────────────────────
_LIMIT_SUP  = int(os.getenv("RAG_LIMIT_SUPPLIERS",    "500"))
_LIMIT_TXN  = int(os.getenv("RAG_LIMIT_TRANSACTIONS", "1000"))
_MODEL_NAME = os.getenv("RAG_EMBED_MODEL", "all-MiniLM-L6-v2")
_BATCH      = int(os.getenv("RAG_BATCH_SIZE", "256"))


def _safe(v: Any) -> Any:
    """Return a JSON/metadata-safe Python scalar."""
    if v is None:
        return ""
    if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
        return 0.0
    if hasattr(v, "item"):
        return v.item()
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    return v


class RAGService:
    """
    In-memory vector search backed by a float32 numpy matrix.

    _matrix  : (N, D) float32  — L2-normalised embeddings
    _docs    : list[str]        — raw document text
    _metas   : list[dict]       — metadata per document
    _ids     : list[str]        — stable string id per document
    """

    def __init__(self, data_loader):
        self.data_loader  = data_loader
        self._model: Optional[SentenceTransformer] = None
        self._matrix: Optional[np.ndarray] = None
        self._docs:   List[str]            = []
        self._metas:  List[Dict[str, Any]] = []
        self._ids:    List[str]            = []
        self._doc_count  = 0
        self._built_once = False

    def _load_model(self):
        if self._model is None:
            logger.info("RAG: loading model '%s'", _MODEL_NAME)
            self._model = SentenceTransformer(_MODEL_NAME)
            logger.info("RAG: model ready")

    def _build_supplier_docs(self, limit: int):
        df: Optional[pd.DataFrame] = getattr(self.data_loader, "suppliers_df", None)
        if df is None or df.empty:
            logger.warning("RAG: suppliers_df missing or empty")
            return [], [], []

        cols = set(df.columns)
        logger.info("RAG supplier cols: %s", sorted(cols))

        if "risk_score" in cols:
            df = df.sort_values("risk_score", ascending=False)
        df = df.head(limit).reset_index(drop=True)

        docs, metas, ids_ = [], [], []
        for i, row in df.iterrows():
            sid     = _safe(row.get("supplier_id", f"idx{i}"))
            name    = _safe(row.get("supplier_name") or row.get("supplier") or row.get("name") or "")
            score   = _safe(row.get("risk_score", 0))
            level   = _safe(row.get("risk_level", ""))
            cluster = _safe(row.get("cluster_label") or row.get("cluster") or "")
            expl    = _safe(row.get("explanation") or "")

            doc = (
                f"Supplier {sid} {name}. Risk score: {score}. "
                f"Risk level: {level}. Cluster: {cluster}. {expl}"
            ).strip()

            meta = {
                "type":          "supplier",
                "supplier_id":   sid,
                "supplier_name": name,
                "risk_score":    score,
                "risk_level":    level,
                "cluster_label": cluster,
                "transaction_id": "",
                "amount":        0.0,
                "has_anomaly":   _safe(row.get("anomaly_rate", 0) if "anomaly_rate" in cols else 0),
            }
            docs.append(doc)
            metas.append(meta)
            ids_.append(f"sup-{sid}")

        logger.info("RAG: %d supplier docs prepared", len(docs))
        return docs, metas, ids_

    def _build_transaction_docs(self, limit: int):
        df: Optional[pd.DataFrame] = getattr(self.data_loader, "transactions_df", None)
        if df is None or df.empty:
            logger.warning("RAG: transactions_df missing or empty")
            return [], [], []

        cols = set(df.columns)
        logger.info("RAG transaction cols: %s", sorted(cols))

        if "risk_score" in cols:
            df = df.sort_values("risk_score", ascending=False)
        df = df.head(limit).reset_index(drop=True)

        amt_col = next((c for c in ("amount", "gr_amount", "po_amount") if c in cols), None)

        docs, metas, ids_ = [], [], []
        for i, row in df.iterrows():
            tid     = _safe(row.get("transaction_id", f"idx{i}"))
            sid     = _safe(row.get("supplier_id", ""))
            score   = _safe(row.get("risk_score", 0))
            level   = _safe(row.get("risk_level", ""))
            amt     = _safe(row.get(amt_col, 0)) if amt_col else 0.0
            anomaly = _safe(row.get("anomaly_classification", "") if "anomaly_classification" in cols else "")
            delayed = _safe(row.get("is_delayed", 0)     if "is_delayed"     in cols else 0)
            days    = _safe(row.get("days_in_system", 0) if "days_in_system" in cols else 0)
            has_an  = _safe(row.get("has_anomaly", 0)    if "has_anomaly"    in cols else 0)

            doc = (
                f"Transaction {tid} supplier {sid}. "
                f"Amount: {amt}. Risk score: {score}. Risk level: {level}. "
                f"Anomaly: {anomaly}. Delayed: {delayed}. Days in system: {days}."
            ).strip()

            meta = {
                "type":                   "transaction",
                "transaction_id":         tid,
                "supplier_id":            sid,
                "amount":                 float(amt) if amt != "" else 0.0,
                "risk_score":             score,
                "risk_level":             level,
                "has_anomaly":            has_an,
                "is_delayed":             delayed,
                "days_in_system":         days,
                "anomaly_classification": anomaly,
            }
            docs.append(doc)
            metas.append(meta)
            ids_.append(f"txn-{tid}")

        logger.info("RAG: %d transaction docs prepared", len(docs))
        return docs, metas, ids_

    def build_collection(
        self,
        limit_suppliers:    Optional[int] = None,
        limit_transactions: Optional[int] = None,
    ):
        t0 = time.time()
        logger.info("RAG build_collection: START")

        lim_sup = limit_suppliers    or _LIMIT_SUP
        lim_txn = limit_transactions or _LIMIT_TXN

        self._load_model()

        s_docs, s_metas, s_ids = self._build_supplier_docs(lim_sup)
        t_docs, t_metas, t_ids = self._build_transaction_docs(lim_txn)

        all_docs  = s_docs  + t_docs
        all_metas = s_metas + t_metas
        all_ids   = s_ids   + t_ids

        if not all_docs:
            logger.warning("RAG: no documents extracted — index stays empty")
            self._built_once = True
            return

        # deduplicate by id
        seen = set()
        u_docs, u_metas, u_ids = [], [], []
        for d, m, i in zip(all_docs, all_metas, all_ids):
            if i not in seen:
                seen.add(i)
                u_docs.append(d)
                u_metas.append(m)
                u_ids.append(i)

        n = len(u_docs)
        logger.info("RAG: encoding %d docs in batches of %d…", n, _BATCH)

        emb_batches = []
        for start in range(0, n, _BATCH):
            batch = u_docs[start : start + _BATCH]
            emb   = self._model.encode(batch, show_progress_bar=False, convert_to_numpy=True)
            emb_batches.append(emb.astype(np.float32))
            logger.info("RAG: encoded %d / %d", min(start + _BATCH, n), n)

        matrix = np.vstack(emb_batches)                         # (N, D)
        norms  = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms  = np.where(norms == 0, 1.0, norms)
        matrix = (matrix / norms).astype(np.float32)            # L2-normalise

        assert matrix.shape[0] == n == len(u_metas) == len(u_ids), (
            f"BUG: matrix={matrix.shape[0]} docs={n} "
            f"metas={len(u_metas)} ids={len(u_ids)}"
        )

        self._matrix    = matrix
        self._docs      = u_docs
        self._metas     = u_metas
        self._ids       = u_ids
        self._doc_count = n
        self._built_once = True

        elapsed = time.time() - t0
        logger.info(
            "RAG build_collection: DONE  sup=%d txn=%d total=%d elapsed=%.1fs",
            len(s_ids), len(t_ids), n, elapsed,
        )

    def query(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Cosine-similarity search over the in-memory matrix."""
        if self._matrix is None or self._doc_count == 0:
            if not self._built_once:
                logger.warning("RAG: index empty — on-demand build")
                try:
                    self.build_collection()
                except Exception:
                    logger.exception("RAG: on-demand build failed")
            if self._matrix is None or self._doc_count == 0:
                return []

        self._load_model()
        q_emb = self._model.encode([query_text], convert_to_numpy=True).astype(np.float32)
        q_norm = np.linalg.norm(q_emb)
        if q_norm > 0:
            q_emb = q_emb / q_norm

        scores  = (self._matrix @ q_emb.T).flatten()
        top_idx = np.argsort(scores)[::-1][: min(top_k, self._doc_count)]

        return [
            {
                "document": self._docs[idx],
                "metadata": self._metas[idx],
                "distance": float(1.0 - scores[idx]),
            }
            for idx in top_idx
        ]

    def is_ready(self) -> bool:
        return self._doc_count > 0 and self._matrix is not None