"""
FastAPI application entrypoint.
RAG index is built in a background thread — server is immediately responsive.
"""
from __future__ import annotations

import asyncio
import logging
import threading
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import HTTPException

from .services.data_loader import DataLoaderService
from .services.rag_service import RAGService
from .routers import (
    transactions, suppliers, risk, analytics, search,
    executive, alerts, supplier360, transaction360,
    analytics_v2, chatbot,
)

logger = logging.getLogger("p2p_api")
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
logger.addHandler(_handler)
logger.setLevel(logging.INFO)


def _rag_thread(app: FastAPI, data_loader: DataLoaderService):
    """Background thread: build the RAG index without blocking startup."""
    try:
        logger.info("RAG thread: starting build")
        rag = RAGService(data_loader)
        app.state.rag_service = rag          # attach early so endpoints can check status
        rag.build_collection(limit_suppliers=500, limit_transactions=1000)
        logger.info("RAG thread: DONE  ready=%s  doc_count=%d",
                    rag.is_ready(), rag._doc_count)
    except Exception:
        logger.exception("RAG thread: build FAILED")


def create_app() -> FastAPI:
    app = FastAPI(title="SAP P2P Risk Monitoring API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # DB init
    try:
        from .db.init_db import init_db
        init_db()
    except Exception:
        logger.exception("DB init failed (non-fatal)")

    # Load datasets synchronously so every router has data immediately
    data_loader = DataLoaderService(data_dir="src/data/products")
    if not data_loader.load_all():
        logger.error("DataLoader: one or more datasets failed to load")
    app.state.data_loader  = data_loader
    app.state.rag_service  = None           # populated by background thread

    @app.on_event("startup")
    async def startup_event():
        logger.info("Startup: launching RAG build thread")
        t = threading.Thread(
            target=_rag_thread,
            args=(app, data_loader),
            daemon=True,
            name="rag-build",
        )
        t.start()
        await asyncio.sleep(0.05)           # let thread attach rag_service to app.state
        logger.info("Startup complete — RAG building in background")

    # ── exception handlers ────────────────────────────────────────────────────
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

    # ── rate limiter ──────────────────────────────────────────────────────────
    app.state.rate_store  = {}
    app.state.rate_window = 60
    app.state.rate_max    = 200

    @app.middleware("http")
    async def rate_limit_and_timing(request: Request, call_next):
        host = request.client.host if request.client else "unknown"
        now  = time.time()
        hits = [t for t in app.state.rate_store.get(host, []) if now - t < app.state.rate_window]
        if len(hits) >= app.state.rate_max:
            return JSONResponse(status_code=429,
                                content={"status": "error", "message": "Rate limit exceeded"})
        hits.append(now)
        app.state.rate_store[host] = hits
        t0       = time.time()
        response = await call_next(request)
        response.headers["X-Process-Time"] = f"{time.time()-t0:.4f}"
        return response

    # ── routers ───────────────────────────────────────────────────────────────
    from .auth import routes as auth_routes
    app.include_router(auth_routes.router)
    app.include_router(transactions.router,   prefix="/api")
    app.include_router(suppliers.router,      prefix="/api")
    app.include_router(risk.router,           prefix="/api")
    app.include_router(analytics.router,      prefix="/api")
    app.include_router(search.router,         prefix="/api")
    app.include_router(executive.router,      prefix="/api")
    app.include_router(alerts.router,         prefix="/api")
    app.include_router(supplier360.router,    prefix="/api")
    app.include_router(transaction360.router, prefix="/api")
    app.include_router(analytics_v2.router,   prefix="/api")
    app.include_router(chatbot.router,        prefix="/api")

    @app.get("/healthz")
    def healthz():
        healthy = app.state.data_loader.is_healthy()
        return {"status": "ok" if healthy else "degraded", "datasets_loaded": healthy}

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, log_level="info")