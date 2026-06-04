from fastapi import APIRouter, Depends, HTTPException

from ..auth.dependencies import get_current_user
from ..core.deps import get_data_loader
from ..core.response import format_response
from ..services.data_loader import DataLoaderService
from ..services.enterprise_service import EnterpriseApiService

router = APIRouter(tags=["Supplier360"])


@router.get("/supplier/{supplier_id}/overview")
def supplier_overview(
    supplier_id: int,
    data_loader: DataLoaderService = Depends(get_data_loader),
    current_user: dict = Depends(get_current_user),
):
    service = EnterpriseApiService(data_loader)
    overview = service.supplier_overview(supplier_id)
    if not overview:
        raise HTTPException(status_code=404, detail=f"Supplier {supplier_id} not found")
    return format_response(overview)


@router.get("/supplier360/{supplier_id}")
def supplier_overview_compatibility(
    supplier_id: int,
    data_loader: DataLoaderService = Depends(get_data_loader),
    current_user: dict = Depends(get_current_user),
):
    service = EnterpriseApiService(data_loader)
    overview = service.supplier_overview(supplier_id)
    if not overview:
        raise HTTPException(status_code=404, detail=f"Supplier {supplier_id} not found")
    return format_response(overview)
