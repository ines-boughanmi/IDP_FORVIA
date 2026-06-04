"""
Risk Scoring Configuration - Phase 1
====================================

Defines all thresholds and weights for transaction and supplier risk scoring.
GOAL: Keep it simple, interpretable, and business-aligned.
"""

# ============================================
# RISK LEVEL THRESHOLDS (Transaction)
# ============================================

TRANSACTION_RISK_THRESHOLDS = {
    'LOW': (0, 25),           # 0-25: Normal, minimal risk
    'MEDIUM': (25, 50),       # 25-50: Moderate attention needed
    'HIGH': (50, 75),         # 50-75: Significant risk, investigate
    'CRITICAL': (75, 100),    # 75-100: Severe risk, escalate
}

# ============================================
# RISK LEVEL THRESHOLDS (Supplier)
# ============================================

SUPPLIER_RISK_THRESHOLDS = {
    'TRUSTED': (0, 25),           # <25: Safe supplier
    'STANDARD': (25, 50),         # 25-50: Normal operations
    'MONITORED': (50, 75),        # 50-75: Enhanced monitoring
    'HIGH_RISK': (75, 100),       # 75-100: Strict controls
}

# ============================================
# RISK SCORE COMPONENT WEIGHTS
# ============================================

TRANSACTION_RISK_WEIGHTS = {
    'ruleengine_signal': 0.40,      # 40% - RuleEngine classification
    'ml_probability': 0.20,          # 20% - ML model confidence
    'amount_anomaly': 0.15,          # 15% - Financial indicators
    'temporal_signal': 0.15,         # 15% - Aging & delays
    'supplier_inherited': 0.10,      # 10% - Supplier context
}

# ============================================
# FINANCIAL RISK INDICATORS
# ============================================

AMOUNT_THRESHOLDS = {
    'gap_pct_low': 2.0,              # < 2% gap = normal
    'gap_pct_medium': 5.0,           # 2-5% = minor
    'gap_pct_high': 10.0,            # 5-10% = moderate
    'gap_pct_critical': 20.0,        # >20% = major
    
    'invoice_ratio_normal_lower': 0.95,  # 0.95-1.05 = normal
    'invoice_ratio_normal_upper': 1.05,
    
    'blocked_amount_pct_threshold': 0.20,  # >20% blocked = risk
}

# ============================================
# TEMPORAL RISK INDICATORS
# ============================================

AGING_THRESHOLDS = {
    'normal_max': 7,              # ≤7 days = recent, no risk
    'acceptable_max': 30,         # 7-30 days = normal processing
    'delayed_max': 60,            # 30-60 days = delayed
    'critical_max': 90,           # 60-90 days = very delayed
    'emergency_max': 180,         # 90-180 days = critical
}

# ============================================
# RULE ENGINE SIGNAL MAPPING
# ============================================

RULEENGINE_SIGNAL_SCORES = {
    'OK': 0,                              # Both GR+IR present = no risk
    'INCOMPLETE': 20,                     # Neither GR nor IR = data issue
    'DELIVERED_NOT_INVOICED': 50,         # GR but no IR = accounting risk
    'INVOICED_NOT_DELIVERED': 100,        # IR but no GR = fraud (currently 0 in data)
}

# ============================================
# SUPPLIER RISK AGGREGATION
# ============================================

SUPPLIER_AGGREGATION = {
    'min_transactions': 5,           # Ignore suppliers with <5 transactions
    'anomaly_rate_warning': 0.10,    # >10% anomalies = concerning
    'anomaly_rate_critical': 0.20,   # >20% anomalies = high risk
    'avg_aging_warning': 30,         # >30 days average aging = concerning
    'avg_aging_critical': 60,        # >60 days = critical
}

# ============================================
# FEATURE COLUMN NAMES
# ============================================

KEY_COLUMNS = {
    'transaction_id': 'po_item',                          # PO+Item key
    'supplier_id': 'supplier_|_lifnr',                    # Supplier
    'gr_amount': 'total_gr_amount',                       # GR total
    'ir_amount': 'total_ir_amount',                       # IR total
    'days_in_system': 'days_in_system',                   # Aging
    'gr_ir_gap_pct': 'gr_ir_gap_pct',                     # % gap
    'blocked_amount': 'blocked_amount',                   # Blocked $
    'anomaly_class': 'anomaly_class',                     # RuleEngine
    'ml_prediction': 'ml_prediction_label',               # ML output
    'ml_confidence': 'ml_prediction_confidence',          # ML probability
    'supplier_anomaly_rate': 'supplier_anomaly_rate',     # Supplier %
}

# ============================================
# EXPLANATION TEMPLATES
# ============================================

EXPLANATION_TEMPLATES = {
    'ok': "Normal transaction with GR and IR present.",
    
    'high_age': "Transaction aging (${days} days). Invoice pending.",
    
    'amount_gap': "Amount gap detected (${gap_pct}% difference between GR and IR).",
    
    'incomplete': "Missing GR or IR. Transaction incomplete.",
    
    'supplier_risk': "Supplier has high anomaly history (${anomaly_rate}% of transactions affected).",
    
    'blocked': "Significant amount blocked (${blocked_pct}% of GR amount).",
    
    'combo_risk': "Multiple risk factors: ${factors}. Requires investigation.",
}

# ============================================
# PRINT CONFIG
# ============================================

if __name__ == "__main__":
    print("=" * 80)
    print("RISK SCORING CONFIGURATION - PHASE 1")
    print("=" * 80)
    print(f"\nTransaction Risk Weights: {TRANSACTION_RISK_WEIGHTS}")
    print(f"\nTransaction Risk Levels: {TRANSACTION_RISK_THRESHOLDS}")
    print(f"\nSupplier Risk Levels: {SUPPLIER_RISK_THRESHOLDS}")
    print(f"\nRuleEngine Signal Scores: {RULEENGINE_SIGNAL_SCORES}")
    print("\nConfiguration loaded successfully ✓")
