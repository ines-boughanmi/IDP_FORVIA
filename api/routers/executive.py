from fastapi import APIRouter, Depends

from ..auth.dependencies import get_current_user
from ..core.deps import get_data_loader
from ..core.response import format_response
from ..services.data_loader import DataLoaderService
from ..services.enterprise_service import EnterpriseApiService

router = APIRouter(tags=["Executive"])


@router.get("/executive/dashboard")
def executive_dashboard(
    data_loader: DataLoaderService = Depends(get_data_loader),
    current_user: dict = Depends(get_current_user),
):
    service = EnterpriseApiService(data_loader)
    return format_response(service.executive_dashboard())
