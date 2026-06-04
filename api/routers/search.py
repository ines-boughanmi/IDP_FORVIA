"""Search API router."""
from fastapi import APIRouter, Depends, Query

from ..auth.dependencies import get_current_user
from ..core.deps import get_data_loader
from ..core.response import format_response
from ..services.data_loader import DataLoaderService
from ..services.enterprise_service import EnterpriseApiService

router = APIRouter(tags=["Search"])


@router.get("/search/transactions")
def search_transactions(
    supplier_id: int | None = Query(None),
    risk_level: str | None = Query(None),
    min_score: float | None = Query(None),
    max_score: float | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    keyword: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    data_loader: DataLoaderService = Depends(get_data_loader),
    current_user: dict = Depends(get_current_user),
):
    service = EnterpriseApiService(data_loader)
    records, total = service.search_transactions(
        supplier_id=supplier_id,
        risk_level=risk_level,
        min_score=min_score,
        max_score=max_score,
        date_from=date_from,
        date_to=date_to,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    return format_response({"transactions": records}, metadata={"total": total, "count": len(records), "page": page, "page_size": page_size})


@router.get("/search/suppliers")
def search_suppliers(
    supplier_id: int | None = Query(None),
    cluster: str | None = Query(None),
    risk_level: str | None = Query(None),
    min_score: float | None = Query(None),
    max_score: float | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    data_loader: DataLoaderService = Depends(get_data_loader),
    current_user: dict = Depends(get_current_user),
):
    service = EnterpriseApiService(data_loader)
    records, total = service.search_suppliers(
        supplier_id=supplier_id,
        cluster=cluster,
        risk_level=risk_level,
        min_score=min_score,
        max_score=max_score,
        page=page,
        page_size=page_size,
    )
    return format_response({"suppliers": records}, metadata={"total": total, "count": len(records), "page": page, "page_size": page_size})


@router.get("/search/transaction")
def search_transaction(q: str = Query(...), limit: int = 20, data_loader: DataLoaderService = Depends(get_data_loader)):
    service = EnterpriseApiService(data_loader)
    records, total = service.search_transactions(keyword=q, page=1, page_size=limit)
    return format_response({"query": q, "total_results": total, "results": records})


@router.get("/search/supplier")
def search_supplier(q: str = Query(...), limit: int = 20, data_loader: DataLoaderService = Depends(get_data_loader)):
    service = EnterpriseApiService(data_loader)
    records, total = service.search_suppliers(supplier_id=int(q) if q.isdigit() else None, page=1, page_size=limit)
    return format_response({"query": q, "total_results": total, "results": records})
