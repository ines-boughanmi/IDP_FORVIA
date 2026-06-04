#!/usr/bin/env python
"""Generate Phase 1 Summary Report"""

import pandas as pd
import numpy as np
from pathlib import Path

print("="*80)
print("PHASE 1 EXECUTION SUMMARY REPORT")
print("="*80)

# Load datasets
df_mon = pd.read_csv('src/data/processed/p2p_monitoring_dataset.csv')
df_ml = pd.read_csv('src/data/processed/p2p_ml_dataset.csv')

print("\n" + "="*80)
print("1. DATASETS CREATED")
print("="*80)

print(f"\nML Dataset (Rich for analysis):")
print(f"  File: src/data/processed/p2p_ml_dataset.csv")
print(f"  Shape: {df_ml.shape[0]:,} rows x {df_ml.shape[1]} columns")
print(f"  Columns: {', '.join(df_ml.columns.tolist())}")

print(f"\nMonitoring Dataset (Clean for production):")
print(f"  File: src/data/processed/p2p_monitoring_dataset.csv")
print(f"  Shape: {df_mon.shape[0]:,} rows x {df_mon.shape[1]} columns")
print(f"  Columns: {', '.join(df_mon.columns.tolist())}")

print("\n" + "="*80)
print("2. TRANSACTION RISK DISTRIBUTION")
print("="*80)

txn_levels = df_mon['transaction_risk_level'].value_counts()
print("\nRisk Levels:")
for level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
    if level in txn_levels.index:
        count = txn_levels[level]
        pct = (count / len(df_mon)) * 100
        print(f"  {level:12} {count:8,} ({pct:6.2f}%)")

print(f"\nRisk Score Statistics:")
print(f"  Mean:   {df_mon['transaction_risk_score'].mean():.2f}")
print(f"  Median: {df_mon['transaction_risk_score'].median():.2f}")
print(f"  Std:    {df_mon['transaction_risk_score'].std():.2f}")
print(f"  Min:    {df_mon['transaction_risk_score'].min():.2f}")
print(f"  Max:    {df_mon['transaction_risk_score'].max():.2f}")

print("\n" + "="*80)
print("3. SUPPLIER RISK DISTRIBUTION")
print("="*80)

supp_levels = df_mon['supplier_risk_level'].value_counts()
print("\nRisk Levels:")
for level in ['HIGH_RISK', 'MONITORED', 'STANDARD', 'TRUSTED']:
    if level in supp_levels.index:
        count = supp_levels[level]
        pct = (count / len(df_mon)) * 100
        print(f"  {level:12} {count:8,} ({pct:6.2f}%)")

print(f"\nRisk Score Statistics:")
print(f"  Mean:   {df_mon['supplier_risk_score'].mean():.2f}")
print(f"  Median: {df_mon['supplier_risk_score'].median():.2f}")
print(f"  Std:    {df_mon['supplier_risk_score'].std():.2f}")
print(f"  Min:    {df_mon['supplier_risk_score'].min():.2f}")
print(f"  Max:    {df_mon['supplier_risk_score'].max():.2f}")

print("\n" + "="*80)
print("4. KEY METRICS")
print("="*80)

high_critical = len(df_mon[df_mon['transaction_risk_level'].isin(['HIGH', 'CRITICAL'])])
pct_high_critical = (high_critical / len(df_mon)) * 100

print(f"\nTransaction Metrics:")
print(f"  Total transactions: {len(df_mon):,}")
print(f"  HIGH/CRITICAL:      {high_critical:,} ({pct_high_critical:.2f}%)")
print(f"  Avg days in system: {df_mon['days_in_system'].mean():.1f} days")
print(f"  Max days in system: {df_mon['days_in_system'].max():.0f} days")

print(f"\nAmount Metrics (SAP P2P):")
print(f"  Total GR:           {df_mon['gr_amount'].sum():,.0f}")
print(f"  Total IR:           {df_mon['ir_amount'].sum():,.0f}")
print(f"  Avg GR per txn:     {df_mon['gr_amount'].mean():,.2f}")
print(f"  Avg IR per txn:     {df_mon['ir_amount'].mean():,.2f}")

unique_suppliers = df_mon['supplier_id'].nunique()
print(f"\nSupplier Metrics:")
print(f"  Unique suppliers:   {unique_suppliers:,}")

print("\n" + "="*80)
print("5. SAMPLE DATA (First 3 rows of Monitoring Dataset)")
print("="*80)

print("\n" + df_mon.head(3).to_string())

print("\n" + "="*80)
print("6. RISK SCORING FORMULA")
print("="*80)

print("""
Transaction Risk Score (0-100):
  = 0.40 * RuleEngine_Signal + 0.20 * ML_Probability + 0.15 * Amount_Anomaly 
    + 0.15 * Temporal_Signal + 0.10 * Supplier_Inherited

Component Scoring:
  - RuleEngine Signal:    Maps anomaly class (OK=0, INCOMPLETE=20, 
                          DELIVERED_NOT_INVOICED=50, INVOICED_NOT_DELIVERED=100)
  - ML Probability:       Inverts confidence score (1.0 conf = 0 risk)
  - Amount Anomaly:       Gap % (50%), Invoice ratio (30%), Blocked amount (20%)
  - Temporal Signal:      Aging-based (>180 days = 100 risk)
  - Supplier Inherited:   Aggregated supplier risk

Supplier Risk Score (0-100):
  = 0.50 * Avg_Transaction_Risk + 0.30 * Anomaly_Rate*100 
    + 0.20 * Avg_Days_in_System/180*100

Risk Levels:
  - Transaction: LOW (0-25), MEDIUM (25-50), HIGH (50-75), CRITICAL (75-100)
  - Supplier:    TRUSTED (0-30), STANDARD (30-60), MONITORED (60-80), HIGH_RISK (80-100)
""")

print("="*80)
print("PHASE 1 COMPLETE")
print("="*80)
print("\nNext Steps:")
print("  1. Review risk score distributions with business team")
print("  2. Validate formulas against manual samples")
print("  3. Proceed to Phase 2: Features & Clustering Analysis")
print("  4. Configure supplier risk thresholds for monitoring")
