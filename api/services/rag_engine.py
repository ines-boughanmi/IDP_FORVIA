from __future__ import annotations

import json
import logging
import math
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Row limits per source tier
# ---------------------------------------------------------------------------
_LIMIT_TRANSACTIONS = int(os.getenv("RAG_LIMIT_TRANSACTIONS", "40000"))
_LIMIT_CONTRACTS    = int(os.getenv("RAG_LIMIT_CONTRACTS",    "30000"))
_LIMIT_DEFAULT      = int(os.getenv("RAG_LIMIT_DEFAULT",       "5000"))

# Files/patterns to skip entirely
_SKIP_NAMES = {
    "transactions_risk_table.jsonl",
    "supplier_risk_table.jsonl",
    "data.zip",
}
_SUPPORTED_SUFFIXES = {".csv", ".xlsx", ".xls", ".parquet", ".json"}

# ---------------------------------------------------------------------------
# Column aliases — maps logical field name → list of possible column names
# ---------------------------------------------------------------------------
_ALIASES: Dict[str, List[str]] = {
    "supplier_id":    ["supplier_id", "lifnr", "supplier_|_lifnr", "vendor_id", "vendor"],
    "transaction_id": ["transaction_id", "doc_id", "document_id"],
    "risk_score":     ["risk_score", "score"],
    "risk_level":     ["risk_level", "level", "risk_category"],
    "amount":         ["amount", "gr_amount", "ir_amount", "amount_|_wrbtr", "wrbtr",
                       "net_amount", "total_amount", "invoice_value_|_reewr"],
    "supplier_name":  ["supplier_name", "name", "vendor_name"],
    "cluster_label":  ["cluster_label", "cluster", "segment"],
    "has_anomaly":    ["has_anomaly", "anomaly", "is_anomaly"],
    "is_delayed":     ["is_delayed", "delayed"],
    "explanation":    ["explanation", "risk_explanation", "reason"],
    "po_number":      ["purchasing_document_|_ebeln", "ebeln", "po_number", "po"],
    "material":       ["material_|_matnr", "material", "matnr"],
    "description":    ["short_text_|_txz01", "description", "short_text", "txz01"],
    "currency":       ["currency_|_waers", "currency", "waers"],
    "document_date":  ["document_date_|_bedat", "document_date", "bedat", "date"],
}

# Precomputed at module load — used in the hot path
_COVERED_COLS: set = {a.lower() for aliases in _ALIASES.values() for a in aliases}


def _find_col(df: pd.DataFrame, field: str) -> Optional[str]:
    cols_lower = {c.lower(): c for c in df.columns}
    for alias in _ALIASES.get(field, []):
        if alias.lower() in cols_lower:
            return cols_lower[alias.lower()]
    return None


def _safe_val(row: pd.Series, field: str) -> Any:
    for alias in _ALIASES.get(field, []):
        if alias in row.index:
            v = row[alias]
            try:
                if pd.isna(v):
                    continue
            except Exception:
                pass
            if str(v) not in ("nan", "None", ""):
                return v
    return None


def _safe_float(v: Any) -> Optional[float]:
    try:
        f = float(v)
        return None if (math.isnan(f) or math.isinf(f)) else f
    except Exception:
        return None


def _safe_int(v: Any) -> Optional[int]:
    try:
        return int(float(str(v)))
    except Exception:
        return None


def _meta_str(v: Any) -> Optional[str]:
    s = str(v) if v is not None else ""
    return s if s not in ("nan", "None", "") else None


# ---------------------------------------------------------------------------
# RAGEngine
# ---------------------------------------------------------------------------

