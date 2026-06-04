#!/usr/bin/env python
"""
Phase 1 Execution: Risk Scoring Engine
=======================================

Loads data, computes risk scores, generates two datasets:
1. p2p_ml_dataset: Rich dataset for analysis
2. p2p_monitoring_dataset: Clean dataset for production/dashboard

IMPORTANT: This does NOT retrain ML models, just scores transactions.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import warnings
warnings.filterwarnings('ignore')

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    PROCESSED_DATA_DIR, RISK_SCORES_DIR, OUTPUTS_DIR,
    ML_FEATURES_X_FILE, ML_FEATURES_Y_FILE, LABELED_DATA_FILE
)
from risk_scoring_engine import (
    TransactionRiskScorer, SupplierRiskScorer, RiskExplainer,
    print_statistics
)

print("=" * 80)
print("PHASE 1: RISK SCORING ENGINE - EXECUTION")
print("=" * 80)

# ============================================================================
# STEP 1: LOAD DATA
# ============================================================================
print("\n[STEP 1] LOADING DATA")
print("-" * 80)

try:
    print("Loading features (ml_features_phase2_X.csv)...")
    X = pd.read_csv(ML_FEATURES_X_FILE)
    print(f"  ✓ Shape: {X.shape}")
    
    print("Loading labels (ml_features_phase2_y.csv)...")
    y = pd.read_csv(ML_FEATURES_Y_FILE, header=None)
    y.columns = ['anomaly_class']
    print(f"  ✓ Shape: {y.shape}")
    
    # Merge
    df = pd.concat([X, y], axis=1)
    print(f"\n✓ Merged dataset: {df.shape}")
    
except Exception as e:
    print(f"❌ Error loading data: {e}")
    sys.exit(1)


# ============================================================================
# STEP 2: LOAD FULL LABELED DATA (for RuleEngine outputs)
# ============================================================================
print("\n[STEP 2] LOADING FULL LABELED DATA")
print("-" * 80)

try:
    print("Loading labeled data (with RuleEngine classifications)...")
    df_labeled = pd.read_csv(LABELED_DATA_FILE)
    print(f"  ✓ Shape: {df_labeled.shape}")
    
    # Extract additional columns we need
    columns_needed = ['po_item', 'supplier_|_lifnr', 'anomaly_class', 'anomaly_type',
                      'total_gr_amount', 'total_ir_amount', 'gr_ir_difference',
                      'gr_ir_gap_pct', 'blocked_amount', 'days_in_system',
                      'supplier_anomaly_rate', 'invoice_ratio']
    
    available_cols = [col for col in columns_needed if col in df_labeled.columns]
    missing_cols = [col for col in columns_needed if col not in df_labeled.columns]
    
    if missing_cols:
        print(f"  ⚠️  Missing columns: {missing_cols}")
    
    # Merge labeled data into our dataset
    df_full = df.copy()
    for col in available_cols:
        if col not in df_full.columns:
            df_full[col] = df_labeled[col]
    
    print(f"\n✓ Enriched dataset: {df_full.shape}")
    
except Exception as e:
    print(f"⚠️  Could not load labeled data: {e}")
    print("  Proceeding with feature data only...")
    df_full = df.copy()


# ============================================================================
# STEP 3: COMPUTE TRANSACTION RISK SCORES
# ============================================================================
print("\n[STEP 3] COMPUTING TRANSACTION RISK SCORES")
print("-" * 80)

try:
    # Initialize scorer
    txn_scorer = TransactionRiskScorer(verbose=True)
    
    # Compute scores (supplier_risks will be added in next step)
    df_scored = txn_scorer.compute_transaction_scores(df_full)
    
    print(f"\n✓ Transaction scores computed for {len(df_scored)} transactions")
    
except Exception as e:
    print(f"❌ Error computing transaction scores: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


# ============================================================================
# STEP 4: COMPUTE SUPPLIER RISK SCORES
# ============================================================================
print("\n\n[STEP 4] COMPUTING SUPPLIER RISK SCORES")
print("-" * 80)

try:
    supp_scorer = SupplierRiskScorer(verbose=True)
    df_suppliers = supp_scorer.compute_supplier_scores(df_scored)
    
    # Create dict for inheritance back to transactions
    supplier_risks = dict(zip(df_suppliers['supplier_id'], 
                              df_suppliers['risk_score_supplier']))
    supplier_levels = dict(zip(df_suppliers['supplier_id'], 
                               df_suppliers['risk_level_supplier']))
    
    # Determine supplier column (try different variations)
    supplier_col = None
    for col in ['supplier_|_lifnr', 'supplier_|_lifnr_first']:
        if col in df_scored.columns:
            supplier_col = col
            break
    
    if supplier_col is None:
        print("WARNING: No supplier column found, using default values")
        df_scored['risk_score_supplier'] = 25
        df_scored['risk_level_supplier'] = 'STANDARD'
    else:
        # Re-score transactions with supplier risk inherited
        df_scored['risk_score_supplier'] = df_scored[supplier_col].map(
            supplier_risks
        ).fillna(25)
        df_scored['risk_level_supplier'] = df_scored[supplier_col].map(
            supplier_levels
        ).fillna('STANDARD')
    
    print(f"✓ Supplier scores computed for {len(df_suppliers)} suppliers")
    
except Exception as e:
    print(f"❌ Error computing supplier scores: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


# ============================================================================
# STEP 5: GENERATE EXPLANATIONS
# ============================================================================
print("\n\n[STEP 5] GENERATING EXPLANATIONS")
print("-" * 80)

try:
    explainer = RiskExplainer(verbose=True)
    df_scored['risk_explanation'] = explainer.generate_explanations(df_scored)
    
    print(f"✓ Explanations generated for {len(df_scored)} transactions")
    
except Exception as e:
    print(f"❌ Error generating explanations: {e}")
    import traceback
    traceback.print_exc()
    df_scored['risk_explanation'] = "Unable to generate explanation"


# ============================================================================
# STEP 6: PRINT STATISTICS
# ============================================================================
print("\n")
print_statistics(df_scored, df_suppliers)


# ============================================================================
# STEP 7: CREATE TWO DATASETS
# ============================================================================
print("\n\n[STEP 6] CREATING OUTPUT DATASETS")
print("-" * 80)

# Dataset 1: ML Dataset (Rich, for analysis)
print("\nCreating ML Dataset (Rich, for analysis)...")

df_ml = df_scored.copy()

ml_columns = [
    'po_item', 'supplier_|_lifnr',
    'total_gr_amount', 'total_ir_amount', 'gr_ir_difference', 
    'abs_gr_ir_diff', 'invoice_ratio', 'gr_ir_gap_pct', 'blocked_amount',
    'days_in_system', 'posting_month', 'posting_quarter',
    'supplier_transaction_count', 'supplier_total_spend', 'supplier_anomaly_rate',
    'anomaly_class', 'anomaly_type',
    'ml_prediction_label', 'ml_prediction_confidence',
    'risk_score_transaction', 'risk_level_transaction',
    'risk_score_supplier', 'risk_explanation'
]

# Only include columns that exist
ml_columns_available = [col for col in ml_columns if col in df_ml.columns]
df_ml_final = df_ml[ml_columns_available].copy()

ml_output_file = PROCESSED_DATA_DIR / "p2p_ml_dataset.csv"
df_ml_final.to_csv(ml_output_file, index=False)

print(f"  ✓ Saved to: {ml_output_file}")
print(f"    Shape: {df_ml_final.shape}")
print(f"    Columns: {len(df_ml_final.columns)}")
print(f"    File size: {ml_output_file.stat().st_size / (1024*1024):.2f} MB")


# Dataset 2: Monitoring Dataset (Clean, for production)
print("\nCreating Monitoring Dataset (Clean, for production)...")

# Determine PO item column
po_col = None
for col in ['po_item', 'purchasing_document_|_ebeln']:
    if col in df_scored.columns:
        po_col = col
        break

# Determine supplier column
supp_col = None
for col in ['supplier_|_lifnr', 'supplier_|_lifnr_first']:
    if col in df_scored.columns:
        supp_col = col
        break

# Build monitoring dataset with flexible column handling
monitoring_data = {}

# Transaction ID
if po_col and po_col in df_scored.columns:
    monitoring_data['transaction_id'] = df_scored[po_col].values
else:
    monitoring_data['transaction_id'] = range(len(df_scored))

# Supplier ID  
if supp_col and supp_col in df_scored.columns:
    monitoring_data['supplier_id'] = df_scored[supp_col].values
else:
    monitoring_data['supplier_id'] = ['UNKNOWN'] * len(df_scored)

# GR Amount
for col in ['total_gr_amount', 'gr_amount']:
    if col in df_scored.columns:
        monitoring_data['gr_amount'] = df_scored[col].values
        break
if 'gr_amount' not in monitoring_data:
    monitoring_data['gr_amount'] = [0] * len(df_scored)

# IR Amount
for col in ['total_ir_amount', 'ir_amount']:
    if col in df_scored.columns:
        monitoring_data['ir_amount'] = df_scored[col].values
        break
if 'ir_amount' not in monitoring_data:
    monitoring_data['ir_amount'] = [0] * len(df_scored)

# Anomaly Classification
if 'anomaly_class' in df_scored.columns:
    monitoring_data['anomaly_classification'] = df_scored['anomaly_class'].values
else:
    monitoring_data['anomaly_classification'] = ['UNKNOWN'] * len(df_scored)

# Days in System
if 'days_in_system' in df_scored.columns:
    monitoring_data['days_in_system'] = df_scored['days_in_system'].values
else:
    monitoring_data['days_in_system'] = [0] * len(df_scored)

# Risk Scores and Levels
monitoring_data['transaction_risk_score'] = df_scored['risk_score_transaction'].values
monitoring_data['transaction_risk_level'] = df_scored['risk_level_transaction'].values
monitoring_data['supplier_risk_score'] = df_scored['risk_score_supplier'].values
monitoring_data['supplier_risk_level'] = df_scored['risk_level_supplier'].values
monitoring_data['explanation'] = df_scored['risk_explanation'].values

df_monitoring = pd.DataFrame(monitoring_data)

monitoring_output_file = PROCESSED_DATA_DIR / "p2p_monitoring_dataset.csv"
df_monitoring.to_csv(monitoring_output_file, index=False)

print(f"  ✓ Saved to: {monitoring_output_file}")
print(f"    Shape: {df_monitoring.shape}")
print(f"    Columns: {len(df_monitoring.columns)}")
print(f"    File size: {monitoring_output_file.stat().st_size / (1024*1024):.2f} MB")


# ============================================================================
# STEP 8: CREATE SUPPLIER RISK RANKING
# ============================================================================
print("\n\n[STEP 7] SUPPLIER RISK RANKING")
print("-" * 80)

supplier_ranking = df_suppliers[[
    'supplier_id',
    'transaction_count',
    'risk_score_supplier',
    'risk_level_supplier',
    'avg_transaction_risk',
    'anomaly_rate',
    'avg_days_in_system'
]].sort_values('risk_score_supplier', ascending=False)

supplier_output_file = RISK_SCORES_DIR / "supplier_risk_ranking.csv"
supplier_ranking.to_csv(supplier_output_file, index=False)

print(f"✓ Saved to: {supplier_output_file}")
print(f"  Suppliers: {len(supplier_ranking)}")


# ============================================================================
# STEP 9: SHOW SAMPLES
# ============================================================================
print("\n\n[STEP 8] SAMPLE DATA")
print("-" * 80)

print("\n🔹 ML DATASET (First 5 rows):")
print(df_ml_final.head().to_string())

print("\n\n🔹 MONITORING DATASET (First 5 rows):")
print(df_monitoring.head().to_string())

print("\n\n🔹 TOP 10 RISKY SUPPLIERS:")
print(supplier_ranking.head(10)[['supplier_id', 'risk_score_supplier', 
                                 'risk_level_supplier', 'transaction_count',
                                 'anomaly_rate']].to_string(index=False))


# ============================================================================
# SUMMARY
# ============================================================================
print("\n\n" + "=" * 80)
print("[SUCCESS] PHASE 1 EXECUTION COMPLETE")
print("=" * 80)

print(f"""
DATASETS CREATED:
✓ p2p_ml_dataset.csv           ({df_ml_final.shape[0]:,} rows × {df_ml_final.shape[1]} cols)
✓ p2p_monitoring_dataset.csv   ({df_monitoring.shape[0]:,} rows × {df_monitoring.shape[1]} cols)
✓ supplier_risk_ranking.csv    ({len(supplier_ranking)} suppliers)

KEY METRICS:
✓ Transactions with HIGH/CRITICAL risk: {len(df_scored[df_scored['risk_level_transaction'].isin(['HIGH', 'CRITICAL'])]):,} ({len(df_scored[df_scored['risk_level_transaction'].isin(['HIGH', 'CRITICAL'])]) / len(df_scored) * 100:.2f}%)
✓ Average transaction risk score: {df_scored['risk_score_transaction'].mean():.2f}
✓ Suppliers analyzed: {len(df_suppliers)}
✓ HIGH_RISK suppliers: {len(df_suppliers[df_suppliers['risk_level_supplier'] == 'HIGH_RISK'])}

NEXT STEPS:
→ Review risk score distributions
→ Validate formulas with business team
→ Proceed to Phase 2: Features & Clustering
""")

print("=" * 80)
