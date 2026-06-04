"""
Risk service for risk-specific operations.

This service provides risk analysis, scoring, and explanation
functionality on top of the data loader.
"""

import logging
from typing import Dict, List, Any, Optional
from .data_loader import DataLoaderService

logger = logging.getLogger(__name__)


class RiskService:
    """Service for risk-related operations."""

    def __init__(self, data_loader: DataLoaderService):
        """
        Initialize the risk service.

        Args:
            data_loader: DataLoaderService instance
        """
        self.data_loader = data_loader

    def get_transaction_risk(self, transaction_id: int) -> Optional[Dict[str, Any]]:
        """
        Get complete risk information for a transaction.

        Args:
            transaction_id: Transaction ID

        Returns:
            Risk information dict or None
        """
        txn = self.data_loader.get_transaction(transaction_id)
        if not txn:
            return None

        return {
            "transaction_id": txn.get("transaction_id"),
            "supplier_id": txn.get("supplier_id"),
            "risk_score": txn.get("risk_score"),
            "risk_level": txn.get("risk_level"),
            "risk_flag": txn.get("risk_flag"),
            "supplier_risk_score": txn.get("supplier_risk_score"),
            "supplier_risk_level": txn.get("supplier_risk_level"),
            "anomaly_classification": txn.get("anomaly_classification"),
            "is_delayed": txn.get("is_delayed"),
            "has_anomaly": txn.get("has_anomaly"),
        }

    def get_transaction_explanation(self, transaction_id: int) -> Optional[Dict[str, Any]]:
        """
        Get risk explanation for a transaction.

        Args:
            transaction_id: Transaction ID

        Returns:
            Explanation dict or None
        """
        txn = self.data_loader.get_transaction(transaction_id)
        if not txn:
            return None

        # Extract risk factors from explanation
        explanation_text = txn.get("explanation", "")
        risk_factors = self._parse_risk_factors(explanation_text)

        return {
            "transaction_id": txn.get("transaction_id"),
            "supplier_id": txn.get("supplier_id"),
            "risk_score": txn.get("risk_score"),
            "risk_level": txn.get("risk_level"),
            "explanation_text": explanation_text,
            "risk_factors": risk_factors,
            "anomaly_type": txn.get("anomaly_classification"),
            "is_delayed": bool(txn.get("is_delayed")),
            "has_anomaly": bool(txn.get("has_anomaly")),
            "days_in_system": txn.get("days_in_system"),
            "amount_gap_pct": txn.get("amount_gap_pct"),
        }

    def get_supplier_risk(self, supplier_id: int) -> Optional[Dict[str, Any]]:
        """
        Get complete risk information for a supplier.

        Args:
            supplier_id: Supplier ID

        Returns:
            Risk information dict or None
        """
        sup = self.data_loader.get_supplier(supplier_id)
        if not sup:
            return None

        return {
            "supplier_id": sup.get("supplier_id"),
            "risk_score": sup.get("risk_score"),
            "risk_level": sup.get("risk_level"),
            "cluster_label": sup.get("cluster_label"),
            "anomaly_rate": sup.get("anomaly_rate"),
            "accounting_issue_rate": sup.get("accounting_issue_rate"),
            "data_issue_rate": sup.get("data_issue_rate"),
            "stability_score": sup.get("stability_score"),
            "transaction_frequency": sup.get("transaction_frequency"),
            "avg_aging_days": sup.get("avg_aging_days"),
        }

    def compare_risks(self, transaction_id: int) -> Optional[Dict[str, Any]]:
        """
        Compare transaction risk with supplier risk.

        Args:
            transaction_id: Transaction ID

        Returns:
            Comparison dict or None
        """
        txn = self.data_loader.get_transaction(transaction_id)
        if not txn:
            return None

        supplier_id = txn.get("supplier_id")
        sup = self.data_loader.get_supplier(supplier_id)
        if not sup:
            return None

        txn_risk = txn.get("risk_score", 0)
        sup_risk = sup.get("risk_score", 0)
        
        # Calculate combined score as weighted average
        combined_score = (txn_risk * 0.6) + (sup_risk * 0.4)
        combined_level = self._score_to_level(combined_score)

        return {
            "transaction_id": transaction_id,
            "transaction_risk_score": txn_risk,
            "transaction_risk_level": txn.get("risk_level"),
            "supplier_id": supplier_id,
            "supplier_risk_score": sup_risk,
            "supplier_risk_level": sup.get("risk_level"),
            "combined_risk_score": combined_score,
            "combined_risk_level": combined_level,
            "risk_differential": txn_risk - sup_risk,
        }

    def get_supplier_risk_profile(self, supplier_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed risk profile for a supplier.

        Args:
            supplier_id: Supplier ID

        Returns:
            Risk profile dict or None
        """
        sup = self.data_loader.get_supplier(supplier_id)
        if not sup:
            return None

        return {
            "supplier_id": supplier_id,
            "risk_score": sup.get("risk_score"),
            "risk_level": sup.get("risk_level"),
            "cluster_label": sup.get("cluster_label"),
            "cluster_id": sup.get("cluster_id"),
            "risk_factors": {
                "anomaly_rate": float(sup.get("anomaly_rate", 0)),
                "accounting_issue_rate": float(sup.get("accounting_issue_rate", 0)),
                "data_issue_rate": float(sup.get("data_issue_rate", 0)),
                "avg_aging_days": float(sup.get("avg_aging_days", 0)),
                "amount_volatility": float(sup.get("amount_volatility", 0)),
                "stability_score": float(sup.get("stability_score", 0)),
            },
            "transaction_frequency": sup.get("transaction_frequency"),
            "explanation": sup.get("explanation"),
        }

    def get_high_risk_summary(self) -> Dict[str, Any]:
        """
        Get summary of high-risk transactions and suppliers.

        Returns:
            Summary dict
        """
        # Get high-risk transactions
        high_txns = self.data_loader.get_high_risk_transactions(limit=20)
        
        # Get high-risk suppliers
        high_sups = self.data_loader.get_high_risk_suppliers(limit=10)
        
        # Get risk distribution
        dist = self.data_loader.get_risk_distribution()
        
        return {
            "high_risk_transactions_count": len(high_txns),
            "high_risk_suppliers_count": len(high_sups),
            "top_risk_transactions": high_txns,
            "top_risk_suppliers": high_sups,
            "risk_distribution": dist,
        }

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    @staticmethod
    def _score_to_level(score: float) -> str:
        """
        Convert risk score to risk level.

        Args:
            score: Risk score (0-100)

        Returns:
            Risk level string
        """
        if score < 20:
            return "LOW"
        elif score < 35:
            return "MEDIUM"
        elif score < 50:
            return "HIGH"
        else:
            return "CRITICAL"

    @staticmethod
    def _parse_risk_factors(explanation_text: str) -> List[str]:
        """
        Extract risk factors from explanation text.

        Args:
            explanation_text: Risk explanation text

        Returns:
            List of identified risk factors
        """
        factors = []
        
        # Simple pattern matching for common risk factors
        text_lower = explanation_text.lower()
        
        if "aging" in text_lower or "days" in text_lower:
            factors.append("Transaction aging")
        if "amount" in text_lower or "gap" in text_lower:
            factors.append("Amount discrepancy")
        if "anomal" in text_lower:
            factors.append("Anomaly detected")
        if "delay" in text_lower:
            factors.append("Processing delay")
        if "volatil" in text_lower:
            factors.append("Amount volatility")
        if "issue" in text_lower or "problem" in text_lower:
            factors.append("Process issue")
        
        return factors if factors else ["Standard processing"]
