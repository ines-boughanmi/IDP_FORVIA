from __future__ import annotations

from typing import Optional

from .enterprise_service import EnterpriseApiService
from .data_loader import DataLoaderService


class ChatbotService:
    def __init__(self, data_loader: DataLoaderService):
        self.enterprise = EnterpriseApiService(data_loader)

    def supplier_context_builder(self, supplier_id: int) -> str:
        overview = self.enterprise.supplier_overview(supplier_id)
        if not overview:
            return f"Supplier {supplier_id} not found."

        supplier = overview["supplier_profile"]
        cluster = overview["cluster"]
        behavior = overview["behavior_metrics"]
        anomalies = overview["anomaly_metrics"]
        stats = overview["transaction_statistics"]

        return (
            f"Supplier narrative for supplier {supplier_id}: "
            f"risk level {overview['risk_level']} with score {overview['risk_score']}. "
            f"Cluster {cluster['cluster_label']} (ID {cluster['cluster_id']}). "
            f"Behavior shows {behavior['transaction_frequency']} transactions, "
            f"average aging {behavior['avg_aging_days']} days, stability score {behavior['stability_score']}. "
            f"Anomaly profile: anomaly rate {anomalies['anomaly_rate']}, "
            f"accounting issues {anomalies['accounting_issue_rate']}, data issues {anomalies['data_issue_rate']}. "
            f"The supplier has {stats['total_transactions']} linked transactions, "
            f"{stats['critical_transactions']} critical and {stats['high_transactions']} high-risk transactions. "
            f"Explanation: {overview['risk_explanation']}."
        )

    def transaction_context_builder(self, transaction_id: int) -> str:
        overview = self.enterprise.transaction_overview(transaction_id)
        if not overview:
            return f"Transaction {transaction_id} not found."

        txn = overview["transaction_profile"]
        supplier = overview["supplier_information"] or {}
        risk_components = overview["risk_components"]

        return (
            f"Transaction narrative for transaction {transaction_id}: "
            f"supplier {txn.get('supplier_id')} with transaction risk {txn.get('risk_score')} ({txn.get('risk_level')}). "
            f"Amount gap is {risk_components['amount_gap_pct']}% and days in system is {risk_components['days_in_system']}. "
            f"Supplier context: risk score {supplier.get('risk_score')} and level {supplier.get('risk_level')}. "
            f"Explanation: {overview['explanation']}."
        )

    def executive_context_builder(self) -> str:
        summary = self.enterprise.executive_dashboard()
        return (
            "Executive platform summary: "
            f"{summary['total_transactions']} transactions, "
            f"{summary['total_suppliers']} suppliers, "
            f"average transaction risk {summary['avg_transaction_risk']}, "
            f"average supplier risk {summary['avg_supplier_risk']}, "
            f"{summary['critical_transactions']} critical transactions, "
            f"{summary['high_transactions']} high transactions, "
            f"{summary['critical_suppliers']} critical suppliers, "
            f"{summary['high_risk_suppliers']} high-risk suppliers, "
            f"anomaly rate {summary['anomaly_rate']}%."
        )
