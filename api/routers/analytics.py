"""Analytics API router for global metrics and risk distribution."""
from fastapi import APIRouter, Depends
from ..services.data_loader import DataLoaderService
from ..models.schemas import SuccessResponse
from ..core.deps import get_data_loader
from ..auth.dependencies import get_current_user
from ..core.response import format_response
import logging

router = APIRouter(tags=["Analytics"])
logger = logging.getLogger(__name__)

@router.get("/metrics/global")
def global_metrics(data_loader: DataLoaderService = Depends(get_data_loader), current_user: dict = Depends(get_current_user)):
    stats = data_loader.get_global_stats()
    return format_response(stats)


@router.get("/metrics/risk-distribution")
def risk_distribution(data_loader: DataLoaderService = Depends(get_data_loader), current_user: dict = Depends(get_current_user)):
    dist = data_loader.get_risk_distribution()
    return format_response(dist)


@router.get("/monitoring")
def monitoring(data_loader: DataLoaderService = Depends(get_data_loader), current_user: dict = Depends(get_current_user)):
    # lightweight monitoring endpoint returning dataset status
    healthy = data_loader.is_healthy()
    return format_response({"status": "ok" if healthy else "degraded", "datasets_loaded": healthy})
