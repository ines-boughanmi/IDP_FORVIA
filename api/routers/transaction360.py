from fastapi import APIRouter, Depends, HTTPException

from ..auth.dependencies import get_current_user
from ..core.deps import get_data_loader
from ..core.response import format_response
from ..services.data_loader import DataLoaderService
from ..services.enterprise_service import EnterpriseApiService

router = APIRouter(tags=["Transaction360"])


@router.get("/transaction/{transaction_id}/overview")
def transaction_overview(
    transaction_id: int,
    data_loader: DataLoaderService = Depends(get_data_loader),
    current_user: dict = Depends(get_current_user),
):
    service = EnterpriseApiService(data_loader)
    overview = service.transaction_overview(transaction_id)
    if not overview:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")
    return format_response(overview)


@router.get("/transaction360/{transaction_id}")
def transaction_overview_compatibility(
    transaction_id: int,
    data_loader: DataLoaderService = Depends(get_data_loader),
    current_user: dict = Depends(get_current_user),
):
    service = EnterpriseApiService(data_loader)
    overview = service.transaction_overview(transaction_id)
    if not overview:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")
    return format_response(overview)
