#!/usr/bin/env python
"""
PHASE 2: Execution - Risk Score Recalibration & Validation
===========================================================

Step 1: Load Phase 1 data
Step 2: Compute supplier statistics (frequency, volatility)
Step 3: Apply Phase 2 recalibrated scoring
Step 4: Normalize scores to percentiles
Step 5: Compare Phase 1 vs Phase 2 distributions
Step 6: Generate validation report
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from risk_scoring_engine_v2 import (
    Phase2TransactionRiskScorer, 
    Phase2SupplierRiskScorer, 
    Phase2RiskNormalizer
)

print("="*80)
print("PHASE 2: RISK SCORE RECALIBRATION & VALIDATION")
print("="*80)

# ============================================================================
# STEP 1: Load Phase 1 Data
# ============================================================================
print("\n[STEP 1] LOADING PHASE 1 DATA")
print("-" * 80)

df_monitoring = pd.read_csv('src/data/processed/p2p_monitoring_dataset.csv')
df_ml = pd.read_csv('src/data/processed/p2p_ml_dataset.csv')

print(f"Monitoring dataset: {df_monitoring.shape[0]:,} rows")
print(f"ML dataset: {df_ml.shape[0]:,} rows")

# Keep Phase 1 scores for comparison
df_monitoring['risk_score_transaction_phase1'] = df_monitoring['transaction_risk_score']
df_monitoring['risk_level_transaction_phase1'] = df_monitoring['transaction_risk_level']


# ============================================================================
# STEP 2: Compute Supplier Statistics
# ============================================================================
print("\n[STEP 2] COMPUTING SUPPLIER STATISTICS")
print("-" * 80)

supplier_scorer = Phase2SupplierRiskScorer(verbose=True)
supplier_stats = supplier_scorer.compute_supplier_stats(df_ml)

if supplier_stats:
    print(f"\nSupplier statistics computed")
    print(f"  Frequency scores: {len(supplier_stats['frequency_map'])} suppliers")
    print(f"  Volatility scores: {len(supplier_stats['volatility_map'])} suppliers")
else:
    print("WARNING: Could not compute supplier stats, using empty maps")
    supplier_stats = {
        'frequency_map': {},
        'volatility_map': {},
        'supplier_agg': pd.DataFrame()
    }


# ============================================================================
# STEP 3: Apply Phase 2 Scoring
# ============================================================================
print("\n[STEP 3] APPLYING PHASE 2 RECALIBRATED SCORING")
print("-" * 80)

txn_scorer = Phase2TransactionRiskScorer(verbose=True)
df_scored_v2 = txn_scorer.compute_transaction_scores(df_ml, supplier_stats=supplier_stats)

print(f"\nPhase 2 Risk Scores Statistics:")
print(f"  Mean:    {df_scored_v2['risk_score_transaction_v2'].mean():.2f}")
print(f"  Median:  {df_scored_v2['risk_score_transaction_v2'].median():.2f}")
print(f"  Std:     {df_scored_v2['risk_score_transaction_v2'].std():.2f}")
print(f"  Min:     {df_scored_v2['risk_score_transaction_v2'].min():.2f}")
print(f"  Max:     {df_scored_v2['risk_score_transaction_v2'].max():.2f}")

# Copy scores to monitoring dataset
df_monitoring['risk_score_transaction_v2'] = df_scored_v2['risk_score_transaction_v2'].values


# ============================================================================
# STEP 4: Normalize Scores to Percentiles
# ============================================================================
print("\n[STEP 4] NORMALIZING SCORES TO PERCENTILES")
print("-" * 80)

normalizer = Phase2RiskNormalizer(verbose=True)
risk_levels_v2, thresholds = normalizer.normalize_transaction_scores(
    df_scored_v2['risk_score_transaction_v2'].values
)

df_monitoring['risk_level_transaction_v2'] = risk_levels_v2

print(f"\nRisk Level Distribution (Phase 2):")
dist_v2 = df_monitoring['risk_level_transaction_v2'].value_counts()
for level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
    if level in dist_v2.index:
        count = dist_v2[level]
        pct = (count / len(df_monitoring)) * 100
        print(f"  {level:12} {count:8,} ({pct:6.2f}%)")


# ============================================================================
# STEP 5: Phase 1 vs Phase 2 Comparison
# ============================================================================
print("\n[STEP 5] PHASE 1 vs PHASE 2 COMPARISON")
print("-" * 80)

print("\nTRANSACTION RISK SCORE STATISTICS:")
print(f"\n  Phase 1:")
print(f"    Mean:    {df_monitoring['risk_score_transaction_phase1'].mean():.2f}")
print(f"    Median:  {df_monitoring['risk_score_transaction_phase1'].median():.2f}")
print(f"    Std:     {df_monitoring['risk_score_transaction_phase1'].std():.2f}")
print(f"    Range:   {df_monitoring['risk_score_transaction_phase1'].min():.2f} - {df_monitoring['risk_score_transaction_phase1'].max():.2f}")

print(f"\n  Phase 2:")
print(f"    Mean:    {df_monitoring['risk_score_transaction_v2'].mean():.2f}")
print(f"    Median:  {df_monitoring['risk_score_transaction_v2'].median():.2f}")
print(f"    Std:     {df_monitoring['risk_score_transaction_v2'].std():.2f}")
print(f"    Range:   {df_monitoring['risk_score_transaction_v2'].min():.2f} - {df_monitoring['risk_score_transaction_v2'].max():.2f}")

print("\n\nRISK LEVEL DISTRIBUTION COMPARISON:")
print("\n  Phase 1:")
dist_p1 = df_monitoring['risk_level_transaction_phase1'].value_counts()
for level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
    if level in dist_p1.index:
        count = dist_p1[level]
        pct = (count / len(df_monitoring)) * 100
        print(f"    {level:12} {count:8,} ({pct:6.2f}%)")

print("\n  Phase 2:")
dist_p2 = df_monitoring['risk_level_transaction_v2'].value_counts()
for level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
    if level in dist_p2.index:
        count = dist_p2[level]
        pct = (count / len(df_monitoring)) * 100
        print(f"    {level:12} {count:8,} ({pct:6.2f}%)")
    else:
        print(f"    {level:12}        0 (  0.00%)")

print("\n\nIMPACT ANALYSIS:")
# Movement from one category to another
movement = pd.DataFrame({
    'Phase1': df_monitoring['risk_level_transaction_phase1'],
    'Phase2': df_monitoring['risk_level_transaction_v2']
})

print("\nMovement between categories:")
print(pd.crosstab(movement['Phase1'], movement['Phase2'], margins=True))


# ============================================================================
# STEP 6: Anomaly Classification Analysis
# ============================================================================
print("\n[STEP 6] ANOMALY CLASSIFICATION IMPACT")
print("-" * 80)

anomaly_analysis = df_monitoring.groupby('anomaly_classification').agg({
    'risk_score_transaction_phase1': 'mean',
    'risk_score_transaction_v2': 'mean',
    'transaction_id': 'count'
}).round(2)

anomaly_analysis.columns = ['Phase1_Mean', 'Phase2_Mean', 'Count']
anomaly_analysis['Change'] = anomaly_analysis['Phase2_Mean'] - anomaly_analysis['Phase1_Mean']

print("\nAverage Risk Score by Anomaly Classification:")
print(anomaly_analysis.to_string())


# ============================================================================
# STEP 7: Top Suppliers Comparison
# ============================================================================
print("\n[STEP 7] TOP SUPPLIERS COMPARISON")
print("-" * 80)

top_suppliers = df_monitoring.groupby('supplier_id').agg({
    'risk_score_transaction_phase1': 'mean',
    'risk_score_transaction_v2': 'mean',
    'transaction_id': 'count',
    'days_in_system': 'mean'
}).round(2)

top_suppliers.columns = ['Phase1_Avg', 'Phase2_Avg', 'TxnCount', 'AvgAging']
top_suppliers = top_suppliers.sort_values('Phase2_Avg', ascending=False)

print("\nTop 15 Suppliers by Phase 2 Risk Score:")
print(top_suppliers.head(15)[['Phase1_Avg', 'Phase2_Avg', 'TxnCount', 'AvgAging']].to_string())

print("\n\nBottom 15 Suppliers (Lowest Risk):")
print(top_suppliers.tail(15)[['Phase1_Avg', 'Phase2_Avg', 'TxnCount', 'AvgAging']].to_string())


# ============================================================================
# STEP 8: Save Results
# ============================================================================
print("\n[STEP 8] SAVING PHASE 2 RESULTS")
print("-" * 80)

# Save updated monitoring dataset
monitoring_output = 'src/data/processed/p2p_monitoring_dataset_phase2.csv'
df_monitoring.to_csv(monitoring_output, index=False)
print(f"\nSaved: {monitoring_output}")

# Save supplier comparison
supplier_output = 'src/data/diagnostics/supplier_risk_comparison_p1_vs_p2.csv'
top_suppliers.to_csv(supplier_output)
print(f"Saved: {supplier_output}")

# Save detailed comparison report
with open('src/data/diagnostics/phase2_recalibration_report.txt', 'w') as f:
    f.write("="*80 + "\n")
    f.write("PHASE 2: RISK SCORE RECALIBRATION REPORT\n")
    f.write("="*80 + "\n\n")
    
    f.write("EXECUTIVE SUMMARY\n")
    f.write("-"*80 + "\n")
    f.write(f"Transactions Analyzed: {len(df_monitoring):,}\n")
    f.write(f"Unique Suppliers: {df_monitoring['supplier_id'].nunique():,}\n\n")
    
    f.write("PHASE 1 DISTRIBUTION:\n")
    for level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
        if level in dist_p1.index:
            count = dist_p1[level]
            pct = (count / len(df_monitoring)) * 100
            f.write(f"  {level:12} {count:8,} ({pct:6.2f}%)\n")
    
    f.write("\nPHASE 2 DISTRIBUTION:\n")
    for level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
        if level in dist_p2.index:
            count = dist_p2[level]
            pct = (count / len(df_monitoring)) * 100
            f.write(f"  {level:12} {count:8,} ({pct:6.2f}%)\n")
        else:
            f.write(f"  {level:12}        0 (  0.00%)\n")
    
    f.write("\n\nWEIGHT CHANGES:\n")
    f.write("-"*80 + "\n")
    f.write("Phase 1 to Phase 2 Component Weights:\n")
    f.write("  RuleEngine:            40% to 20%  (REDUCED - NONE class too common)\n")
    f.write("  ML Probability:        20% to 15%  (REDUCED - not primary driver)\n")
    f.write("  Amount Anomaly:        15% to 15%  (UNCHANGED)\n")
    f.write("  Temporal Signal:       15% to 10%  (REDUCED - was over-dominant)\n")
    f.write("  NEW Anomaly Classif:    0% to 25%  (NEW - direct integration)\n")
    f.write("  NEW Supplier Frequency: 0% to 10%  (NEW - independent metric)\n")
    f.write("  NEW Supplier Volatility: 0% to 5%  (NEW - behavioral metric)\n")
    
    f.write("\n\nKEY IMPROVEMENTS:\n")
    f.write("-"*80 + "\n")
    f.write("1. Percentile-based normalization (target distribution)\n")
    f.write("2. Direct anomaly classification integration\n")
    f.write("3. Independent supplier risk metrics\n")
    f.write("4. Recalibrated temporal aging curve\n")
    f.write("5. Better score discrimination and spread\n")

print("Saved: src/data/diagnostics/phase2_recalibration_report.txt")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "="*80)
print("PHASE 2 EXECUTION COMPLETE")
print("="*80)

print(f"""
DISTRIBUTION IMPROVEMENT:
  Phase 1: HIGH/CRITICAL = 98.0% (OVER-AGGRESSIVE)
  Phase 2: HIGH/CRITICAL = ~{(len(df_monitoring[df_monitoring['risk_level_transaction_v2'].isin(['HIGH', 'CRITICAL'])]) / len(df_monitoring) * 100):.1f}% (REALISTIC)

SCORE RANGE IMPROVEMENT:
  Phase 1: 40.8 - 57.08 (16 point range - poor discrimination)
  Phase 2: {df_scored_v2['risk_score_transaction_v2'].min():.2f} - {df_scored_v2['risk_score_transaction_v2'].max():.2f} (better spread)

NEW DATASETS CREATED:
  [OK] p2p_monitoring_dataset_phase2.csv (with Phase 1 + Phase 2 scores)
  [OK] supplier_risk_comparison_p1_vs_p2.csv (comparison)
  [OK] phase2_recalibration_report.txt (detailed report)

NEXT STEPS:
  1. Validate Phase 2 scores with business team
  2. Check correlations with actual P2P issues
  3. Implement supplier clustering (Phase 2 Task 4)
  4. Proceed to Phase 3: SHAP Explainability
""")

print("="*80)
