"""Risk API router."""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from ..services.data_loader import DataLoaderService
from ..services.risk_service import RiskService
from ..models.schemas import SuccessResponse
from ..core.deps import get_data_loader
from ..auth.dependencies import get_current_user
from ..core.response import format_response
import logging

router = APIRouter(tags=["Risk"])
logger = logging.getLogger(__name__)


@router.get("/risk/score/{transaction_id}")
def get_risk_score(transaction_id: int, data_loader: DataLoaderService = Depends(get_data_loader), current_user: dict = Depends(get_current_user)):
    risk_svc = RiskService(data_loader)
    result = risk_svc.get_transaction_risk(transaction_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")
    return format_response(result)


@router.get("/risk/explain/{transaction_id}")
def get_risk_explain(transaction_id: int, data_loader: DataLoaderService = Depends(get_data_loader), current_user: dict = Depends(get_current_user)):
    risk_svc = RiskService(data_loader)
    result = risk_svc.get_transaction_explanation(transaction_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")
    return format_response(result)


@router.get("/risk/compare/{transaction_id}")
def compare_risk(transaction_id: int, data_loader: DataLoaderService = Depends(get_data_loader), current_user: dict = Depends(get_current_user)):
    risk_svc = RiskService(data_loader)
    result = risk_svc.compare_risks(transaction_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found or supplier missing")
    return format_response(result)
