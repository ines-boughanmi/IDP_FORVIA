#!/usr/bin/env python
"""
PHASE 2: Risk Score Re-Calibration - Diagnostic Analysis
=========================================================

Task 1: Analyze current distribution and identify calibration issues
Task 2: Validate feature contributions
Task 3: Prepare for recalibration
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from pathlib import Path

print("="*80)
print("PHASE 2: DIAGNOSTIC ANALYSIS - Risk Score Calibration")
print("="*80)

# Load datasets
df_mon = pd.read_csv('src/data/processed/p2p_monitoring_dataset.csv')
df_ml = pd.read_csv('src/data/processed/p2p_ml_dataset.csv')

print(f"\nDataset loaded: {len(df_mon):,} transactions")

# ============================================================================
# ANALYSIS 1: Current Transaction Risk Distribution
# ============================================================================
print("\n" + "="*80)
print("1. CURRENT TRANSACTION RISK DISTRIBUTION (Phase 1)")
print("="*80)

txn_dist = df_mon['transaction_risk_level'].value_counts().sort_index()
print("\nRisk Level Counts:")
for level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
    if level in df_mon['transaction_risk_level'].values:
        count = len(df_mon[df_mon['transaction_risk_level'] == level])
        pct = (count / len(df_mon)) * 100
        print(f"  {level:12} {count:8,} ({pct:6.2f}%)")

print("\nRisk Score Statistics:")
print(f"  Mean:      {df_mon['transaction_risk_score'].mean():.2f}")
print(f"  Median:    {df_mon['transaction_risk_score'].median():.2f}")
print(f"  Std Dev:   {df_mon['transaction_risk_score'].std():.4f}")
print(f"  Min:       {df_mon['transaction_risk_score'].min():.2f}")
print(f"  Max:       {df_mon['transaction_risk_score'].max():.2f}")
print(f"  Percentiles:")
for p in [10, 25, 50, 75, 90]:
    val = np.percentile(df_mon['transaction_risk_score'], p)
    print(f"    {p}th:     {val:.2f}")

# ============================================================================
# ANALYSIS 2: Current Supplier Risk Distribution
# ============================================================================
print("\n" + "="*80)
print("2. CURRENT SUPPLIER RISK DISTRIBUTION (Phase 1)")
print("="*80)

supp_dist = df_mon['supplier_risk_level'].value_counts().sort_index()
print("\nSupplier Risk Level (Transaction-level):")
for level in ['TRUSTED', 'STANDARD', 'MONITORED', 'HIGH_RISK']:
    if level in df_mon['supplier_risk_level'].values:
        count = len(df_mon[df_mon['supplier_risk_level'] == level])
        pct = (count / len(df_mon)) * 100
        print(f"  {level:12} {count:8,} ({pct:6.2f}%)")

print("\nSupplier Risk Score Statistics (transaction-level):")
print(f"  Mean:      {df_mon['supplier_risk_score'].mean():.2f}")
print(f"  Median:    {df_mon['supplier_risk_score'].median():.2f}")
print(f"  Std Dev:   {df_mon['supplier_risk_score'].std():.4f}")
print(f"  Min:       {df_mon['supplier_risk_score'].min():.2f}")
print(f"  Max:       {df_mon['supplier_risk_score'].max():.2f}")

# ============================================================================
# ANALYSIS 3: Analyze by Supplier Aggregation
# ============================================================================
print("\n" + "="*80)
print("3. SUPPLIER-LEVEL AGGREGATION ANALYSIS")
print("="*80)

supplier_stats = df_mon.groupby('supplier_id').agg({
    'transaction_risk_score': ['count', 'mean', 'std', 'min', 'max'],
    'days_in_system': 'mean',
    'gr_amount': 'sum',
    'anomaly_classification': lambda x: (x != 'NONE').sum() / len(x) if len(x) > 0 else 0
}).round(3)

supplier_stats.columns = ['txn_count', 'avg_risk', 'std_risk', 'min_risk', 'max_risk',
                          'avg_aging', 'total_gr', 'anomaly_rate']

print(f"\nSuppliers: {len(supplier_stats):,}")
print(f"\nSupplier Counts by Transaction Volume:")
print(f"  1-5 txns:      {len(supplier_stats[supplier_stats['txn_count'] <= 5]):,}")
print(f"  6-20 txns:     {len(supplier_stats[(supplier_stats['txn_count'] > 5) & (supplier_stats['txn_count'] <= 20)]):,}")
print(f"  21-100 txns:   {len(supplier_stats[(supplier_stats['txn_count'] > 20) & (supplier_stats['txn_count'] <= 100)]):,}")
print(f"  100+ txns:     {len(supplier_stats[supplier_stats['txn_count'] > 100]):,}")

print(f"\nSupplier Risk Score Statistics (aggregate):")
print(f"  Mean:      {supplier_stats['avg_risk'].mean():.2f}")
print(f"  Median:    {supplier_stats['avg_risk'].median():.2f}")
print(f"  Std Dev:   {supplier_stats['avg_risk'].std():.4f}")
print(f"  Min:       {supplier_stats['avg_risk'].min():.2f}")
print(f"  Max:       {supplier_stats['avg_risk'].max():.2f}")

# ============================================================================
# ANALYSIS 4: Feature Correlation with Risk
# ============================================================================
print("\n" + "="*80)
print("4. FEATURE CORRELATION WITH TRANSACTION RISK")
print("="*80)

corr_cols = ['transaction_risk_score', 'days_in_system', 'gr_amount', 'ir_amount']
available_cols = [c for c in corr_cols if c in df_mon.columns]

print(f"\nCorrelations with transaction_risk_score:")
correlations = df_mon[available_cols].corr()['transaction_risk_score'].sort_values(ascending=False)
for feature, corr_val in correlations.items():
    if feature != 'transaction_risk_score':
        print(f"  {feature:30} {corr_val:8.4f}")

# ============================================================================
# ANALYSIS 5: Anomaly Classification Distribution
# ============================================================================
print("\n" + "="*80)
print("5. ANOMALY CLASSIFICATION ANALYSIS")
print("="*80)

anom_dist = df_mon['anomaly_classification'].value_counts()
print("\nAnomalies by Classification:")
for anom, count in anom_dist.items():
    pct = (count / len(df_mon)) * 100
    avg_risk = df_mon[df_mon['anomaly_classification'] == anom]['transaction_risk_score'].mean()
    print(f"  {str(anom):20} {count:8,} ({pct:6.2f}%) Avg Risk: {avg_risk:6.2f}")

# ============================================================================
# ANALYSIS 6: Problems Identified
# ============================================================================
print("\n" + "="*80)
print("6. IDENTIFIED PROBLEMS & CALIBRATION ISSUES")
print("="*80)

print("""
PROBLEM 1: Over-Aggressive Scoring
  - 98% of transactions classified as HIGH/CRITICAL
  - Very narrow score range: 40.8 - 57.08 (only 16 points)
  - No discrimination between transactions

