#!/usr/bin/env python
"""
PHASE 2: Calibrated Risk Scoring Engine (v2)
==============================================

Key Improvements:
1. Percentile-based normalization instead of fixed thresholds
2. Reduced temporal signal weight (aging was over-dominant)
3. Independent supplier features (frequency, volatility)
4. Better anomaly classification handling
5. Statistical recalibration for realistic distributions
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

# =============================================================================
# CONFIGURATION - RECALIBRATED WEIGHTS AND THRESHOLDS
# =============================================================================

class Phase2Config:
    """Recalibrated configuration for Phase 2"""
    
    # RECALIBRATED WEIGHTS (reduced temporal, increased anomaly/supplier)
    TRANSACTION_WEIGHTS = {
        'ruleengine_signal': 0.20,      # REDUCED from 0.40 (was dominant with NONE=0)
        'anomaly_classification': 0.25, # NEW: Direct anomaly weight
        'ml_probability': 0.15,         # REDUCED from 0.20
        'amount_anomaly': 0.15,         # SAME
        'temporal_signal': 0.10,        # REDUCED from 0.15 (was over-dominant)
        'supplier_frequency': 0.10,     # NEW: Independent supplier metric
        'supplier_volatility': 0.05     # NEW: Amount volatility
    }
    
    # RECALIBRATED TEMPORAL THRESHOLDS (less aggressive)
    TEMPORAL_THRESHOLDS = {
        'critical': 365,  # > 1 year
        'high': 180,      # 6-12 months
        'medium': 90,     # 3-6 months
        'low': 30,        # < 3 months
    }
    
    # ANOMALY SCORES (direct mapping)
    ANOMALY_SCORES = {
        'NONE': 20,                  # Normal but may have aging issues
        'DATA': 35,                  # Data quality issue (moderate)
        'ACCOUNTING': 60,            # Accounting mismatch (higher)
        'FRAUD': 100,                # Fraud flag (critical)
    }
    
    # SUPPLIER RISK THRESHOLDS (independent from transaction)
    SUPPLIER_THRESHOLDS = {
        'HIGH_VOLATILITY': 0.40,     # Std dev > 40% of mean
        'SLOW_SUPPLIER': 600,        # Avg days > 600
        'LOW_FREQUENCY': 10,         # Avg transactions per month < 10
    }
    
    # DISTRIBUTION TARGETS
    TARGET_DISTRIBUTION = {
        'LOW': {'min': 0, 'max': 25, 'target_pct': 35},
        'MEDIUM': {'min': 25, 'max': 50, 'target_pct': 30},
        'HIGH': {'min': 50, 'max': 75, 'target_pct': 20},
        'CRITICAL': {'min': 75, 'max': 100, 'target_pct': 15},
    }


# =============================================================================
# PHASE 2 SCORING ENGINE
# =============================================================================

class Phase2TransactionRiskScorer:
    """
    Recalibrated transaction risk scorer with:
    - Better weight distribution
    - Anomaly classification integration
    - Percentile normalization support
    """
    
    def __init__(self, verbose=False):
        self.config = Phase2Config()
        self.verbose = verbose
        self.transaction_scores = None
        
    def log(self, msg):
        if self.verbose:
            print(f"  {msg}")
    
    # =========================================================================
    # COMPONENT SCORERS
    # =========================================================================
    
    def score_anomaly_classification(self, df):
        """
        Score based on anomaly classification directly.
        Maps DATA < ACCOUNTING < FRAUD scale
        """
        self.log("Computing anomaly classification score...")
        
        scores = df['anomaly_class'].map(self.config.ANOMALY_SCORES).fillna(20)
        
        return scores.values
    
    def score_ruleengine_signal(self, df):
        """
        Score based on RuleEngine classification.
        Reduced weight since most = NONE (which should be low risk)
        """
        self.log("Computing RuleEngine signal score...")
        
        # Map: OK=0, INCOMPLETE=30, DELIVERED_NOT_INVOICED=60, INVOICED_NOT_DELIVERED=80
        mapping = {
            'OK': 0,
            'INCOMPLETE': 30,
            'DELIVERED_NOT_INVOICED': 60,
            'INVOICED_NOT_DELIVERED': 80,
            'NONE': 0  # Default for missing
        }
        
        scores = df['anomaly_class'].map(mapping).fillna(0)
        return scores.values
    
    def score_ml_probability(self, df):
        """
        Score based on ML prediction confidence.
        Inverted: high confidence = low risk
        """
        self.log("Computing ML probability score...")
        
        if 'ml_prediction_confidence' in df.columns:
            confidence = df['ml_prediction_confidence'].fillna(0.7)
        else:
            confidence = np.full(len(df), 0.7)
        
        # Invert confidence to risk: 1.0 conf → 0 risk, 0.0 conf → 100 risk
        if isinstance(confidence, (pd.Series, np.ndarray)):
            scores = (1.0 - np.asarray(confidence)) * 100
        else:
            scores = (1.0 - confidence) * 100
        
        return np.clip(scores, 0, 100)
    
    def score_amount_anomaly(self, df):
        """
        Score based on amount discrepancies.
        Uses GR/IR gap, invoice ratio, blocked amount
        """
        self.log("Computing amount anomaly score...")
        
        scores = np.zeros(len(df))
        
        # Gap percentage (50% weight)
        if 'gr_ir_gap_pct' in df.columns:
            gap_scores = (df['gr_ir_gap_pct'].fillna(0).clip(0, 100)) * 0.50
        else:
            gap_scores = 0
        
        # Invoice ratio (30% weight)
        if 'invoice_ratio' in df.columns:
            # Low invoice ratio = high risk
            invoice_scores = (1.0 - df['invoice_ratio'].fillna(0.5).clip(0, 1)) * 100 * 0.30
        else:
            invoice_scores = 0
        
        # Blocked amount (20% weight)
        if 'blocked_amount' in df.columns:
            if 'gr_amount' in df.columns:
                gr = df['gr_amount'].fillna(0)
            elif 'total_gr_amount' in df.columns:
                gr = df['total_gr_amount'].fillna(0)
            else:
                gr = 1  # Avoid division by zero
            
            blocked_pct = (df['blocked_amount'].fillna(0) / (gr + 0.01)).clip(0, 1)
            blocked_scores = blocked_pct * 100 * 0.20
        else:
            blocked_scores = 0
        
        scores = (gap_scores + invoice_scores + blocked_scores).clip(0, 100)
        
        return scores
    
    def score_temporal_signal(self, df):
        """
        Score based on transaction aging.
        RECALIBRATED: Less aggressive than Phase 1
        """
        self.log("Computing temporal signal score...")
        
        if 'days_in_system' not in df.columns:
            return np.zeros(len(df))
        
        days = df['days_in_system'].fillna(0)
        scores = np.zeros(len(df))
        
        # Recalibrated aging curve (more gradual)
        scores[days <= 30] = 5
        scores[(days > 30) & (days <= 90)] = 15
        scores[(days > 90) & (days <= 180)] = 35
        scores[(days > 180) & (days <= 365)] = 65
        scores[days > 365] = 95
        
        return scores.clip(0, 100)
    
    def score_supplier_frequency(self, df, supplier_txn_map):
        """
        Score based on supplier transaction frequency.
        Low frequency suppliers = higher risk (less predictable)
        """
        self.log("Computing supplier frequency score...")
        
        if 'supplier_|_lifnr_first' in df.columns:
            supplier_col = 'supplier_|_lifnr_first'
        elif 'supplier_id' in df.columns:
            supplier_col = 'supplier_id'
        else:
            return np.zeros(len(df))
        
        # Map suppliers to frequency scores
        frequency_scores = df[supplier_col].map(supplier_txn_map).fillna(50)
        
        return frequency_scores.values.clip(0, 100)
    
    def score_supplier_volatility(self, df, supplier_volatility_map):
        """
        Score based on supplier amount volatility.
        High volatility suppliers = higher risk
        """
        self.log("Computing supplier volatility score...")
        
        if 'supplier_|_lifnr_first' in df.columns:
            supplier_col = 'supplier_|_lifnr_first'
        elif 'supplier_id' in df.columns:
            supplier_col = 'supplier_id'
        else:
            return np.zeros(len(df))
        
        volatility_scores = df[supplier_col].map(supplier_volatility_map).fillna(30)
        
        return volatility_scores.values.clip(0, 100)
    
    # =========================================================================
    # MAIN SCORING
    # =========================================================================
    
    def compute_transaction_scores(self, df, supplier_stats=None):
        """
        Compute weighted transaction risk scores using recalibrated formula.
        
        Formula:
        Score = 0.20*RuleEngine + 0.25*Anomaly + 0.15*ML + 0.15*Amount 
               + 0.10*Temporal + 0.10*Frequency + 0.05*Volatility
        """
        self.log("Computing transaction risk scores (Phase 2)...")
        
        df_scored = df.copy()
        
        # Compute component scores
        s_ruleengine = self.score_ruleengine_signal(df_scored)
        s_anomaly = self.score_anomaly_classification(df_scored)
        s_ml = self.score_ml_probability(df_scored)
        s_amount = self.score_amount_anomaly(df_scored)
        s_temporal = self.score_temporal_signal(df_scored)
        
        # Supplier-based scores (require pre-computed maps)
        if supplier_stats is not None:
            s_frequency = self.score_supplier_frequency(df_scored, supplier_stats['frequency_map'])
            s_volatility = self.score_supplier_volatility(df_scored, supplier_stats['volatility_map'])
        else:
            s_frequency = np.zeros(len(df_scored))
            s_volatility = np.zeros(len(df_scored))
        
        # Weighted combination with recalibrated weights
        df_scored['risk_score_transaction_v2'] = (
            self.config.TRANSACTION_WEIGHTS['ruleengine_signal'] * s_ruleengine +
            self.config.TRANSACTION_WEIGHTS['anomaly_classification'] * s_anomaly +
            self.config.TRANSACTION_WEIGHTS['ml_probability'] * s_ml +
            self.config.TRANSACTION_WEIGHTS['amount_anomaly'] * s_amount +
            self.config.TRANSACTION_WEIGHTS['temporal_signal'] * s_temporal +
            self.config.TRANSACTION_WEIGHTS['supplier_frequency'] * s_frequency +
            self.config.TRANSACTION_WEIGHTS['supplier_volatility'] * s_volatility
        ).clip(0, 100)
        
        self.transaction_scores = df_scored['risk_score_transaction_v2'].copy()
        
        self.log(f"Computed scores for {len(df_scored)} transactions")
        self.log(f"  Mean: {df_scored['risk_score_transaction_v2'].mean():.2f}")
        self.log(f"  Std: {df_scored['risk_score_transaction_v2'].std():.2f}")
        
        return df_scored


class Phase2SupplierRiskScorer:
    """
    Independent supplier risk scorer.
    NOT derived from transaction risk, but from supplier behavior.
    """
    
    def __init__(self, verbose=False):
        self.config = Phase2Config()
        self.verbose = verbose
    
    def log(self, msg):
        if self.verbose:
            print(f"  {msg}")
    
    def compute_supplier_stats(self, df):
        """
        Compute independent supplier risk metrics.
        Returns maps for frequency and volatility scoring.
        """
        self.log("Computing supplier statistics...")
        
        # Determine supplier column
        if 'supplier_|_lifnr_first' in df.columns:
            supplier_col = 'supplier_|_lifnr_first'
        elif 'supplier_id' in df.columns:
            supplier_col = 'supplier_id'
        else:
            return None
        
        supplier_agg = df.groupby(supplier_col).agg({
            'gr_amount' if 'gr_amount' in df.columns else 'total_gr_amount': ['mean', 'std'],
            'transaction_id' if 'transaction_id' in df.columns else df.columns[0]: 'count',
            'days_in_system': 'mean' if 'days_in_system' in df.columns else lambda x: 0,
        }).reset_index()
        
        supplier_agg.columns = ['supplier_id', 'avg_amount', 'std_amount', 'txn_count', 'avg_aging']
        
        # Calculate metrics
        supplier_agg['frequency_score'] = self._calc_frequency_risk(supplier_agg)
        supplier_agg['volatility_score'] = self._calc_volatility_risk(supplier_agg)
        supplier_agg['aging_score'] = self._calc_aging_risk(supplier_agg)
        
        # Create maps
        frequency_map = dict(zip(supplier_agg['supplier_id'], supplier_agg['frequency_score']))
        volatility_map = dict(zip(supplier_agg['supplier_id'], supplier_agg['volatility_score']))
        
        return {
            'frequency_map': frequency_map,
            'volatility_map': volatility_map,
            'supplier_agg': supplier_agg
        }
    
    def _calc_frequency_risk(self, df):
        """
        Risk score based on transaction frequency.
        Low frequency (unpredictable) = higher risk
        """
        # Monthly equivalent
        monthly_freq = df['txn_count'] / 12  # Assume 1 year of data
        
        scores = np.zeros(len(df))
        scores[monthly_freq > 100] = 10   # Very frequent = low risk
        scores[(monthly_freq >= 50) & (monthly_freq <= 100)] = 25
        scores[(monthly_freq >= 20) & (monthly_freq < 50)] = 50
        scores[(monthly_freq >= 5) & (monthly_freq < 20)] = 70
        scores[monthly_freq < 5] = 90   # Very rare = high risk
        
        return scores
    
    def _calc_volatility_risk(self, df):
        """
        Risk score based on amount volatility.
        High coefficient of variation = higher risk
        """
        # Coefficient of variation: std / mean
        df_copy = df.fillna(0)
        cv = df_copy['std_amount'] / (df_copy['avg_amount'] + 0.01)
        
        scores = np.zeros(len(df))
        scores[cv < 0.2] = 10    # Low volatility = low risk
        scores[(cv >= 0.2) & (cv < 0.5)] = 30
        scores[(cv >= 0.5) & (cv < 1.0)] = 60
        scores[cv >= 1.0] = 80   # High volatility = high risk
        
        return scores
    
    def _calc_aging_risk(self, df):
        """
        Risk score based on average transaction aging.
        """
        scores = np.zeros(len(df))
        scores[df['avg_aging'] <= 90] = 10
        scores[(df['avg_aging'] > 90) & (df['avg_aging'] <= 180)] = 30
        scores[(df['avg_aging'] > 180) & (df['avg_aging'] <= 365)] = 60
        scores[df['avg_aging'] > 365] = 90
        
        return scores


class Phase2RiskNormalizer:
    """
    Normalize risk scores to achieve target distributions.
    Uses percentile-based mapping instead of fixed thresholds.
    """
    
    def __init__(self, verbose=False):
        self.verbose = verbose
    
    def log(self, msg):
        if self.verbose:
            print(f"  {msg}")
    
    def normalize_transaction_scores(self, scores):
        """
        Map raw scores to percentile-based risk levels.
        Target: LOW 35%, MEDIUM 30%, HIGH 20%, CRITICAL 15%
        """
        self.log("Normalizing transaction scores with percentile mapping...")
        
        # Calculate percentile thresholds
        p_low = np.percentile(scores, 35)      # TOP 65% are not LOW
        p_medium = np.percentile(scores, 65)   # TOP 35% are MEDIUM+
        p_high = np.percentile(scores, 85)     # TOP 15% are HIGH+
        
        self.log(f"  Percentile thresholds: LOW≤{p_low:.1f}, MEDIUM≤{p_medium:.1f}, HIGH≤{p_high:.1f}")
        
        levels = np.zeros(len(scores), dtype=object)
        levels[scores <= p_low] = 'LOW'
        levels[(scores > p_low) & (scores <= p_medium)] = 'MEDIUM'
        levels[(scores > p_medium) & (scores <= p_high)] = 'HIGH'
        levels[scores > p_high] = 'CRITICAL'
        
        return levels, {
            'low_threshold': p_low,
            'medium_threshold': p_medium,
            'high_threshold': p_high
        }


# =============================================================================
# TESTING/VALIDATION
# =============================================================================

if __name__ == '__main__':
    print("Phase 2: Recalibrated Scoring Engine Loaded")
    print(f"Recalibrated Weights: {Phase2Config.TRANSACTION_WEIGHTS}")
    print(f"\nTarget Distribution:")
    for level, target in Phase2Config.TARGET_DISTRIBUTION.items():
        print(f"  {level}: {target['target_pct']}%")
