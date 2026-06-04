from fastapi import APIRouter, Depends

from ..auth.dependencies import get_current_user
from ..core.deps import get_data_loader
from ..core.response import format_response
from ..services.data_loader import DataLoaderService
from ..services.enterprise_service import EnterpriseApiService

router = APIRouter(tags=["AnalyticsV2"])


@router.get("/analytics/risk-distribution")
def risk_distribution(
    data_loader: DataLoaderService = Depends(get_data_loader),
    current_user: dict = Depends(get_current_user),
):
    service = EnterpriseApiService(data_loader)
    return format_response(service.risk_distribution())


@router.get("/analytics/top-risk-suppliers")
def top_risk_suppliers(
    limit: int = 20,
    data_loader: DataLoaderService = Depends(get_data_loader),
    current_user: dict = Depends(get_current_user),
):
    service = EnterpriseApiService(data_loader)
    records = service.top_risk_suppliers(limit=limit)
    return format_response({"suppliers": records}, metadata={"count": len(records)})


@router.get("/analytics/cluster-distribution")
def cluster_distribution(
    data_loader: DataLoaderService = Depends(get_data_loader),
    current_user: dict = Depends(get_current_user),
):
    service = EnterpriseApiService(data_loader)
    return format_response(service.cluster_distribution())


@router.get("/analytics/anomaly-summary")
def anomaly_summary(
    data_loader: DataLoaderService = Depends(get_data_loader),
    current_user: dict = Depends(get_current_user),
):
    service = EnterpriseApiService(data_loader)
    return format_response(service.anomaly_summary())


@router.get("/analytics/overview")
def analytics_overview(
    data_loader: DataLoaderService = Depends(get_data_loader),
    current_user: dict = Depends(get_current_user),
):
    service = EnterpriseApiService(data_loader)
    return format_response(service.executive_dashboard())