ROOT CAUSES:
  a) RuleEngine Signal: All transactions = NONE class → score should be 0
     BUT: Currently using ML confidence as main driver
  
  b) Temporal Signal: Aging factor dominates
     - Most transactions > 180 days (avg 483 days)
     - Temporal_Signal scores: 40-80 for all
  
  c) Missing Supplier ID: All use default 25.0 (no supplier discrimination)

PROBLEM 2: Lack of Statistical Calibration
  - Scores not normalized by percentiles
  - No distribution-aware thresholds
  - Fixed thresholds (50-75 for HIGH) not appropriate for this data

PROBLEM 3: Supplier Risk De-Correlation
  - 100% of transactions show STANDARD supplier risk
  - Supplier scores not independent of transaction scores
  - Missing: frequency, volatility, consistency metrics

RECOMMENDATION FOR RECALIBRATION:
  1. Use percentile-based normalization (not fixed thresholds)
  2. Reduce weight of temporal signal OR recalibrate aging formula
  3. Add supplier-independent features (frequency, volatility)
  4. Include anomaly_classification more directly
  5. Test on different supplier segments

TARGET DISTRIBUTION:
  - LOW:      30-40%  (normal, no issues)
  - MEDIUM:   25-35%  (watch, some issues)
  - HIGH:     15-25%  (investigate, multiple issues)
  - CRITICAL: 5-10%   (immediate action, severe issues)
""")

# ============================================================================
# ANALYSIS 7: Top vs Bottom Suppliers
# ============================================================================
print("\n" + "="*80)
print("7. TOP vs BOTTOM SUPPLIERS COMPARISON")
print("="*80)

top_suppliers = supplier_stats.nlargest(5, 'txn_count')
print("\nTop 5 Suppliers by Transaction Count:")
print(top_suppliers[['txn_count', 'avg_risk', 'std_risk', 'avg_aging', 'anomaly_rate']].to_string())

print("\n\nBottom 10 Suppliers by Transaction Count:")
bottom_suppliers = supplier_stats.nsmallest(10, 'txn_count')
print(bottom_suppliers[['txn_count', 'avg_risk', 'std_risk', 'avg_aging', 'anomaly_rate']].to_string())

# ============================================================================
# ANALYSIS 8: Save Summary for Next Phase
# ============================================================================
print("\n" + "="*80)
print("8. SAVING DIAGNOSTIC RESULTS")
print("="*80)

supplier_stats.to_csv('src/data/diagnostics/phase2_supplier_diagnostics.csv')
print("\nDiagnostic file saved: src/data/diagnostics/phase2_supplier_diagnostics.csv")

# Save distribution for reference
with open('src/data/diagnostics/phase2_diagnostic_summary.txt', 'w') as f:
    f.write("PHASE 2 DIAGNOSTIC SUMMARY\n")
    f.write("="*80 + "\n\n")
    f.write("Current Transaction Distribution:\n")
    f.write(f"  HIGH/CRITICAL: {len(df_mon[df_mon['transaction_risk_level'].isin(['HIGH', 'CRITICAL'])]):,} ({len(df_mon[df_mon['transaction_risk_level'].isin(['HIGH', 'CRITICAL'])]) / len(df_mon) * 100:.2f}%)\n")
    f.write(f"  MEDIUM: {len(df_mon[df_mon['transaction_risk_level'] == 'MEDIUM']):,}\n")
    f.write(f"  LOW: {len(df_mon[df_mon['transaction_risk_level'] == 'LOW']):,}\n\n")
    f.write("Problems:\n")
    f.write("  1. Over-aggressive scoring (98% HIGH/CRITICAL)\n")
    f.write("  2. Narrow score range (40.8-57.08)\n")
    f.write("  3. No supplier discrimination\n")
    f.write("  4. Temporal aging dominates\n\n")
    f.write("Calibration Targets:\n")
    f.write("  LOW: 30-40%\n")
    f.write("  MEDIUM: 25-35%\n")
    f.write("  HIGH: 15-25%\n")
    f.write("  CRITICAL: 5-10%\n")

print("Summary saved: src/data/diagnostics/phase2_diagnostic_summary.txt")

print("\n" + "="*80)
print("DIAGNOSTIC COMPLETE - Ready for Recalibration")
print("="*80)
