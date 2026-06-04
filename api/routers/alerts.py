from fastapi import APIRouter, Depends

from ..auth.dependencies import get_current_user
from ..core.deps import get_data_loader
from ..core.response import format_response
from ..services.data_loader import DataLoaderService
from ..services.enterprise_service import EnterpriseApiService

router = APIRouter(tags=["Alerts"])


@router.get("/alerts")
def alerts(
    data_loader: DataLoaderService = Depends(get_data_loader),
    current_user: dict = Depends(get_current_user),
):
    service = EnterpriseApiService(data_loader)
    records = service.alerts_all()
    return format_response({"alerts": records}, metadata={"count": len(records)})


@router.get("/alerts/high-risk")
def alerts_high_risk(
    data_loader: DataLoaderService = Depends(get_data_loader),
    current_user: dict = Depends(get_current_user),
):
    service = EnterpriseApiService(data_loader)
    records = service.alerts_transactions()
    return format_response({"alerts": records}, metadata={"count": len(records)})


@router.get("/alerts/transactions")
def alerts_transactions(
    data_loader: DataLoaderService = Depends(get_data_loader),
    current_user: dict = Depends(get_current_user),
):
    service = EnterpriseApiService(data_loader)
    records = service.alerts_transactions()
    return format_response({"alerts": records}, metadata={"count": len(records)})


@router.get("/alerts/suppliers")
def alerts_suppliers(
    data_loader: DataLoaderService = Depends(get_data_loader),
    current_user: dict = Depends(get_current_user),
):
    service = EnterpriseApiService(data_loader)
    records = service.alerts_suppliers()
    return format_response({"alerts": records}, metadata={"count": len(records)})
