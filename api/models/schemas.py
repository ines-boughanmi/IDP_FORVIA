"""
Pydantic schemas for API request/response serialization.

These schemas define the structure of all API responses and handle
validation of incoming data.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============================================================================
# TRANSACTION MODELS
# ============================================================================

class TransactionBase(BaseModel):
    """Base transaction schema with core fields."""
    transaction_id: int
    supplier_id: int
    gr_amount: float
    ir_amount: float
    amount_difference: float
    amount_gap_pct: float
    days_in_system: int
    risk_score: float
    risk_level: str
    risk_flag: int
    anomaly_classification: str
    is_delayed: int
    has_anomaly: int
    supplier_risk_score: float
    supplier_risk_level: str
    explanation: str
    data_version: str
    created_timestamp: str


class TransactionDetail(TransactionBase):
    """Detailed transaction response with all fields."""
    pass


class TransactionSummary(BaseModel):
    """Lightweight transaction summary for list views."""
    transaction_id: int
    supplier_id: int
    risk_score: float
    risk_level: str
    risk_flag: int
    is_delayed: int
    has_anomaly: int
    supplier_risk_score: float
    days_in_system: int
    amount_difference: float


class TransactionListResponse(BaseModel):
    """Paginated transaction list response."""
    total: int
    count: int
    page: int
    page_size: int
    transactions: List[TransactionSummary]


class TransactionSearchResult(BaseModel):
    """Single result from transaction search."""
    transaction_id: int
    supplier_id: int
    risk_score: float
    risk_level: str
    explanation: str
    match_score: float = Field(default=1.0, description="Search relevance score")


class TransactionSearchResponse(BaseModel):
    """Search results for transactions."""
    query: str
    total_results: int
    results: List[TransactionSearchResult]


# ============================================================================
# SUPPLIER MODELS
# ============================================================================

class SupplierBase(BaseModel):
    """Base supplier schema with core fields."""
    supplier_id: int
    risk_score: float
    risk_level: str
    cluster_id: int
    cluster_label: str
    anomaly_rate: float
    accounting_issue_rate: float
    data_issue_rate: float
    avg_aging_days: float
    aging_std_dev: float
    amount_volatility: float
    transaction_frequency: int
    stability_score: float
    explanation: str
    data_version: str
    created_timestamp: str


class SupplierDetail(SupplierBase):
    """Detailed supplier response with all fields."""
    pass


class SupplierSummary(BaseModel):
    """Lightweight supplier summary for list views."""
    supplier_id: int
    risk_score: float
    risk_level: str
    cluster_label: str
    anomaly_rate: float
    transaction_frequency: int
    stability_score: float


class SupplierListResponse(BaseModel):
    """Paginated supplier list response."""
    total: int
    count: int
    page: int
    page_size: int
    suppliers: List[SupplierSummary]


class SupplierSearchResult(BaseModel):
    """Single result from supplier search."""
    supplier_id: int
    risk_score: float
    risk_level: str
    cluster_label: str
    explanation: str
    match_score: float = Field(default=1.0)


class SupplierSearchResponse(BaseModel):
    """Search results for suppliers."""
    query: str
    total_results: int
    results: List[SupplierSearchResult]


# ============================================================================
# RISK MODELS
# ============================================================================

class RiskScore(BaseModel):
    """Risk score response."""
    transaction_id: int
    supplier_id: int
    risk_score: float
    risk_level: str
    risk_flag: int
    risk_components: Dict[str, Any] = Field(
        default={},
        description="Risk score breakdown by component"
    )


class RiskExplanation(BaseModel):
    """Risk explanation response."""
    transaction_id: int
    supplier_id: int
    risk_score: float
    risk_level: str
    explanation_text: str
    risk_factors: List[str] = Field(
        default_factory=list,
        description="List of identified risk factors"
    )
    anomaly_type: Optional[str] = None
    is_delayed: bool
    has_anomaly: bool


class RiskComparison(BaseModel):
    """Comparison of transaction vs supplier risk."""
    transaction_id: int
    transaction_risk_score: float
    transaction_risk_level: str
    supplier_id: int
    supplier_risk_score: float
    supplier_risk_level: str
    combined_risk_score: float
    combined_risk_level: str


# ============================================================================
# ANALYTICS & METRICS MODELS
# ============================================================================

class MetricValue(BaseModel):
    """Single metric value."""
    metric_name: str
    metric_value: float
    metric_type: str = Field(default="gauge")
    category: str


class GlobalMetrics(BaseModel):
    """Global system metrics."""
    total_transactions: int
    unique_suppliers: int
    avg_transaction_risk_score: float
    median_transaction_risk_score: float
    max_transaction_risk_score: float
    min_transaction_risk_score: float
    avg_supplier_risk_score: float
    delayed_transactions_count: int
    delayed_transactions_pct: float
    transactions_with_anomalies_count: int
    transactions_with_anomalies_pct: float
    avg_days_in_system: float


class RiskDistribution(BaseModel):
    """Risk level distribution metrics."""
    LOW: Dict[str, Any] = Field(description="LOW risk metrics")
    MEDIUM: Dict[str, Any] = Field(description="MEDIUM risk metrics")
    HIGH: Dict[str, Any] = Field(description="HIGH risk metrics")
    CRITICAL: Dict[str, Any] = Field(description="CRITICAL risk metrics")


class SupplierMetrics(BaseModel):
    """Supplier-level metrics."""
    total_suppliers: int
    high_risk_suppliers: int
    high_risk_pct: float
    standard_suppliers: int
    standard_pct: float
    avg_anomaly_rate: float
    avg_stability_score: float
    avg_aging_days: float


class DashboardMetrics(BaseModel):
    """All dashboard metrics combined."""
    global_metrics: GlobalMetrics
    risk_distribution: RiskDistribution
    supplier_metrics: SupplierMetrics
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ============================================================================
# ERROR MODELS
# ============================================================================

class ErrorDetail(BaseModel):
    """Standard error response."""
    error: str
    detail: str
    status_code: int
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ErrorResponse(BaseModel):
    """Error response wrapper."""
    status: str = "error"
    error: ErrorDetail


# ============================================================================
# QUERY PARAMETERS
# ============================================================================

class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=1000)
    sort_by: Optional[str] = None
    order: str = Field(default="desc", pattern="^(asc|desc)$")


class FilterParams(BaseModel):
    """Filter parameters for list endpoints."""
    risk_level: Optional[str] = None
    min_risk_score: Optional[float] = None
    max_risk_score: Optional[float] = None
    has_anomaly: Optional[bool] = None
    is_delayed: Optional[bool] = None


# ============================================================================
# SUCCESS RESPONSE WRAPPER
# ============================================================================

class SuccessResponse(BaseModel):
    """Generic success response wrapper."""
    status: str = "success"
    data: Any
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
