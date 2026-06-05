"""
FastAPI application entrypoint.

The RAG index is built in a background thread immediately after startup —
the server is responsive right away and the chatbot becomes available once
indexing completes (typically 2–5 minutes depending on dataset size).
"""
from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
import threading
import time
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import HTTPException

from .services.data_loader import DataLoaderService
from .services.rag_engine import RAGEngine
from .routers import (
    transactions, suppliers, risk, analytics, search,
    executive, alerts, supplier360, transaction360,
    analytics_v2, chatbot,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("p2p_api")
# Make chatbot logs visible at WARNING+ (shows auth failures)
logging.getLogger("api.routers.chatbot").setLevel(logging.DEBUG)


def _rag_build_thread(app: FastAPI):
    """Background thread: builds the full RAG index."""
    try:
        logger.info("RAG build thread: starting")
        engine: RAGEngine = app.state.rag_engine
        engine.build_index(force=False)
        logger.info(
            "RAG build thread: DONE  ready=%s  documents=%d",
            engine.is_ready(),
            engine._doc_count,
        )
    except Exception:
        logger.exception("RAG build thread: FAILED")


def create_app() -> FastAPI:
    app = FastAPI(title="SAP P2P Risk Monitoring API", version="2.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Database init ─────────────────────────────────────────────────────────
    try:
        from .db.init_db import init_db
        init_db()
    except Exception:
        logger.exception("DB init failed (non-fatal)")

    # ── Dataset loading (synchronous, blocking) ───────────────────────────────
    data_loader = DataLoaderService(data_dir="src/data/products")
    if not data_loader.load_all():
        logger.error("DataLoader: one or more datasets failed to load")
    app.state.data_loader = data_loader

    # ── RAG engine (build in background) ─────────────────────────────────────
    rag_engine = RAGEngine(
        data_dir=os.getenv("RAG_DATA_DIR", "src/data"),
        contracts_path=os.getenv("CONTRACTS_CSV_PATH", "Contracts.csv"),
        chroma_dir=os.getenv("CHROMA_PERSIST_DIR", "./chroma_db"),
        model_name=os.getenv("RAG_EMBED_MODEL", "all-MiniLM-L6-v2"),
    )
    # Pre-load the product DataFrames so exact ID lookups work immediately
    rag_engine._suppliers_df    = data_loader.suppliers_df
    rag_engine._transactions_df = data_loader.transactions_df
    app.state.rag_engine = rag_engine

    @app.on_event("startup")
    async def startup_event():
        logger.info("Startup: launching RAG index build in background thread")
        t = threading.Thread(
            target=_rag_build_thread,
            args=(app,),
            daemon=True,
            name="rag-build",
        )
        t.start()
        await asyncio.sleep(0.05)
        logger.info("Startup complete — RAG indexing in background")

    # ── Exception handlers ────────────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception):
        logger.exception("Unhandled: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "data": None,
                     "metadata": {"message": str(exc)}},
        )

    @app.exception_handler(HTTPException)
    async def http_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"status": "error", "message": exc.detail},
        )

    # ── Rate limiter ──────────────────────────────────────────────────────────
    app.state.rate_store  = {}
    app.state.rate_window = 60
    app.state.rate_max    = 200

    @app.middleware("http")
    async def rate_limit_and_timing(request: Request, call_next):
        host = request.client.host if request.client else "unknown"
        now  = time.time()
        hits = [t for t in app.state.rate_store.get(host, []) if now - t < app.state.rate_window]
        if len(hits) >= app.state.rate_max:
            return JSONResponse(
                status_code=429,
                content={"status": "error", "message": "Rate limit exceeded"},
            )
        hits.append(now)
        app.state.rate_store[host] = hits
        t0       = time.time()
        response = await call_next(request)
        response.headers["X-Process-Time"] = f"{time.time()-t0:.4f}"
        return response

    # ── Routers ───────────────────────────────────────────────────────────────
    from .auth import routes as auth_routes
    app.include_router(auth_routes.router)
    app.include_router(transactions.router,    prefix="/api")
    app.include_router(suppliers.router,       prefix="/api")
    app.include_router(risk.router,            prefix="/api")
    app.include_router(analytics.router,       prefix="/api")
    app.include_router(search.router,          prefix="/api")
    app.include_router(executive.router,       prefix="/api")
    app.include_router(alerts.router,          prefix="/api")
    app.include_router(supplier360.router,     prefix="/api")
    app.include_router(transaction360.router,  prefix="/api")
    app.include_router(analytics_v2.router,    prefix="/api")
    app.include_router(chatbot.router,         prefix="/api")

    @app.get("/healthz")
    def healthz():
        healthy = app.state.data_loader.is_healthy()
        return {"status": "ok" if healthy else "degraded", "datasets_loaded": healthy}

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, log_level="info")
