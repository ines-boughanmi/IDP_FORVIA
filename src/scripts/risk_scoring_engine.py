"""
Risk Scoring Engine - Phase 1
=============================

Simple, interpretable transaction and supplier risk scoring.
NO SHAP, NO ML RETRAINING - just deterministic scoring.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

from risk_thresholds_config import (
    TRANSACTION_RISK_WEIGHTS,
    TRANSACTION_RISK_THRESHOLDS,
    SUPPLIER_RISK_THRESHOLDS,
    AMOUNT_THRESHOLDS,
    AGING_THRESHOLDS,
    RULEENGINE_SIGNAL_SCORES,
    SUPPLIER_AGGREGATION,
    EXPLANATION_TEMPLATES,
    KEY_COLUMNS,
)


class TransactionRiskScorer:
    """
    Compute transaction-level risk scores (0-100).
    Simple, interpretable, business-aligned.
    """
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.risk_scores = None
        self.component_scores = None
    
    
    def log(self, msg):
        if self.verbose:
            print(f"  📊 {msg}")
    
    
    def score_ruleengine_signal(self, df):
        """
        Score based on RuleEngine classification.
        
        Returns: 0-100 score
        - OK = 0 (no risk)
        - INCOMPLETE = 20 (data issue)
        - DELIVERED_NOT_INVOICED = 50 (accounting risk)
        - INVOICED_NOT_DELIVERED = 100 (fraud risk)
        """
        self.log("Computing RuleEngine signal score...")
        
        score = df['anomaly_class'].map(RULEENGINE_SIGNAL_SCORES).fillna(50)
        
        return score.clip(0, 100)
    
    
    def score_ml_probability(self, df):
        """
        Score based on ML model confidence.
        
        Higher confidence (closer to 1.0) in any prediction = lower risk
        (model is certain) vs low confidence = higher risk
        (model uncertain about what class this is)
        """
        self.log("Computing ML probability score...")
        
        # Check if confidence column exists, if not use default
        if 'ml_prediction_confidence' in df.columns:
            confidence = df['ml_prediction_confidence'].fillna(0.7)
        else:
            # Default: 0.7 confidence for all (moderate)
            self.log("  ⚠️  ml_prediction_confidence not found, using default 0.7")
            confidence = pd.Series(0.7, index=df.index)
        
        # Invert: 1.0 confidence = 0 risk, 0.0 confidence = 100 risk
        score = (1.0 - confidence) * 100
        
        return score.clip(0, 100)
    
    
    def score_amount_anomaly(self, df):
        """
        Score based on financial indicators.
        
        Combines:
        - GR/IR gap percentage
        - Invoice ratio deviation
        - Blocked amount percentage
        """
        self.log("Computing amount anomaly score...")
        
        # 1. GAP PERCENTAGE SCORE
        gap_pct = df['gr_ir_gap_pct'].fillna(0)
        
        gap_score = np.where(
            gap_pct < AMOUNT_THRESHOLDS['gap_pct_low'], 0,
            np.where(gap_pct < AMOUNT_THRESHOLDS['gap_pct_medium'], 25,
            np.where(gap_pct < AMOUNT_THRESHOLDS['gap_pct_high'], 50,
            np.where(gap_pct < AMOUNT_THRESHOLDS['gap_pct_critical'], 75, 100)))
        )
        
        # 2. INVOICE RATIO SCORE
        if 'invoice_ratio' in df.columns:
            ratio = df['invoice_ratio'].fillna(1.0)
        else:
            # If not available, create from GR and IR amounts
            gr_amt = df['total_gr_amount'].fillna(0)
            ir_amt = df['total_ir_amount'].fillna(0)
            ratio = np.where(gr_amt > 0, ir_amt / gr_amt, 1.0)
        
        ratio_lower = AMOUNT_THRESHOLDS['invoice_ratio_normal_lower']
        ratio_upper = AMOUNT_THRESHOLDS['invoice_ratio_normal_upper']
        
        ratio_score = np.where(
            (ratio >= ratio_lower) & (ratio <= ratio_upper), 0,  # Normal
            np.where(
                ((ratio >= 0.90) & (ratio < ratio_lower)) |
                ((ratio > ratio_upper) & (ratio <= 1.10)), 25,  # Minor
                np.where(
                    ((ratio >= 0.80) & (ratio < 0.90)) |
                    ((ratio > 1.10) & (ratio <= 1.20)), 50,  # Moderate
                    75  # Significant deviation
                )
            )
        )
        
        # 3. BLOCKED AMOUNT SCORE
        gr_amt = df['total_gr_amount'].fillna(0)
        if 'blocked_amount' in df.columns:
            blocked_amt = df['blocked_amount'].fillna(0)
        else:
            blocked_amt = np.where(
                gr_amt > df['total_ir_amount'].fillna(0),
                gr_amt - df['total_ir_amount'].fillna(0),
                0
            )
        
        blocked_pct = np.where(
            gr_amt > 0, blocked_amt / gr_amt, 0
        )
        
        blocked_score = np.where(
            blocked_pct == 0, 0,
            np.where(blocked_pct < 0.05, 10,
            np.where(blocked_pct < 0.20, 40,
            np.where(blocked_pct < 0.50, 70, 90)))
        )
        
        # COMBINED SCORE
        combined_score = (gap_score * 0.5) + (ratio_score * 0.3) + (blocked_score * 0.2)
        
        return combined_score.clip(0, 100)
    
    
    def score_temporal_signal(self, df):
        """
        Score based on aging and temporal patterns.
        
        Older transactions = higher risk (blocked longer)
        Recent transactions = lower risk
        """
        self.log("Computing temporal signal score...")
        
        days = df['days_in_system'].fillna(0)
        
        score = np.where(
            days <= AGING_THRESHOLDS['normal_max'], 0,
            np.where(days <= AGING_THRESHOLDS['acceptable_max'], 15,
            np.where(days <= AGING_THRESHOLDS['delayed_max'], 40,
            np.where(days <= AGING_THRESHOLDS['critical_max'], 65,
            np.where(days <= AGING_THRESHOLDS['emergency_max'], 80, 100))))
        )
        
        return score.clip(0, 100)
    
    
    def score_supplier_inherited(self, supplier_risks):
        """
        Inherit supplier risk score to individual transactions.
        
        Args:
            supplier_risks: dict of {supplier_id: risk_score}
        """
        self.log("Computing supplier inherited score...")
        
        # Will be filled after supplier scoring is complete
        return pd.Series(0.0)  # Placeholder
    
    
    def compute_transaction_scores(self, df, supplier_risks=None):
        """
        Compute complete transaction risk scores.
        
        Args:
            df: DataFrame with all features
            supplier_risks: dict of {supplier_id: risk_score} for inheritance
            
        Returns:
            DataFrame with risk scores added
        """
        self.log("Computing transaction risk scores...")
        
        df_scored = df.copy()
        
        # Compute components
        components = {}
        components['ruleengine_signal'] = self.score_ruleengine_signal(df)
        components['ml_probability'] = self.score_ml_probability(df)
        components['amount_anomaly'] = self.score_amount_anomaly(df)
        components['temporal_signal'] = self.score_temporal_signal(df)
        
        # Supplier inherited risk
        if supplier_risks:
            supplier_col = KEY_COLUMNS['supplier_id']
            components['supplier_inherited'] = df[supplier_col].map(
                lambda x: supplier_risks.get(x, 25)  # Default to 25 if unknown
            ).fillna(25)
        else:
            components['supplier_inherited'] = pd.Series(25.0, index=df.index)
        
        # Store components for analysis
        self.component_scores = pd.DataFrame(components)
        
        # Weighted combination
        weights = TRANSACTION_RISK_WEIGHTS
        
        total_weight = sum(weights.values())
        weighted_sum = sum(
            components[key] * weights[key] / total_weight
            for key in components.keys()
        )
        
        df_scored['risk_score_transaction'] = weighted_sum.clip(0, 100)
        
        # Assign risk level
        df_scored['risk_level_transaction'] = self._assign_risk_level(
            df_scored['risk_score_transaction']
        )
        
        self.risk_scores = df_scored[['risk_score_transaction', 'risk_level_transaction']]
        
        self.log(f"✓ Computed scores for {len(df_scored)} transactions")
        
        return df_scored
    
    
    def _assign_risk_level(self, scores):
        """Map 0-100 score to risk level."""
        levels = []
        for score in scores:
            if score < 25:
                levels.append('LOW')
            elif score < 50:
                levels.append('MEDIUM')
            elif score < 75:
                levels.append('HIGH')
            else:
                levels.append('CRITICAL')
        return pd.Series(levels, index=scores.index)


class SupplierRiskScorer:
    """
    Compute supplier-level risk scores by aggregating transactions.
    """
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.supplier_scores = None
    
    
    def log(self, msg):
        if self.verbose:
            print(f"  🏭 {msg}")
    
    
    def compute_supplier_scores(self, df):
        """
        Aggregate transaction scores to supplier level.
        
        Args:
            df: DataFrame with transaction risk scores
            
        Returns:
            DataFrame with supplier risk scores
        """
        self.log("Computing supplier risk scores...")
        
        supplier_col = KEY_COLUMNS['supplier_id']
        
        # Check if supplier column exists
        if supplier_col not in df.columns:
            self.log(f"  WARNING Supplier column '{supplier_col}' not found!")
            self.log("  Creating dummy supplier column for aggregation...")
            df = df.copy()
            df[supplier_col] = 'UNKNOWN_SUPPLIER'
        
        # Group by supplier
        supplier_agg = df.groupby(supplier_col).agg({
            'risk_score_transaction': ['mean', 'std', 'min', 'max', 'count'],
            'days_in_system': 'mean',
            'gr_ir_gap_pct': 'mean',
            'anomaly_class': lambda x: (x != 'OK').sum() / len(x) if len(x) > 0 else 0,  # % anomalies
        }).reset_index()
        
        supplier_agg.columns = ['supplier_id', 
                                'avg_transaction_risk', 'std_transaction_risk',
                                'min_transaction_risk', 'max_transaction_risk',
                                'transaction_count',
                                'avg_days_in_system', 'avg_gap_pct',
                                'anomaly_rate']
        
        # Filter out very small suppliers
        min_txn = SUPPLIER_AGGREGATION['min_transactions']
        supplier_agg = supplier_agg[supplier_agg['transaction_count'] >= min_txn].copy()
        
        self.log(f"Analyzing {len(supplier_agg)} suppliers (min {min_txn} transactions)")
        
        # Compute supplier risk score (simple weighted average)
        supplier_agg['risk_score_supplier'] = (
            (supplier_agg['avg_transaction_risk'] * 0.50) +    # 50% avg txn risk
            (supplier_agg['anomaly_rate'] * 100 * 0.30) +      # 30% anomaly rate
            (supplier_agg['avg_days_in_system'] / 180 * 100 * 0.20)  # 20% aging
        ).clip(0, 100)
        
        # Assign supplier risk level
        supplier_agg['risk_level_supplier'] = supplier_agg['risk_score_supplier'].apply(
            self._assign_supplier_level
        )
        
        self.supplier_scores = supplier_agg
        
        self.log(f"OK Computed scores for {len(supplier_agg)} suppliers")
        
        return supplier_agg
    
    
    def _assign_supplier_level(self, score):
        """Map score to supplier risk level."""
        if score < 25:
            return 'TRUSTED'
        elif score < 50:
            return 'STANDARD'
        elif score < 75:
            return 'MONITORED'
        else:
            return 'HIGH_RISK'


class RiskExplainer:
    """
    Generate simple, human-readable explanations for risk scores.
    """
    
    def __init__(self, verbose=True):
        self.verbose = verbose
    
    
    def log(self, msg):
        if self.verbose:
            print(f"  💭 {msg}")
    
    
    def generate_explanations(self, df):
        """
        Generate simple text explanations for each transaction.
        
        Args:
            df: DataFrame with risk scores and components
            
        Returns:
            Series with explanations
        """
        self.log("Generating explanations...")
        
        explanations = []
        
        for idx, row in df.iterrows():
            explanation = self._explain_transaction(row)
            explanations.append(explanation)
        
        return pd.Series(explanations, index=df.index)
    
    
    def _explain_transaction(self, row):
        """Generate explanation for a single transaction."""
        factors = []
        
        # Check aging
        days = row.get('days_in_system', 0)
        if days > 60:
            factors.append(f"aging ({int(days)} days)")
        
        # Check amount gap
        gap_pct = row.get('gr_ir_gap_pct', 0)
        if gap_pct > 10:
            factors.append(f"amount gap ({gap_pct:.1f}%)")
        
        # Check GR/IR status
        anomaly_class = row.get('anomaly_class', 'OK')
        if anomaly_class == 'INCOMPLETE':
            factors.append("incomplete transaction")
        elif anomaly_class == 'DELIVERED_NOT_INVOICED':
            factors.append("goods received, invoice pending")
        elif anomaly_class == 'INVOICED_NOT_DELIVERED':
            factors.append("invoice received, goods pending")
        
        # Check supplier history
        supplier_anomaly_rate = row.get('supplier_anomaly_rate', 0)
        if supplier_anomaly_rate > 0.15:
            factors.append(f"supplier risk ({supplier_anomaly_rate:.0%} anomalies)")
        
        # Build explanation
        if not factors:
            return "Normal transaction with no risk indicators."
        elif len(factors) == 1:
            return f"Risk due to {factors[0]}."
        else:
            return f"Multiple risk factors: {', '.join(factors)}."


def print_statistics(df_transactions, df_suppliers):
    """Print summary statistics."""
    print("\n" + "=" * 80)
    print("RISK SCORING SUMMARY")
    print("=" * 80)
    
    # Transaction stats
    print("\n📊 TRANSACTION RISK DISTRIBUTION:")
    txn_dist = df_transactions['risk_level_transaction'].value_counts()
    for level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
        count = txn_dist.get(level, 0)
        pct = (count / len(df_transactions)) * 100
        print(f"  {level:10s}: {count:8,} ({pct:5.2f}%)")
    
    print(f"\n  Transaction Risk Score Statistics:")
    print(f"    Mean:   {df_transactions['risk_score_transaction'].mean():.2f}")
    print(f"    Median: {df_transactions['risk_score_transaction'].median():.2f}")
    print(f"    Std:    {df_transactions['risk_score_transaction'].std():.2f}")
    print(f"    Min:    {df_transactions['risk_score_transaction'].min():.2f}")
    print(f"    Max:    {df_transactions['risk_score_transaction'].max():.2f}")
    
    # Supplier stats
    print("\n\n🏭 SUPPLIER RISK DISTRIBUTION:")
    supp_dist = df_suppliers['risk_level_supplier'].value_counts()
    for level in ['TRUSTED', 'STANDARD', 'MONITORED', 'HIGH_RISK']:
        count = supp_dist.get(level, 0)
        pct = (count / len(df_suppliers)) * 100
        print(f"  {level:10s}: {count:5,} ({pct:5.2f}%)")
    
    print(f"\n  Supplier Risk Score Statistics:")
    print(f"    Mean:   {df_suppliers['risk_score_supplier'].mean():.2f}")
    print(f"    Median: {df_suppliers['risk_score_supplier'].median():.2f}")
    print(f"    Std:    {df_suppliers['risk_score_supplier'].std():.2f}")
    print(f"    Min:    {df_suppliers['risk_score_supplier'].min():.2f}")
    print(f"    Max:    {df_suppliers['risk_score_supplier'].max():.2f}")
    
    # Top risky suppliers
    print("\n\n⚠️  TOP 10 RISKIEST SUPPLIERS:")
    top_risky = df_suppliers.nlargest(10, 'risk_score_supplier')[
        ['supplier_id', 'risk_score_supplier', 'risk_level_supplier', 
         'transaction_count', 'anomaly_rate']
    ]
    print(top_risky.to_string(index=False))
    
    print("\n" + "=" * 80)
