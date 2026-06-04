"""
Suppliers API router.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from ..services.data_loader import DataLoaderService
from ..services.risk_service import RiskService
from ..models.schemas import SuccessResponse
from ..core.deps import get_data_loader
from ..auth.dependencies import get_current_user
from ..core.response import format_response
import logging

router = APIRouter(tags=["Suppliers"])
logger = logging.getLogger(__name__)


@router.get("/suppliers", response_model=SuccessResponse)
def list_suppliers(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    risk_level: Optional[str] = Query(None),
    cluster_label: Optional[str] = Query(None),
    min_risk_score: Optional[float] = Query(None),
    max_risk_score: Optional[float] = Query(None),
    sort_by: str = Query("risk_score"),
    order: str = Query("desc"),
    data_loader: DataLoaderService = Depends(get_data_loader),
    current_user: dict = Depends(get_current_user),
):
    try:
        records, total = data_loader.get_suppliers(
            page=page,
            page_size=page_size,
            risk_level=risk_level,
            cluster_label=cluster_label,
            min_risk_score=min_risk_score,
            max_risk_score=max_risk_score,
            sort_by=sort_by,
            order=order,
        )

        metadata = {"total": total, "count": len(records), "page": page, "page_size": page_size}
        return format_response({"suppliers": records}, metadata=metadata)
    except Exception as e:
        logger.exception("Failed to list suppliers")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suppliers/{supplier_id}")
def get_supplier(supplier_id: int, data_loader: DataLoaderService = Depends(get_data_loader), current_user: dict = Depends(get_current_user)):
    sup = data_loader.get_supplier(supplier_id)
    if not sup:
        raise HTTPException(status_code=404, detail=f"Supplier {supplier_id} not found")
    return format_response(sup)


@router.get("/suppliers/high-risk")
def high_risk_suppliers(limit: int = 50, data_loader: DataLoaderService = Depends(get_data_loader), current_user: dict = Depends(get_current_user)):
    records = data_loader.get_high_risk_suppliers(limit=limit)
    metadata = {"count": len(records)}
    return format_response({"suppliers": records}, metadata=metadata)
