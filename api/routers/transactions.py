"""Transactions API router."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from ..services.data_loader import DataLoaderService
from ..services.risk_service import RiskService
from ..core.deps import get_data_loader
from ..auth.dependencies import get_current_user
from ..core.response import format_response
import logging

router = APIRouter(tags=["Transactions"])
logger = logging.getLogger(__name__)


@router.get("/transactions")
def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    risk_level: Optional[str] = Query(None),
    min_risk_score: Optional[float] = Query(None),
    max_risk_score: Optional[float] = Query(None),
    has_anomaly: Optional[bool] = Query(None),
    is_delayed: Optional[bool] = Query(None),
    sort_by: str = Query("risk_score"),
    order: str = Query("desc"),
    data_loader: DataLoaderService = Depends(get_data_loader),
    current_user: dict = Depends(get_current_user),
):
    try:
        records, total = data_loader.get_transactions(
            page=page,
            page_size=page_size,
            risk_level=risk_level,
            min_risk_score=min_risk_score,
            max_risk_score=max_risk_score,
            has_anomaly=has_anomaly,
            is_delayed=is_delayed,
            sort_by=sort_by,
            order=order,
        )
        metadata = {"total": total, "count": len(records), "page": page, "page_size": page_size}
        return format_response({"transactions": records}, metadata=metadata)
    except Exception as e:
        logger.exception("Failed to list transactions")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: int, data_loader: DataLoaderService = Depends(get_data_loader), current_user: dict = Depends(get_current_user)):
    txn = data_loader.get_transaction(transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")
    return format_response(txn)


@router.get("/transactions/high-risk")
def high_risk_transactions(limit: int = 100, data_loader: DataLoaderService = Depends(get_data_loader), current_user: dict = Depends(get_current_user)):
    records = data_loader.get_high_risk_transactions(limit=limit)
    metadata = {"count": len(records)}
    return format_response({"transactions": records}, metadata=metadata)