class RAGEngine:
    COLLECTION_NAME = "p2p_copilot_v2"

    def __init__(
        self,
        data_dir: str = "src/data",
        contracts_path: str = "Contracts.csv",
        chroma_dir: str = "./chroma_db",
        model_name: str = "all-MiniLM-L6-v2",
    ):
        self.data_dir       = Path(data_dir)
        self.contracts_path = Path(contracts_path)
        self.chroma_dir     = chroma_dir
        self.model_name     = os.getenv("RAG_EMBED_MODEL", model_name)
        self._state_file    = os.path.join(chroma_dir, "rag_state.json")

        self._model: Optional[SentenceTransformer] = None
        self._client = None
        self._collection = None

        self._doc_count: int     = 0
        self._sources: List[str] = []
        self._built: bool        = False
        self._building: bool     = False

        self._suppliers_df:    Optional[pd.DataFrame] = None
        self._transactions_df: Optional[pd.DataFrame] = None

    # -------------------------------------------------------------------------
    # Internal initialisation
    # -------------------------------------------------------------------------

    def _init_model(self):
        if self._model is None:
            logger.info("RAG: loading embedding model %s", self.model_name)
            self._model = SentenceTransformer(self.model_name)

    def _init_client(self):
        if self._client is None:
            os.makedirs(self.chroma_dir, exist_ok=True)
            try:
                self._client = chromadb.PersistentClient(path=self.chroma_dir)
                logger.info("RAG: ChromaDB PersistentClient at %s", self.chroma_dir)
            except Exception:
                logger.warning("RAG: PersistentClient unavailable, using in-memory ChromaDB")
                self._client = chromadb.Client()

    def _open_collection(self, reset: bool = False):
        self._init_client()
        if reset:
            try:
                self._client.delete_collection(self.COLLECTION_NAME)
                logger.info("RAG: deleted collection %s", self.COLLECTION_NAME)
            except Exception:
                pass
        try:
            self._collection = self._client.create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception:
            try:
                self._collection = self._client.get_collection(self.COLLECTION_NAME)
            except Exception:
                logger.exception("RAG: cannot get or create collection")
                self._collection = None

    # -------------------------------------------------------------------------
    # Persistent index cache (skip rebuild on restart)
    # -------------------------------------------------------------------------

    def _load_existing_index(self) -> bool:
        """
        Load a previously built ChromaDB index without re-embedding.
        Returns True if a valid existing index was found and loaded.
        """
        try:
            self._init_client()
            col = self._client.get_collection(self.COLLECTION_NAME)
            count = col.count()
            if count <= 0:
                return False
            self._collection = col
            self._doc_count  = count
            self._built      = True
            if os.path.exists(self._state_file):
                with open(self._state_file) as f:
                    state = json.load(f)
                self._doc_count = state.get("doc_count", count)
                self._sources   = state.get("sources", [])
            else:
                self._sources = ["cached"]
            logger.info(
                "RAG: loaded existing index — %d documents across %d sources (no rebuild needed)",
                self._doc_count, len(self._sources),
            )
            return True
        except Exception:
            return False

    def _save_state(self, doc_count: int, sources: List[str]):
        try:
            os.makedirs(self.chroma_dir, exist_ok=True)
            with open(self._state_file, "w") as f:
                json.dump({"doc_count": doc_count, "sources": sources}, f)
        except Exception:
            logger.warning("RAG: could not save state file")

    # -------------------------------------------------------------------------
    # File discovery
    # -------------------------------------------------------------------------

    def discover_files(self) -> List[Tuple[Path, str]]:
        found: List[Tuple[Path, str]] = []
        products_dir = self.data_dir / "products"
        if products_dir.exists():
            for f in sorted(products_dir.iterdir()):
                if f.suffix in _SUPPORTED_SUFFIXES and f.name not in _SKIP_NAMES:
                    found.append((f, f"products/{f.stem}"))
        if self.contracts_path.exists():
            found.append((self.contracts_path, "Contracts"))
        if self.data_dir.exists():
            skip_dirs = {"products"}
            for subdir in sorted(self.data_dir.iterdir()):
                if not subdir.is_dir() or subdir.name in skip_dirs:
                    continue
                for f in sorted(subdir.iterdir()):
                    if f.suffix in _SUPPORTED_SUFFIXES and f.name not in _SKIP_NAMES:
                        found.append((f, f"{subdir.name}/{f.stem}"))
        return found

    # -------------------------------------------------------------------------
    # Data loading
    # -------------------------------------------------------------------------

    def _load_file(self, path: Path) -> Optional[pd.DataFrame]:
        try:
            if path.suffix == ".csv":
                df = pd.read_csv(path, low_memory=False)
            elif path.suffix in (".xlsx", ".xls"):
                df = pd.read_excel(path)
            elif path.suffix == ".parquet":
                df = pd.read_parquet(path)
            elif path.suffix == ".json":
                df = pd.read_json(path)
            else:
                return None
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except Exception:
            logger.exception("RAG: failed to load %s", path)
            return None

    # -------------------------------------------------------------------------
    # Fast vectorised row → document (hot path)
    # -------------------------------------------------------------------------

    @staticmethod
    def _get_val_fast(record: Dict[str, Any], col: Optional[str]) -> Any:
        """O(1) field lookup using precomputed column name."""
        if not col or col not in record:
            return None
        v = record[col]
        if v is None:
            return None
        try:
            if pd.isna(v):
                return None
        except Exception:
            pass
        return None if str(v) in ("nan", "None", "") else v

    def _row_to_doc_fast(
        self,
        record: Dict[str, Any],
        source: str,
        row_idx: int,
        col_map: Dict[str, Optional[str]],
    ) -> Tuple[str, Dict[str, Any], str]:
        """Convert a plain dict row to (text, metadata, doc_id) using precomputed col_map."""
        g = lambda f: RAGEngine._get_val_fast(record, col_map.get(f))

        supplier_id    = _safe_int(g("supplier_id"))
        transaction_id = _safe_int(g("transaction_id"))
        po_number      = g("po_number")
        risk_score     = _safe_float(g("risk_score"))
        risk_level     = _meta_str(g("risk_level"))
        amount         = _safe_float(g("amount"))
        supplier_name  = _meta_str(g("supplier_name"))
        cluster_label  = _meta_str(g("cluster_label"))
        has_anomaly    = g("has_anomaly")
        is_delayed     = g("is_delayed")
        explanation    = _meta_str(g("explanation"))
        material       = _meta_str(g("material"))
        description    = _meta_str(g("description"))
        currency       = _meta_str(g("currency"))
        document_date  = _meta_str(g("document_date"))

        parts: List[str] = []
        if transaction_id is not None:
            parts.append(f"Transaction ID: {transaction_id}")
        if po_number is not None:
            parts.append(f"PO Number: {po_number}")
        if supplier_id is not None:
            parts.append(f"Supplier ID: {supplier_id}")
        if supplier_name:
            parts.append(f"Supplier Name: {supplier_name}")
        if risk_score is not None:
            parts.append(f"Risk Score: {risk_score:.2f}")
        if risk_level:
            parts.append(f"Risk Level: {risk_level}")
        if cluster_label:
            parts.append(f"Cluster: {cluster_label}")
        if amount is not None:
            currency_str = f" {currency}" if currency else ""
            parts.append(f"Amount: {amount:.2f}{currency_str}")
        if has_anomaly is not None:
            try:
                flag = bool(int(float(str(has_anomaly))))
            except Exception:
                flag = bool(has_anomaly)
            parts.append(f"Anomaly: {'Yes' if flag else 'No'}")
        if is_delayed is not None:
            try:
                flag = bool(int(float(str(is_delayed))))
            except Exception:
                flag = bool(is_delayed)
            parts.append(f"Delayed: {'Yes' if flag else 'No'}")
        if material:
            parts.append(f"Material: {material}")
        if description:
            parts.append(f"Description: {description}")
        if document_date:
            parts.append(f"Date: {document_date}")
        if explanation and explanation != "No explanation available":
            parts.append(f"Explanation: {explanation}")

        # Up to 6 extra columns not already covered by aliases
        extra = 0
        for col, v in record.items():
            if col.lower() in _COVERED_COLS or extra >= 6:
                continue
            if v is None:
                continue
            try:
                if pd.isna(v):
                    continue
            except Exception:
                pass
            s = str(v)
            if s not in ("nan", "None", ""):
                parts.append(f"{col}: {s}")
                extra += 1

        parts.append(f"Source: {source}")
        text = " | ".join(parts)

        meta: Dict[str, Any] = {"source": source, "row_idx": row_idx}
        if supplier_id is not None:
            meta["supplier_id"] = supplier_id
        if transaction_id is not None:
            meta["transaction_id"] = transaction_id
        if risk_score is not None:
            meta["risk_score"] = risk_score
        if risk_level:
            meta["risk_level"] = risk_level
        if cluster_label:
            meta["cluster_label"] = cluster_label
        if supplier_name:
            meta["supplier_name"] = supplier_name
        if amount is not None:
            meta["amount"] = amount
        if currency:
            meta["currency"] = currency

        src_slug = re.sub(r"[^a-zA-Z0-9_-]", "_", source)[:40]
        if transaction_id is not None:
            doc_id = f"txn-{transaction_id}"
        elif supplier_id is not None and po_number is not None:
            doc_id = f"contract-{supplier_id}-{row_idx}"
        elif supplier_id is not None:
            doc_id = f"sup-{supplier_id}-{src_slug}"
        else:
            doc_id = f"{src_slug}-{row_idx}"

        return text, meta, doc_id

    # -------------------------------------------------------------------------
    # DataFrame → document lists (vectorised)
    # -------------------------------------------------------------------------

    def _df_to_docs(
        self,
        df: pd.DataFrame,
        source: str,
        row_limit: Optional[int],
    ) -> Tuple[List[str], List[Dict], List[str]]:
        if df.empty:
            return [], [], []

        risk_col = _find_col(df, "risk_score")
        if row_limit and len(df) > row_limit:
            df = df.nlargest(row_limit, risk_col) if risk_col else df.head(row_limit)

        # Precompute column mapping once per DataFrame (not once per row)
        col_map = {field: _find_col(df, field) for field in _ALIASES}

        # to_dict("records") is ~10–50× faster than iterrows() for large DataFrames
        records = df.reset_index(drop=True).to_dict("records")

        texts, metas, ids = [], [], []
        seen: set = set()

        for idx, record in enumerate(records):
            try:
                text, meta, doc_id = self._row_to_doc_fast(record, source, idx, col_map)
            except Exception:
                continue
            if not text.strip():
                continue
            if doc_id in seen:
                doc_id = f"{doc_id}-{idx}"
            seen.add(doc_id)
            texts.append(text)
            metas.append(meta)
            ids.append(doc_id)

        return texts, metas, ids

    # -------------------------------------------------------------------------
    # Embedding + upsert
    # -------------------------------------------------------------------------

    def _embed(self, texts: List[str], batch_size: int = 128) -> np.ndarray:
        batches = []
        for i in range(0, len(texts), batch_size):
            emb = self._model.encode(
                texts[i:i + batch_size],
                show_progress_bar=False,
                convert_to_numpy=True,
            )
            batches.append(emb)
        return np.vstack(batches) if batches else np.empty((0, 384))

    def _upsert(self, texts: List[str], metas: List[Dict], ids: List[str]) -> int:
        chunk = int(os.getenv("RAG_BATCH_SIZE", "512"))
        added = 0
        for i in range(0, len(texts), chunk):
            bt, bm, bi = texts[i:i+chunk], metas[i:i+chunk], ids[i:i+chunk]
            try:
                emb = self._embed(bt)
                self._collection.add(
                    ids=bi,
                    documents=bt,
                    metadatas=bm,
                    embeddings=emb.tolist(),
                )
                added += len(bt)
            except Exception:
                logger.exception("RAG: upsert error at batch index %d", i)
        return added

    # -------------------------------------------------------------------------
    # Public: build_index
    # -------------------------------------------------------------------------

    def build_index(self, force: bool = True):
        """Build (or rebuild) the full vector index from all data sources."""
        if self._building:
            logger.info("RAG: build already in progress — skipping")
            return

        # On restart (force=False): reuse ChromaDB if it already has data
        if not force and self._load_existing_index():
            return

        if self._built and not force:
            logger.info("RAG: index already built — skipping")
            return

        self._building = True
        try:
            self._init_model()
            self._open_collection(reset=True)
            if self._collection is None:
                logger.error("RAG: no collection available — aborting build")
                return

            total = 0
            indexed_sources: List[str] = []

            for path, source in self.discover_files():
                logger.info("RAG: indexing %s (%s)", source, path.name)
                df = self._load_file(path)
                if df is None or df.empty:
                    logger.warning("RAG: skipped %s — empty or unreadable", source)
                    continue

                if source == "products/transactions_risk_table":
                    row_limit = _LIMIT_TRANSACTIONS
                    self._transactions_df = df.copy()
                elif source == "products/supplier_risk_table":
                    row_limit = None
                    self._suppliers_df = df.copy()
                elif source == "Contracts":
                    row_limit = _LIMIT_CONTRACTS
                else:
                    row_limit = _LIMIT_DEFAULT

                texts, metas, ids = self._df_to_docs(df, source, row_limit)
                if not texts:
                    logger.warning("RAG: no documents extracted from %s", source)
                    continue

                n = self._upsert(texts, metas, ids)
                total += n
                indexed_sources.append(source)
                logger.info("RAG: %s → %d documents indexed", source, n)

            self._doc_count = total
            self._sources   = indexed_sources
            self._built     = True
            self._save_state(total, indexed_sources)
            logger.info(
                "RAG: build complete — %d documents across %d sources",
                total, len(indexed_sources),
            )

        except Exception:
            logger.exception("RAG: build_index failed")
        finally:
            self._building = False

    # -------------------------------------------------------------------------
    # Exact ID lookups (bypass vector search for precise queries)
    # -------------------------------------------------------------------------

    def _lookup_supplier(self, supplier_id: int) -> List[Dict[str, Any]]:
        df = self._suppliers_df
        if df is None:
            return []
        sup_col = _find_col(df, "supplier_id")
        if sup_col is None:
            return []
        matches = df[pd.to_numeric(df[sup_col], errors="coerce") == supplier_id]
        results = []
        col_map = {field: _find_col(df, field) for field in _ALIASES}
        for _, row in matches.iterrows():
            text_parts = [
                f"{k}: {v}" for k, v in row.items()
                if v is not None and str(v) not in ("nan", "None", "")
                and not (hasattr(v, '__float__') and math.isnan(float(v)) if isinstance(v, float) else False)
            ]
            record = row.to_dict()
            _, meta, _ = self._row_to_doc_fast(record, "products/supplier_risk_table", 0, col_map)
            results.append({
                "document":   " | ".join(text_parts),
                "metadata":   meta,
                "source":     "products/supplier_risk_table",
                "match_type": "exact_id",
                "score":      1.0,
            })
        return results

    def _lookup_transaction(self, transaction_id: int) -> List[Dict[str, Any]]:
        df = self._transactions_df
        if df is None:
            return []
        txn_col = _find_col(df, "transaction_id")
        if txn_col is None:
            return []
        matches = df[pd.to_numeric(df[txn_col], errors="coerce") == transaction_id]
        results = []
        col_map = {field: _find_col(df, field) for field in _ALIASES}
        for _, row in matches.iterrows():
            text_parts = [
                f"{k}: {v}" for k, v in row.items()
                if v is not None and str(v) not in ("nan", "None", "")
            ]
            record = row.to_dict()
            _, meta, _ = self._row_to_doc_fast(record, "products/transactions_risk_table", 0, col_map)
            results.append({
                "document":   " | ".join(text_parts),
                "metadata":   meta,
                "source":     "products/transactions_risk_table",
                "match_type": "exact_id",
                "score":      1.0,
            })
        return results

    # -------------------------------------------------------------------------
    # Semantic search
    # -------------------------------------------------------------------------

    def _semantic_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        self._init_model()
        if self._collection is None:
            self._init_client()
            try:
                self._collection = self._client.get_collection(self.COLLECTION_NAME)
            except Exception:
                logger.warning("RAG: collection not available for semantic search")
                return []
        try:
            q_emb = self._model.encode([query], convert_to_numpy=True).tolist()
            n = max(1, min(top_k, self._doc_count or top_k))
            resp = self._collection.query(
                query_embeddings=q_emb,
                n_results=n,
                include=["documents", "metadatas", "distances"],
            )
            results = []
            for docs, metas, dists in zip(
                resp.get("documents", [[]]),
                resp.get("metadatas", [[]]),
                resp.get("distances", [[]]),
            ):
                for doc, meta, dist in zip(docs, metas, dists):
                    score = max(0.0, 1.0 - float(dist))
                    results.append({
                        "document":   doc,
                        "metadata":   meta,
                        "source":     meta.get("source", "unknown"),
                        "match_type": "semantic",
                        "score":      round(score, 4),
                    })
            return results
        except Exception:
            logger.exception("RAG: semantic search failed")
            return []

    # -------------------------------------------------------------------------
    # Public: query
    # -------------------------------------------------------------------------

    def query(self, question: str, top_k: int = 10) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        q_lower = question.lower()
        numbers = [int(m) for m in re.findall(r"\b(\d{3,12})\b", question)]

        if "supplier" in q_lower and numbers:
            for num in numbers:
                results.extend(self._lookup_supplier(num))

        if ("transaction" in q_lower or "txn" in q_lower) and numbers and not results:
            for num in numbers:
                results.extend(self._lookup_transaction(num))

        if not results and numbers:
            for num in numbers:
                hits = self._lookup_supplier(num)
                if not hits:
                    hits = self._lookup_transaction(num)
                results.extend(hits)

        semantic = self._semantic_search(question, top_k=top_k)
        seen_docs = {r["document"] for r in results}
        for r in semantic:
            if r["document"] not in seen_docs:
                results.append(r)
                seen_docs.add(r["document"])

        context_parts: List[str] = []
        sources: List[str] = []
        for r in results[:12]:
            context_parts.append(r["document"])
            src = r.get("source", "unknown")
            if src not in sources:
                sources.append(src)

        context    = "\n\n".join(context_parts)
        confidence = results[0]["score"] if results else 0.0
        has_exact  = any(r.get("match_type") == "exact_id" for r in results)

        return {
            "context":         context,
            "sources":         sources,
            "results":         results[:12],
            "confidence":      round(float(confidence), 4),
            "has_exact_match": has_exact,
        }

    # -------------------------------------------------------------------------
    # Status helpers
    # -------------------------------------------------------------------------

    def is_ready(self) -> bool:
        return self._built and self._doc_count > 0

    def status(self) -> Dict[str, Any]:
        return {
            "ready":     self.is_ready(),
            "building":  self._building,
            "documents": self._doc_count,
            "sources":   self._sources,
        }
