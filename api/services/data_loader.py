"""
Data loader service for Phase 3 datasets.

This service loads the three Phase 3 production datasets at application
startup and provides cached access to them for all API endpoints.

Loaded datasets:
- transactions_risk_table.csv (294,722 rows)
- supplier_risk_table.csv (2,293 rows)
- monitoring_dataset.csv (18 rows)
"""

import logging
import os
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class DataLoaderService:
    """Service for loading and managing Phase 3 datasets."""

    def __init__(self, data_dir: str = "src/data/products"):
        """
        Initialize the data loader service.

        Args:
            data_dir: Path to the data directory containing Phase 3 products
        """
        self.data_dir = Path(data_dir)
        self.transactions_df: Optional[pd.DataFrame] = None
        self.suppliers_df: Optional[pd.DataFrame] = None
        self.monitoring_df: Optional[pd.DataFrame] = None
        self.contracts_df: Optional[pd.DataFrame] = None
        self.loaded_at: Optional[datetime] = None
        self.load_status = {
            "transactions": False,
            "suppliers": False,
            "monitoring": False,
            "contracts": False,
        }
        # Simple in-memory caches for single-record lookups
        self._txn_cache: Dict[int, Dict[str, Any]] = {}
        self._sup_cache: Dict[int, Dict[str, Any]] = {}
        self._supplier_names: Dict[int, str] = {}

    def load_all(self) -> bool:
        """
        Load all Phase 3 datasets.

        Returns:
            bool: True if all datasets loaded successfully, False otherwise
        """
        try:
            logger.info("Starting Phase 3 dataset loading...")
            
            # Load transactions
            self.load_transactions()
            
            # Load suppliers
            self.load_suppliers()
            
            # Load monitoring metrics
            self.load_monitoring()
            # Load contracts if available
            self.load_contracts()
            # Build supplier_id -> supplier_name lookup
            self.load_supplier_names()
            
            self.loaded_at = datetime.utcnow()
            
            # Log summary
            logger.info(f"✓ Transactions loaded: {len(self.transactions_df):,} rows")
            logger.info(f"✓ Suppliers loaded: {len(self.suppliers_df):,} rows")
            logger.info(f"✓ Monitoring metrics loaded: {len(self.monitoring_df):,} rows")
            if self.contracts_df is not None:
                logger.info(f"✓ Contracts loaded: {len(self.contracts_df):,} rows")
            else:
                logger.info("✓ Contracts dataset not found or failed to load")
            logger.info("All datasets loaded successfully!")
            
            return all(self.load_status.values())
        except Exception as e:
            logger.error(f"Failed to load datasets: {str(e)}")
            return False

    def load_transactions(self) -> None:
        """Load transactions_risk_table.csv."""
        try:
            file_path = self.data_dir / "transactions_risk_table.csv"
            logger.debug(f"Loading transactions from {file_path}")
            
            self.transactions_df = pd.read_csv(file_path)
            
            # Create indexed views for fast lookup
            self.transactions_df.set_index("transaction_id", inplace=False)
            
            self.load_status["transactions"] = True
            logger.info(f"Transactions loaded: {len(self.transactions_df)} rows, {len(self.transactions_df.columns)} columns")
        except Exception as e:
            logger.error(f"Failed to load transactions: {str(e)}")
            self.load_status["transactions"] = False
            raise

    def load_suppliers(self) -> None:
        """Load supplier_risk_table.csv."""
        try:
            file_path = self.data_dir / "supplier_risk_table.csv"
            logger.debug(f"Loading suppliers from {file_path}")
            
            self.suppliers_df = pd.read_csv(file_path)
            self.load_status["suppliers"] = True
            logger.info(f"Suppliers loaded: {len(self.suppliers_df)} rows, {len(self.suppliers_df.columns)} columns")
        except Exception as e:
            logger.error(f"Failed to load suppliers: {str(e)}")
            self.load_status["suppliers"] = False
            raise

    def load_monitoring(self) -> None:
        """Load monitoring_dataset.csv."""
        try:
            file_path = self.data_dir / "monitoring_dataset.csv"
            logger.debug(f"Loading monitoring metrics from {file_path}")
            
            self.monitoring_df = pd.read_csv(file_path)
            self.load_status["monitoring"] = True
            logger.info(f"Monitoring metrics loaded: {len(self.monitoring_df)} rows, {len(self.monitoring_df.columns)} columns")
        except Exception as e:
            logger.error(f"Failed to load monitoring: {str(e)}")
            self.load_status["monitoring"] = False
            raise

    def load_supplier_names(self) -> None:
        """Build a supplier_id -> supplier_name lookup from the raw documents dataset."""
        try:
            file_path = Path("src/data/raw/Documents1.csv")
            if not file_path.exists():
                logger.warning("Supplier name lookup not built — %s not found", file_path)
                return
            df = pd.read_csv(file_path, usecols=["supplier_id", "supplier_name"], low_memory=False)
            names = df.dropna().drop_duplicates("supplier_id")
            self._supplier_names = {
                int(row.supplier_id): str(row.supplier_name) for row in names.itertuples()
            }
            logger.info(f"Supplier name lookup built: {len(self._supplier_names)} suppliers")
        except Exception as e:
            logger.error(f"Failed to build supplier name lookup: {str(e)}")

    def load_contracts(self) -> None:
        """Load Contracts.csv for contract-level RAG retrieval."""
        try:
            file_path = Path(os.getenv("CONTRACTS_CSV_PATH", "Contracts.csv"))
            if not file_path.exists():
                raise FileNotFoundError(f"Contracts CSV not found at {file_path}")
            logger.debug(f"Loading contracts from {file_path}")
            self.contracts_df = pd.read_csv(file_path)
            self.load_status["contracts"] = True
            logger.info(f"Contracts loaded: {len(self.contracts_df)} rows, {len(self.contracts_df.columns)} columns")
        except Exception as e:
            logger.error(f"Failed to load contracts: {str(e)}")
            self.contracts_df = None
            self.load_status["contracts"] = False
            raise

    # ========================================================================
    # TRANSACTION QUERIES
    # ========================================================================

    def get_transaction(self, transaction_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single transaction by ID.

        Args:
            transaction_id: Transaction ID to retrieve

        Returns:
            Transaction record as dict, or None if not found
        """
        if self.transactions_df is None:
            return None
        
        # Check cache first
        if transaction_id in self._txn_cache:
            return self._txn_cache[transaction_id]

        matches = self.transactions_df[self.transactions_df["transaction_id"] == transaction_id]
        if len(matches) == 0:
            return None

        result = matches.iloc[0].to_dict()
        # Cache result
        try:
            self._txn_cache[transaction_id] = result
        except Exception:
            pass
        return result

    def get_transactions(
        self,
        page: int = 1,
        page_size: int = 50,
        risk_level: Optional[str] = None,
        min_risk_score: Optional[float] = None,
        max_risk_score: Optional[float] = None,
        has_anomaly: Optional[bool] = None,
        is_delayed: Optional[bool] = None,
        sort_by: str = "risk_score",
        order: str = "desc",
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Get paginated transactions with optional filters.

        Args:
            page: Page number (1-indexed)
            page_size: Number of records per page
            risk_level: Filter by risk level (LOW, MEDIUM, HIGH, CRITICAL)
            min_risk_score: Minimum risk score
            max_risk_score: Maximum risk score
            has_anomaly: Filter by anomaly flag
            is_delayed: Filter by delay flag
            sort_by: Column to sort by
            order: Sort order ('asc' or 'desc')

        Returns:
            Tuple of (filtered records, total count)
        """
        if self.transactions_df is None:
            return [], 0
        
        df = self.transactions_df.copy()
        
        # Apply filters
        if risk_level:
            df = df[df["risk_level"] == risk_level]
        if min_risk_score is not None:
            df = df[df["risk_score"] >= min_risk_score]
        if max_risk_score is not None:
            df = df[df["risk_score"] <= max_risk_score]
        if has_anomaly is not None:
            df = df[df["has_anomaly"] == (1 if has_anomaly else 0)]
        if is_delayed is not None:
            df = df[df["is_delayed"] == (1 if is_delayed else 0)]
        
        total_count = len(df)
        
        # Sort
        if sort_by in df.columns:
            ascending = order == "asc"
            df = df.sort_values(sort_by, ascending=ascending)
        
        # Paginate
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        df = df.iloc[start_idx:end_idx]
        
        return df.to_dict("records"), total_count

    def get_high_risk_transactions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get high-risk transactions."""
        if self.transactions_df is None:
            return []
        
        df = self.transactions_df[
            (self.transactions_df["risk_level"].isin(["HIGH", "CRITICAL"]))
        ].head(limit)
        
        return df.to_dict("records")

    # ========================================================================
    # SUPPLIER QUERIES
    # ========================================================================

    def get_supplier(self, supplier_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single supplier by ID.

        Args:
            supplier_id: Supplier ID to retrieve

        Returns:
            Supplier record as dict, or None if not found
        """
        if self.suppliers_df is None:
            return None
        
        # Cache lookup
        if supplier_id in self._sup_cache:
            return self._sup_cache[supplier_id]

        matches = self.suppliers_df[self.suppliers_df["supplier_id"] == supplier_id]
        if len(matches) == 0:
            return None

        result = matches.iloc[0].to_dict()
        try:
            self._sup_cache[supplier_id] = result
        except Exception:
            pass
        return result

    def get_suppliers(
        self,
        page: int = 1,
        page_size: int = 50,
        risk_level: Optional[str] = None,
        cluster_label: Optional[str] = None,
        min_risk_score: Optional[float] = None,
        max_risk_score: Optional[float] = None,
        sort_by: str = "risk_score",
        order: str = "desc",
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Get paginated suppliers with optional filters.

        Args:
            page: Page number (1-indexed)
            page_size: Number of records per page
            risk_level: Filter by risk level
            cluster_label: Filter by cluster label
            min_risk_score: Minimum risk score
            max_risk_score: Maximum risk score
            sort_by: Column to sort by
            order: Sort order ('asc' or 'desc')

        Returns:
            Tuple of (filtered records, total count)
        """
        if self.suppliers_df is None:
            return [], 0
        
        df = self.suppliers_df.copy()
        
        # Apply filters
        if risk_level:
            df = df[df["risk_level"] == risk_level]
        if cluster_label:
            df = df[df["cluster_label"] == cluster_label]
        if min_risk_score is not None:
            df = df[df["risk_score"] >= min_risk_score]
        if max_risk_score is not None:
            df = df[df["risk_score"] <= max_risk_score]
        
        total_count = len(df)
        
        # Sort
        if sort_by in df.columns:
            ascending = order == "asc"
            df = df.sort_values(sort_by, ascending=ascending)
        
        # Paginate
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        df = df.iloc[start_idx:end_idx]
        
        return df.to_dict("records"), total_count

    def get_high_risk_suppliers(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get high-risk suppliers ranked by risk_score."""
        if self.suppliers_df is None:
            return []

        df = self.suppliers_df[
            self.suppliers_df["risk_level"].isin(["HIGH", "CRITICAL"])
        ].nlargest(limit, "risk_score")

        return df.to_dict("records")

    # ========================================================================
    # MONITORING QUERIES
    # ========================================================================

    def get_metrics(self) -> List[Dict[str, Any]]:
        """Get all monitoring metrics."""
        if self.monitoring_df is None:
            return []
        
        return self.monitoring_df.to_dict("records")

    def get_metric(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific metric by name."""
        if self.monitoring_df is None:
            return None
        
        matches = self.monitoring_df[self.monitoring_df["metric_name"] == metric_name]
        if len(matches) == 0:
            return None
        
        return matches.iloc[0].to_dict()

    def get_metrics_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get metrics filtered by category."""
        if self.monitoring_df is None:
            return []
        
        df = self.monitoring_df[self.monitoring_df["category"] == category]
        return df.to_dict("records")

    # ========================================================================
    # AGGREGATION & STATISTICS
    # ========================================================================

    def get_global_stats(self) -> Dict[str, Any]:
        """
        Calculate global statistics from transactions dataset.

        Returns:
            Dictionary with global metrics
        """
        if self.transactions_df is None:
            return {}
        
        txn = self.transactions_df
        
        return {
            "total_transactions": len(txn),
            "unique_suppliers": txn["supplier_id"].nunique(),
            "avg_risk_score": float(txn["risk_score"].mean()),
            "median_risk_score": float(txn["risk_score"].median()),
            "max_risk_score": float(txn["risk_score"].max()),
            "min_risk_score": float(txn["risk_score"].min()),
            "std_risk_score": float(txn["risk_score"].std()),
            "delayed_transactions": int(txn["is_delayed"].sum()),
            "delayed_pct": float((txn["is_delayed"].sum() / len(txn) * 100)),
            "transactions_with_anomalies": int(txn["has_anomaly"].sum()),
            "anomalies_pct": float((txn["has_anomaly"].sum() / len(txn) * 100)),
            "avg_days_in_system": float(txn["days_in_system"].mean()),
        }

    def get_risk_distribution(self) -> Dict[str, Any]:
        """
        Get risk level distribution.

        Returns:
            Dictionary with counts and percentages by risk level
        """
        if self.transactions_df is None:
            return {}
        
        txn = self.transactions_df
        total = len(txn)
        
        result = {}
        for level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            count = len(txn[txn["risk_level"] == level])
            result[level] = {
                "count": count,
                "percentage": float((count / total * 100)) if total > 0 else 0,
            }
        
        return result

    def search_transactions(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search transactions by transaction_id or supplier_id.

        Args:
            query: Search query (numeric)
            limit: Maximum results to return

        Returns:
            List of matching transactions
        """
        if self.transactions_df is None:
            return []
        
        try:
            query_int = int(query)
            df = self.transactions_df[
                (self.transactions_df["transaction_id"] == query_int) |
                (self.transactions_df["supplier_id"] == query_int)
            ].head(limit)
            return df.to_dict("records")
        except ValueError:
            return []

    def search_suppliers(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search suppliers by supplier_id.

        Args:
            query: Search query (numeric)
            limit: Maximum results to return

        Returns:
            List of matching suppliers
        """
        if self.suppliers_df is None:
            return []
        
        try:
            query_int = int(query)
            df = self.suppliers_df[
                self.suppliers_df["supplier_id"] == query_int
            ].head(limit)
            return df.to_dict("records")
        except ValueError:
            return []

    def get_supplier_name(self, supplier_id: int) -> Optional[str]:
        """Look up a supplier's display name from the contracts dataset."""
        return self._supplier_names.get(int(supplier_id))

    def is_healthy(self) -> bool:
        """Check if all datasets are loaded."""
        return all(self.load_status.values())
