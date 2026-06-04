#!/usr/bin/env python
"""
PHASE 2 — Supplier Explainability Engine
=========================================

Task 5: Generate business-readable explanations for each supplier.

Explanations are:
- Interpretable
- Actionable
- Monitoring-ready
- Dashboard-compatible
"""

import pandas as pd
import numpy as np
from pathlib import Path


class SupplierExplainabilityEngine:
    """
    Generate business-readable explanations for supplier risk profiles.
    """
    
    def __init__(self, verbose=True):
        self.verbose = verbose
    
    def log(self, msg):
        if self.verbose:
            print(f"  {msg}")
    
    # =========================================================================
    # CORE EXPLANATION GENERATION
    # =========================================================================
    
    def generate_supplier_explanation(self, supplier_row):
        """
        Generate comprehensive explanation for a single supplier.
        """
        reasons = []
        warnings = []
        strengths = []
        
        # Risk level
        risk_level = supplier_row.get('supplier_risk_level', 'UNKNOWN')
        risk_score = supplier_row.get('supplier_risk_score', 0)
        
        # Temporal analysis
        temporal_risk = supplier_row.get('risk_temporal', 0)
        aging = supplier_row.get('temporal_avg_aging_days', 0)
        temporal_consistency = supplier_row.get('temporal_temporal_consistency', 0)
        
        if temporal_risk > 60:
            reasons.append(f"High aging issues (avg {aging:.0f} days, risk {temporal_risk:.0f})")
        elif temporal_risk > 40:
            warnings.append(f"Moderate aging ({aging:.0f} days)")
        else:
            strengths.append(f"Good transaction timeliness ({aging:.0f} days)")
        
        if temporal_consistency > 0.8:
            strengths.append("Consistent processing timelines")
        elif temporal_consistency < 0.5:
            reasons.append("Highly inconsistent transaction delays")
        
        # Financial analysis
        financial_risk = supplier_row.get('risk_financial', 0)
        volatility = supplier_row.get('financial_amount_volatility_cv', 0)
        abnormal_ratio = supplier_row.get('financial_abnormal_amount_ratio', 0)
        
        if financial_risk > 60:
            reasons.append(f"High amount volatility (CV={volatility:.2f})")
        elif volatility > 0.5:
            warnings.append(f"Moderate amount volatility (CV={volatility:.2f})")
        
        if abnormal_ratio > 0.1:
            reasons.append(f"Abnormal amounts in {abnormal_ratio:.1%} of transactions")
        
        # Behavioral analysis
        behavioral_risk = supplier_row.get('risk_behavioral', 0)
        anomaly_ratio = supplier_row.get('behavioral_anomaly_ratio', 0)
        accounting_ratio = supplier_row.get('behavioral_accounting_issue_ratio', 0)
        data_ratio = supplier_row.get('behavioral_data_issue_ratio', 0)
        stability = supplier_row.get('behavioral_supplier_stability_score', 0)
        
        if behavioral_risk > 60:
            reasons.append(f"High behavioral risk ({behavioral_risk:.0f})")
        
        if anomaly_ratio > 0.1:
            reasons.append(f"Anomaly rate of {anomaly_ratio:.1%} transactions")
        
        if accounting_ratio > 0.05:
            warnings.append(f"Accounting issues in {accounting_ratio:.1%} of transactions")
        
        if data_ratio > 0.05:
            warnings.append(f"Data quality issues in {data_ratio:.1%} of transactions")
        
        if stability > 0.8:
            strengths.append("Stable operational behavior")
        
        # Business analysis
        business_risk = supplier_row.get('risk_business', 0)
        frequency = supplier_row.get('behavioral_transaction_frequency', 0)
        diversity = supplier_row.get('business_business_diversity', 0)
        repeat_ratio = supplier_row.get('business_repeat_po_ratio', 0)
        
        if frequency > 100:
            strengths.append(f"High transaction volume ({frequency:.0f} transactions)")
        elif frequency < 10:
            warnings.append(f"Low transaction volume ({frequency:.0f} transactions) - less predictable")
        
        if diversity > 0.7:
            strengths.append("Good business diversity across POs")
        elif diversity < 0.3:
            warnings.append("Limited business diversity")
        
        if repeat_ratio > 0.5:
            strengths.append("Repetitive PO patterns - predictable")
        
        # Build explanation text
        summary = f"This supplier is {risk_level} risk (score: {risk_score:.1f}/100)."
        
        if reasons:
            reason_text = "\n\nRisk factors:\n" + "\n".join([f"• {r}" for r in reasons])
        else:
            reason_text = ""
        
        if warnings:
            warning_text = "\n\nWarning signs:\n" + "\n".join([f"• {w}" for w in warnings])
        else:
            warning_text = ""
        
        if strengths:
            strength_text = "\n\nStrengths:\n" + "\n".join([f"• {s}" for s in strengths])
        else:
            strength_text = ""
        
        # Recommendations
        recommendations = self._generate_recommendations(risk_level, reasons)
        if recommendations:
            rec_text = "\n\nRecommendations:\n" + "\n".join([f"• {r}" for r in recommendations])
        else:
            rec_text = ""
        
        explanation = summary + reason_text + warning_text + strength_text + rec_text
        
        return {
            'explanation': explanation,
            'reasons': reasons,
            'warnings': warnings,
            'strengths': strengths,
            'reason_count': len(reasons),
            'warning_count': len(warnings),
            'strength_count': len(strengths),
        }
    
    def _generate_recommendations(self, risk_level, reasons):
        """
        Generate actionable recommendations based on risk profile.
        """
        recommendations = []
        
        if risk_level == 'CRITICAL':
            recommendations.append("Immediate review required - consider escalation")
            recommendations.append("Validate recent transactions with supplier")
            recommendations.append("Request updated documentation")
        
        elif risk_level == 'HIGH':
            recommendations.append("Investigate identified risk factors")
            recommendations.append("Monitor next 10 transactions closely")
            recommendations.append("Schedule supplier review meeting")
        
        elif risk_level == 'MEDIUM':
            recommendations.append("Standard monitoring recommended")
            recommendations.append("Address identified warnings")
        
        else:  # LOW
            recommendations.append("Continue normal monitoring")
            recommendations.append("Consider for trusted supplier program")
        
        # Add specific recommendations based on reasons
        reason_text = " ".join(reasons).lower()
        
        if "aging" in reason_text:
            recommendations.append("Accelerate GR/IR closure process")
        
        if "volatility" in reason_text:
            recommendations.append("Request amount forecasts for next period")
        
        if "anomaly" in reason_text:
            recommendations.append("Request root cause analysis from supplier")
        
        if "inconsistent" in reason_text:
            recommendations.append("Standardize order-to-pay process with supplier")
        
        return recommendations
    
    # =========================================================================
    # BATCH EXPLANATION GENERATION
    # =========================================================================
    
    def generate_supplier_explanations_batch(self, df_suppliers):
        """
        Generate explanations for all suppliers.
        """
        self.log("Generating supplier explanations...")
        
        explanations = []
        
        for idx, row in df_suppliers.iterrows():
            explanation_dict = self.generate_supplier_explanation(row)
            explanations.append(explanation_dict)
        
        # Add to dataframe
        df_explanations = pd.DataFrame(explanations)
        df_result = pd.concat([df_suppliers.reset_index(drop=True), df_explanations], axis=1)
        
        self.log(f"✓ Generated {len(df_result)} supplier explanations")
        
        return df_result
    
    # =========================================================================
    # SUMMARY STATISTICS
    # =========================================================================
    
    def compute_explanation_statistics(self, df_with_explanations):
        """
        Compute statistics on explanations.
        """
        self.log("Computing explanation statistics...")
        
        stats = {
            'total_suppliers': len(df_with_explanations),
            'avg_reasons_per_supplier': df_with_explanations['reason_count'].mean(),
            'avg_warnings_per_supplier': df_with_explanations['warning_count'].mean(),
            'avg_strengths_per_supplier': df_with_explanations['strength_count'].mean(),
            'suppliers_with_no_reasons': (df_with_explanations['reason_count'] == 0).sum(),
            'suppliers_with_multiple_reasons': (df_with_explanations['reason_count'] > 2).sum(),
        }
        
        return stats
    
    # =========================================================================
    # EXPORT FOR DASHBOARD
    # =========================================================================
    
    def prepare_for_dashboard(self, df_with_explanations):
        """
        Prepare supplier data in dashboard-ready format.
        """
        self.log("Preparing for dashboard...")
        
        dashboard_cols = [
            'supplier_id',
            'supplier_risk_score',
            'supplier_risk_level',
            'cluster',
            'cluster_label',
            'cluster_description',
            'behavioral_transaction_frequency',
            'behavioral_anomaly_ratio',
            'temporal_avg_aging_days',
            'financial_amount_volatility_cv',
            'explanation',
        ]
        
        # Keep only available columns
        available_cols = [c for c in dashboard_cols if c in df_with_explanations.columns]
        df_dashboard = df_with_explanations[available_cols].copy()
        
        self.log(f"✓ Dashboard dataset: {len(df_dashboard)} suppliers")
        
        return df_dashboard


# =============================================================================
# TESTING
# =============================================================================

if __name__ == '__main__':
    print("="*80)
    print("PHASE 2 — SUPPLIER EXPLAINABILITY ENGINE")
    print("="*80)
    
    print("\nModules loaded:")
    print("  ✓ SupplierExplainabilityEngine")
    print("\nCapabilities:")
    print("  ✓ Business-readable explanations")
    print("  ✓ Risk factor analysis")
    print("  ✓ Recommendation generation")
    print("  ✓ Dashboard preparation")
