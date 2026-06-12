from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .data_loader import DataLoaderService


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    try:
        return float(value)
    except Exception:
        return None


def _to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    try:
        return int(value)
    except Exception:
        return None


def _iso_datetime(value: Any) -> str:
    if value is None:
        return datetime.utcnow().isoformat()
    try:
        if pd.isna(value):
            return datetime.utcnow().isoformat()
    except Exception:
        pass
    try:
        parsed = pd.to_datetime(value, errors="coerce")
        if pd.isna(parsed):
            return str(value)
        return parsed.to_pydatetime().isoformat()
    except Exception:
        return str(value)


def _record_to_json(record: Dict[str, Any]) -> Dict[str, Any]:
    cleaned: Dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, (pd.Timestamp, datetime)):
            cleaned[key] = value.isoformat()
        elif hasattr(value, "item"):
            try:
                cleaned[key] = value.item()
            except Exception:
                cleaned[key] = value
        else:
            cleaned[key] = value
    return cleaned


@dataclass
class EnterpriseApiService:
    data_loader: DataLoaderService

    # ------------------------------------------------------------------
    # Executive dashboard
    # ------------------------------------------------------------------
    def executive_dashboard(self) -> Dict[str, Any]:
        stats = self.data_loader.get_global_stats()
        supplier_df = self.data_loader.suppliers_df
        txn_df = self.data_loader.transactions_df

        critical_transactions = 0
        high_transactions = 0
        critical_suppliers = 0
        high_risk_suppliers = 0
        top_risk_supplier: Optional[Dict[str, Any]] = None

        if txn_df is not None and not txn_df.empty:
            critical_transactions = int((txn_df["risk_level"] == "CRITICAL").sum())
            high_transactions = int((txn_df["risk_level"] == "HIGH").sum())

        if supplier_df is not None and not supplier_df.empty:
            critical_suppliers = int((supplier_df["risk_level"] == "CRITICAL").sum())
            high_risk_suppliers = int((supplier_df["risk_level"] == "HIGH").sum())
            top = supplier_df.sort_values("risk_score", ascending=False).iloc[0].to_dict()
            top_supplier_id = _to_int(top.get("supplier_id"))
            top_risk_supplier = {
                "supplier_id": top_supplier_id,
                "supplier_name": self.data_loader.get_supplier_name(top_supplier_id) if top_supplier_id is not None else None,
                "risk_score": _to_float(top.get("risk_score")),
                "risk_level": top.get("risk_level"),
                "cluster_label": top.get("cluster_label"),
                "explanation": top.get("explanation"),
            }

        return {
            "total_transactions": stats.get("total_transactions", 0),
            "total_suppliers": stats.get("unique_suppliers", 0),
            "avg_transaction_risk": stats.get("avg_risk_score", 0),
            "avg_supplier_risk": float(supplier_df["risk_score"].mean()) if supplier_df is not None and not supplier_df.empty else 0,
            "critical_transactions": critical_transactions,
            "high_transactions": high_transactions,
            "critical_suppliers": critical_suppliers,
            "high_risk_suppliers": high_risk_suppliers,
            "anomaly_rate": stats.get("anomalies_pct", 0),
            "top_risk_supplier": top_risk_supplier,
        }

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------
    def search_transactions(
        self,
        supplier_id: Optional[int] = None,
        risk_level: Optional[str] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[Dict[str, Any]], int]:
        df = self.data_loader.transactions_df
        if df is None or df.empty:
            return [], 0

        filtered = df.copy()

        if supplier_id is not None:
            filtered = filtered[filtered["supplier_id"] == supplier_id]
        if risk_level:
            filtered = filtered[filtered["risk_level"] == risk_level]
        if min_score is not None:
            filtered = filtered[filtered["risk_score"] >= min_score]
        if max_score is not None:
            filtered = filtered[filtered["risk_score"] <= max_score]

        if date_from or date_to:
            timestamps = pd.to_datetime(filtered["created_timestamp"], errors="coerce")
            if date_from:
                from_ts = pd.to_datetime(date_from, errors="coerce")
                if not pd.isna(from_ts):
                    filtered = filtered[timestamps >= from_ts]
            if date_to:
                to_ts = pd.to_datetime(date_to, errors="coerce")
                if not pd.isna(to_ts):
                    filtered = filtered[timestamps <= to_ts]

        if keyword:
            keyword_mask = (
                filtered["explanation"].astype(str).str.contains(keyword, case=False, na=False)
                | filtered["anomaly_classification"].astype(str).str.contains(keyword, case=False, na=False)
                | filtered["data_version"].astype(str).str.contains(keyword, case=False, na=False)
                | filtered["risk_level"].astype(str).str.contains(keyword, case=False, na=False)
                | filtered["transaction_id"].astype(str).str.contains(keyword, case=False, na=False)
                | filtered["supplier_id"].astype(str).str.contains(keyword, case=False, na=False)
            )
            filtered = filtered[keyword_mask]

        total = len(filtered)
        filtered = filtered.sort_values(["risk_score", "created_timestamp"], ascending=[False, False])
        offset = (page - 1) * page_size
        records = filtered.iloc[offset : offset + page_size].to_dict("records")
        results = []
        for record in records:
            item = _record_to_json(record)
            item["supplier_name"] = self.data_loader.get_supplier_name(item["supplier_id"])
            results.append(item)
        return results, total

    def search_suppliers(
        self,
        supplier_id: Optional[int] = None,
        cluster: Optional[str] = None,
        risk_level: Optional[str] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[Dict[str, Any]], int]:
        df = self.data_loader.suppliers_df
        if df is None or df.empty:
            return [], 0

        filtered = df.copy()

        if supplier_id is not None:
            filtered = filtered[filtered["supplier_id"] == supplier_id]
        if cluster:
            if cluster.isdigit():
                filtered = filtered[filtered["cluster_id"] == int(cluster)]
            else:
                filtered = filtered[
                    (filtered["cluster_label"].astype(str).str.contains(cluster, case=False, na=False))
                    | (filtered["cluster_label"] == cluster)
                ]
        if risk_level:
            filtered = filtered[filtered["risk_level"] == risk_level]
        if min_score is not None:
            filtered = filtered[filtered["risk_score"] >= min_score]
        if max_score is not None:
            filtered = filtered[filtered["risk_score"] <= max_score]

        total = len(filtered)
        filtered = filtered.sort_values(["risk_score", "created_timestamp"], ascending=[False, False])
        offset = (page - 1) * page_size
        records = filtered.iloc[offset : offset + page_size].to_dict("records")
        results = []
        for record in records:
            item = _record_to_json(record)
            item["supplier_name"] = self.data_loader.get_supplier_name(item["supplier_id"])
            results.append(item)
        return results, total

    # ------------------------------------------------------------------
    # Alerts
    # ------------------------------------------------------------------
    def alerts_transactions(self) -> List[Dict[str, Any]]:
        df = self.data_loader.transactions_df
        if df is None or df.empty:
            return []
        filtered = df[df["risk_level"].isin(["HIGH", "CRITICAL"])].sort_values("risk_score", ascending=False).copy()
        filtered["alert_id"] = "txn-" + filtered["transaction_id"].astype(str)
        filtered["entity_type"] = "transaction"
        filtered["created_at"] = pd.to_datetime(filtered["created_timestamp"], errors="coerce").dt.strftime("%Y-%m-%dT%H:%M:%S")
        records = filtered[["alert_id", "entity_type", "risk_score", "risk_level", "explanation", "created_at", "supplier_id"]].to_dict("records")
        results = []
        for record in records:
            item = _record_to_json(record)
            item["supplier_name"] = self.data_loader.get_supplier_name(item["supplier_id"])
            results.append(item)
        return results

    def alerts_suppliers(self) -> List[Dict[str, Any]]:
        df = self.data_loader.suppliers_df
        if df is None or df.empty:
            return []
        filtered = df[df["risk_level"].isin(["HIGH", "CRITICAL"])].sort_values("risk_score", ascending=False).copy()
        filtered["alert_id"] = "sup-" + filtered["supplier_id"].astype(str)
        filtered["entity_type"] = "supplier"
        filtered["created_at"] = pd.to_datetime(filtered["created_timestamp"], errors="coerce").dt.strftime("%Y-%m-%dT%H:%M:%S")
        records = filtered[["alert_id", "entity_type", "risk_score", "risk_level", "explanation", "created_at", "supplier_id"]].to_dict("records")
        results = []
        for record in records:
            item = _record_to_json(record)
            item["supplier_name"] = self.data_loader.get_supplier_name(item["supplier_id"])
            results.append(item)
        return results

    def alerts_all(self) -> List[Dict[str, Any]]:
        return self.alerts_transactions() + self.alerts_suppliers()

    # ------------------------------------------------------------------
    # 360 views
    # ------------------------------------------------------------------
    def supplier_overview(self, supplier_id: int) -> Optional[Dict[str, Any]]:
        supplier = self.data_loader.get_supplier(supplier_id)
        if not supplier:
            return None

        txn_df = self.data_loader.transactions_df
        supplier_txn = txn_df[txn_df["supplier_id"] == supplier_id] if txn_df is not None else pd.DataFrame()

        transaction_statistics = {
            "total_transactions": int(len(supplier_txn)),
            "avg_transaction_risk": _to_float(supplier_txn["risk_score"].mean()) if not supplier_txn.empty else 0,
            "max_transaction_risk": _to_float(supplier_txn["risk_score"].max()) if not supplier_txn.empty else 0,
            "critical_transactions": int((supplier_txn["risk_level"] == "CRITICAL").sum()) if not supplier_txn.empty else 0,
            "high_transactions": int((supplier_txn["risk_level"] == "HIGH").sum()) if not supplier_txn.empty else 0,
            "delayed_transactions": int(supplier_txn["is_delayed"].sum()) if not supplier_txn.empty else 0,
            "anomalous_transactions": int(supplier_txn["has_anomaly"].sum()) if not supplier_txn.empty else 0,
            "total_gr_amount": _to_float(supplier_txn["gr_amount"].sum()) if not supplier_txn.empty else 0,
            "total_ir_amount": _to_float(supplier_txn["ir_amount"].sum()) if not supplier_txn.empty else 0,
        }

        recent_transactions = []
        if not supplier_txn.empty:
            recent_transactions = (
                supplier_txn.sort_values("created_timestamp", ascending=False)
                .head(5)
                .to_dict("records")
            )
            recent_transactions = [_record_to_json(record) for record in recent_transactions]

        return {
            "supplier_profile": _record_to_json(supplier),
            "supplier_name": self.data_loader.get_supplier_name(_to_int(supplier.get("supplier_id"))),
            "risk_score": _to_float(supplier.get("risk_score")),
            "risk_level": supplier.get("risk_level"),
            "cluster": {
                "cluster_id": _to_int(supplier.get("cluster_id")),
                "cluster_label": supplier.get("cluster_label"),
            },
            "behavior_metrics": {
                "avg_aging_days": _to_float(supplier.get("avg_aging_days")),
                "aging_std_dev": _to_float(supplier.get("aging_std_dev")),
                "amount_volatility": _to_float(supplier.get("amount_volatility")),
                "transaction_frequency": _to_int(supplier.get("transaction_frequency")),
                "stability_score": _to_float(supplier.get("stability_score")),
            },
            "anomaly_metrics": {
                "anomaly_rate": _to_float(supplier.get("anomaly_rate")),
                "accounting_issue_rate": _to_float(supplier.get("accounting_issue_rate")),
                "data_issue_rate": _to_float(supplier.get("data_issue_rate")),
            },
            "risk_explanation": supplier.get("explanation"),
            "transaction_statistics": transaction_statistics,
            "recent_transactions": recent_transactions,
        }

    def transaction_overview(self, transaction_id: int) -> Optional[Dict[str, Any]]:
        txn = self.data_loader.get_transaction(transaction_id)
        if not txn:
            return None

        supplier = self.data_loader.get_supplier(int(txn.get("supplier_id")))

        related_alerts = []
        if txn.get("risk_level") in {"HIGH", "CRITICAL"}:
            related_alerts.append(
                {
                    "alert_id": f"txn-{txn.get('transaction_id')}",
                    "entity_type": "transaction",
                    "risk_score": _to_float(txn.get("risk_score")),
                    "risk_level": txn.get("risk_level"),
                    "explanation": txn.get("explanation"),
                    "created_at": _iso_datetime(txn.get("created_timestamp")),
                }
            )

        if supplier and supplier.get("risk_level") in {"HIGH", "CRITICAL"}:
            related_alerts.append(
                {
                    "alert_id": f"sup-{supplier.get('supplier_id')}",
                    "entity_type": "supplier",
                    "risk_score": _to_float(supplier.get("risk_score")),
                    "risk_level": supplier.get("risk_level"),
                    "explanation": supplier.get("explanation"),
                    "created_at": _iso_datetime(supplier.get("created_timestamp")),
                }
            )

        risk_components = {
            "amount_gap_pct": _to_float(txn.get("amount_gap_pct")),
            "days_in_system": _to_int(txn.get("days_in_system")),
            "supplier_risk_score": _to_float(txn.get("supplier_risk_score")),
            "supplier_risk_level": txn.get("supplier_risk_level"),
            "risk_flag": _to_int(txn.get("risk_flag")),
            "anomaly_classification": txn.get("anomaly_classification"),
            "has_anomaly": _to_int(txn.get("has_anomaly")),
            "is_delayed": _to_int(txn.get("is_delayed")),
        }

        supplier_name = self.data_loader.get_supplier_name(int(txn.get("supplier_id")))
        transaction_profile = _record_to_json(txn)
        transaction_profile["supplier_name"] = supplier_name

        supplier_information = _record_to_json(supplier) if supplier else None
        if supplier_information is not None:
            supplier_information["supplier_name"] = supplier_name

        return {
            "transaction_profile": transaction_profile,
            "risk_components": risk_components,
            "supplier_information": supplier_information,
            "explanation": txn.get("explanation"),
            "alerts": related_alerts,
        }

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------
    def risk_distribution(self) -> Dict[str, Any]:
        return self.data_loader.get_risk_distribution()

    def top_risk_suppliers(self, limit: int = 20) -> List[Dict[str, Any]]:
        df = self.data_loader.suppliers_df
        if df is None or df.empty:
            return []
        records = (
            df.sort_values("risk_score", ascending=False)
            .head(limit)
            .to_dict("records")
        )
        results = []
        for record in records:
            item = _record_to_json(record)
            item["supplier_name"] = self.data_loader.get_supplier_name(item["supplier_id"])
            results.append(item)
        return results

    def cluster_distribution(self) -> Dict[str, Any]:
        df = self.data_loader.suppliers_df
        if df is None or df.empty:
            return {"clusters": []}

        grouped = (
            df.groupby(["cluster_id", "cluster_label"], dropna=False)
            .agg(
                suppliers=("supplier_id", "count"),
                avg_risk_score=("risk_score", "mean"),
                avg_stability_score=("stability_score", "mean"),
                avg_anomaly_rate=("anomaly_rate", "mean"),
            )
            .reset_index()
            .sort_values("suppliers", ascending=False)
        )

        clusters = []
        for _, row in grouped.iterrows():
            clusters.append(
                {
                    "cluster_id": _to_int(row.get("cluster_id")),
                    "cluster_label": row.get("cluster_label"),
                    "suppliers": _to_int(row.get("suppliers")),
                    "avg_risk_score": _to_float(row.get("avg_risk_score")),
                    "avg_stability_score": _to_float(row.get("avg_stability_score")),
                    "avg_anomaly_rate": _to_float(row.get("avg_anomaly_rate")),
                }
            )

        return {"clusters": clusters}

    def anomaly_summary(self) -> Dict[str, Any]:
        stats = self.data_loader.get_global_stats()
        txn_df = self.data_loader.transactions_df
        supplier_df = self.data_loader.suppliers_df

        return {
            "transactions_with_anomalies": stats.get("transactions_with_anomalies", 0),
            "anomaly_rate": stats.get("anomalies_pct", 0),
            "delayed_transactions": stats.get("delayed_transactions", 0),
            "delayed_rate": stats.get("delayed_pct", 0),
            "supplier_anomaly_rate_avg": _to_float(supplier_df["anomaly_rate"].mean()) if supplier_df is not None and not supplier_df.empty else 0,
            "critical_transaction_count": int((txn_df["risk_level"] == "CRITICAL").sum()) if txn_df is not None and not txn_df.empty else 0,
            "high_transaction_count": int((txn_df["risk_level"] == "HIGH").sum()) if txn_df is not None and not txn_df.empty else 0,
        }
