#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
COMPLETE FRAUD DETECTION TRACE ANALYSIS
Trace exactly where fraud cases (INVOICED_NOT_DELIVERED) disappear
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

print("="*100)
print("FRAUD DETECTION ROOT CAUSE ANALYSIS - COMPLETE TRACE")
print("="*100)

PROJECT_ROOT = Path(__file__).parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
RAW_DATA_DIR = SRC_DIR / "data" / "raw"
PROCESSED_DATA_DIR = SRC_DIR / "data" / "processed"

print("\n")
print("="*100)
print("PHASE 1: RAW DATA ANALYSIS")
print("="*100)

# Find Documents1.csv specifically (not Ariba or other files)
raw_file = RAW_DATA_DIR / "Documents1.csv"
if not raw_file.exists():
    print(f"[ERROR] Documents1.csv not found at {raw_file}")
    # Try alternate paths
    raw_files = list(RAW_DATA_DIR.glob("Documents*.csv"))
    if raw_files:
        raw_file = raw_files[0]
        print(f"[FALLBACK] Using {raw_file.name}")
    else:
        print("[ERROR] No Documents CSV files found")
        exit(1)
print(f"\n[FILE] {raw_file.name}")
print(f"[SIZE] {raw_file.stat().st_size / 1024 / 1024:.1f} MB")

print("\n[LOADING] Raw data...")
try:
    df_raw = pd.read_csv(raw_file, low_memory=False)
except Exception as e:
    print(f"[ERROR] Failed to load: {e}")
    exit(1)

print(f"[OK] Loaded {len(df_raw):,} rows x {df_raw.shape[1]} columns")

# Show columns
print(f"\n[COLUMNS] Available in raw data:")
relevant_cols = [c for c in df_raw.columns if 'po_history' in c.lower() or 'bewtp' in c.lower() 
                  or 'movement' in c.lower() or 'amount' in c.lower() or 'invoice' in c.lower()
                  or 'receipt' in c.lower()]
for col in sorted(relevant_cols):
    print(f"  - {col}")

# Check for GR/IR indicators
print("\n[CHECKING] GR/IR detection columns...")

# Check po_history_category_|_bewtp column
if 'po_history_category_|_bewtp' in df_raw.columns:
    print(f"\n[COLUMN] po_history_category_|_bewtp")
    print(f"  Unique values: {df_raw['po_history_category_|_bewtp'].unique()}")
    
    # Count E and Q
    has_e = (df_raw['po_history_category_|_bewtp'].astype(str).str.contains('E', na=False)).sum()
    has_q = (df_raw['po_history_category_|_bewtp'].astype(str).str.contains('Q', na=False)).sum()
    has_both = (df_raw['po_history_category_|_bewtp'].astype(str).str.contains('E', na=False) & 
                df_raw['po_history_category_|_bewtp'].astype(str).str.contains('Q', na=False)).sum()
    
    print(f"  Has 'E' (GR): {has_e:,} ({has_e/len(df_raw)*100:.2f}%)")
    print(f"  Has 'Q' (IR): {has_q:,} ({has_q/len(df_raw)*100:.2f}%)")
    print(f"  Has both 'E' and 'Q': {has_both:,}")

# Alternative: check movement_type
if 'movement_type_|_bwart' in df_raw.columns:
    print(f"\n[COLUMN] movement_type_|_bwart")
    mvmt_counts = df_raw['movement_type_|_bwart'].value_counts()
    print(f"  Unique values: {sorted(df_raw['movement_type_|_bwart'].unique())}")
    for mvmt, count in mvmt_counts.head(10).items():
        pct = count / len(df_raw) * 100
        print(f"    Movement {mvmt}: {count:7,} ({pct:5.2f}%)")

# Check amount columns
print(f"\n[CHECKING] Amount/Invoice columns...")
amount_cols = [c for c in df_raw.columns if 'amount' in c.lower() or 'wrbtr' in c.lower() or 'invoice' in c.lower() or 'reewr' in c.lower()]
for col in amount_cols:
    null_count = df_raw[col].isna().sum()
    zero_count = (df_raw[col] == 0).sum()
    print(f"  {col}:")
    print(f"    Nulls: {null_count:,}, Zeros: {zero_count:,}")

# Check for PO grouping
print(f"\n[CHECKING] PO grouping keys...")
po_cols = [c for c in df_raw.columns if 'ebeln' in c.lower() or 'ebelp' in c.lower() or 'purchasing' in c.lower()]
for col in po_cols:
    unique_count = df_raw[col].nunique()
    print(f"  {col}: {unique_count:,} unique values")

# Now the critical check: simulate RuleEngine logic
print("\n" + "="*100)
print("PHASE 2: SIMULATE RULEENGINE GR/IR DETECTION")
print("="*100)

# Step 1: Filter valid transactions (same as RuleEngine)
print("\n[STEP 1] Filter valid transactions...")
initial_rows = len(df_raw)

# Filter 1: Must have amount
if 'amount_|_wrbtr' in df_raw.columns:
    df_filtered = df_raw[df_raw['amount_|_wrbtr'].notna()].copy()
    null_amount = initial_rows - len(df_filtered)
    print(f"  Removed (null amount): {null_amount:,}")
else:
    df_filtered = df_raw.copy()
    print(f"  Warning: amount_|_wrbtr column not found, skipping")

# Filter 2: Must not be deleted
if 'deletion_indicator_|_loekz' in df_filtered.columns:
    before = len(df_filtered)
    df_filtered = df_filtered[df_filtered['deletion_indicator_|_loekz'].isna()].copy()
    deleted = before - len(df_filtered)
    print(f"  Removed (deleted flag): {deleted:,}")
else:
    print(f"  Warning: deletion_indicator column not found")

print(f"  After filtering: {len(df_filtered):,} rows")

# Step 2: Aggregate by PO + Item (same as RuleEngine)
print("\n[STEP 2] Aggregate by (PO, Item)...")

po_col = 'purchasing_document_|_ebeln'
item_col = 'item_|_ebelp'

if po_col in df_filtered.columns and item_col in df_filtered.columns:
    agg_dict = {
        'amount_|_wrbtr': 'sum' if 'amount_|_wrbtr' in df_filtered.columns else 'count',
        'invoice_value_|_reewr': 'sum' if 'invoice_value_|_reewr' in df_filtered.columns else 'count',
        'po_history_category_|_bewtp': lambda x: ''.join(x.unique()) if 'po_history_category_|_bewtp' in df_filtered.columns else ''
    }
    
    # Only include columns that exist
    agg_dict_final = {}
    for col, func in agg_dict.items():
        if col in df_filtered.columns:
            agg_dict_final[col] = func
    
    df_agg = df_filtered.groupby([po_col, item_col]).agg(agg_dict_final).reset_index()
    print(f"  Before aggregation: {len(df_filtered):,} rows")
    print(f"  After aggregation: {len(df_agg):,} rows")
    print(f"  Reduction ratio: {len(df_filtered) / len(df_agg):.1f}x")
else:
    print(f"  [ERROR] PO columns not found")
    df_agg = df_filtered.copy()

# Step 3: Detect GR and IR flags (same as RuleEngine)
print("\n[STEP 3] Detect GR & IR flags...")

if 'po_history_category_|_bewtp' in df_agg.columns:
    df_agg['has_gr'] = df_agg['po_history_category_|_bewtp'].astype(str).str.contains('E', na=False).astype(int)
    df_agg['has_ir'] = df_agg['po_history_category_|_bewtp'].astype(str).str.contains('Q', na=False).astype(int)
else:
    print(f"  [WARNING] po_history_category_|_bewtp not in aggregated data")
    df_agg['has_gr'] = 0
    df_agg['has_ir'] = 0

gr_count = df_agg['has_gr'].sum()
ir_count = df_agg['has_ir'].sum()
both_count = ((df_agg['has_gr'] == 1) & (df_agg['has_ir'] == 1)).sum()
gr_only = ((df_agg['has_gr'] == 1) & (df_agg['has_ir'] == 0)).sum()
ir_only = ((df_agg['has_gr'] == 0) & (df_agg['has_ir'] == 1)).sum()
neither = ((df_agg['has_gr'] == 0) & (df_agg['has_ir'] == 0)).sum()

print(f"  Has GR (E): {gr_count:,} ({gr_count/len(df_agg)*100:.2f}%)")
print(f"  Has IR (Q): {ir_count:,} ({ir_count/len(df_agg)*100:.2f}%)")
print(f"  Has both GR+IR: {both_count:,} ({both_count/len(df_agg)*100:.2f}%)")
print(f"  GR only (DELIVERED_NOT_INVOICED): {gr_only:,} ({gr_only/len(df_agg)*100:.2f}%)")
print(f"  IR only (INVOICED_NOT_DELIVERED - FRAUD): {ir_only:,} ({ir_only/len(df_agg)*100:.2f}%) <-- KEY METRIC")
print(f"  Neither: {neither:,} ({neither/len(df_agg)*100:.2f}%)")

# Step 4: Classify anomalies (same as RuleEngine)
print("\n[STEP 4] Classify anomalies...")

def classify_row(row):
    has_gr = row['has_gr']
    has_ir = row['has_ir']
    
    if has_gr == 1 and has_ir == 1:
        return 'OK'
    elif has_gr == 1 and has_ir == 0:
        return 'DELIVERED_NOT_INVOICED'
    elif has_gr == 0 and has_ir == 1:
        return 'INVOICED_NOT_DELIVERED'
    else:
        return 'INCOMPLETE'

df_agg['anomaly_label'] = df_agg.apply(classify_row, axis=1)

print(f"  Label distribution (after RuleEngine logic):")
label_dist = df_agg['anomaly_label'].value_counts()
for label, count in label_dist.items():
    pct = count / len(df_agg) * 100
    print(f"    {label:30s}: {count:7,} ({pct:5.2f}%)")

# Step 5: Create anomaly_type (same as RuleEngine)
print("\n[STEP 5] Map anomaly_type...")

df_agg['anomaly_type'] = df_agg['anomaly_label'].apply(
    lambda x: 'ACCOUNTING' if x == 'DELIVERED_NOT_INVOICED' 
    else ('FRAUD' if x == 'INVOICED_NOT_DELIVERED' 
    else ('DATA' if x == 'INCOMPLETE' else 'NONE'))
)

print(f"  anomaly_type distribution:")
type_dist = df_agg['anomaly_type'].value_counts()
for atype, count in type_dist.items():
    pct = count / len(df_agg) * 100
    print(f"    {atype:30s}: {count:7,} ({pct:5.2f}%)")

print("\n" + "="*100)
print("PHASE 3: PROCESSED DATA VERIFICATION")
print("="*100)

# Load actual processed data
processed_files = list(PROCESSED_DATA_DIR.glob("documents_with_labels_and_features*.csv"))
if processed_files:
    processed_file = sorted(processed_files)[-1]
    print(f"\n[FILE] {processed_file.name}")
    
    print("[LOADING] Processed data...")
    df_processed = pd.read_csv(processed_file)
    print(f"[OK] Loaded {len(df_processed):,} rows x {df_processed.shape[1]} columns")
    
    # Check for label columns
    print(f"\n[COLUMNS] Label-related columns:")
    label_cols = [c for c in df_processed.columns if 'anomaly' in c.lower() or 'label' in c.lower() or 'type' in c.lower()]
    for col in label_cols:
        print(f"  {col}")
        if col in df_processed.columns:
            unique_vals = df_processed[col].unique()
            if len(unique_vals) <= 10:
                print(f"    Values: {unique_vals}")
                dist = df_processed[col].value_counts()
                for val, count in dist.items():
                    pct = count / len(df_processed) * 100
                    print(f"      {str(val):30s}: {count:7,} ({pct:5.2f}%)")

else:
    print("[WARNING] No processed data files found")

print("\n" + "="*100)
print("PHASE 4: ML VALIDATION DATA CHECK")
print("="*100)

ml_y_file = PROCESSED_DATA_DIR / "ml_features_phase2_y.csv"
if ml_y_file.exists():
    print(f"\n[FILE] {ml_y_file.name}")
    df_ml_y = pd.read_csv(ml_y_file, header=None)
    print(f"[OK] Loaded {len(df_ml_y):,} rows x {df_ml_y.shape[1]} columns")
    
    print(f"\n[DISTRIBUTION] ML Labels:")
    ml_dist = df_ml_y[0].value_counts()
    for label, count in ml_dist.items():
        pct = count / len(df_ml_y) * 100
        print(f"  {str(label):30s}: {count:7,} ({pct:5.2f}%)")
else:
    print("[WARNING] ML labels file not found")

print("\n" + "="*100)
print("PHASE 5: ROOT CAUSE ANALYSIS")
print("="*100)

# Summary
print("\n[SUMMARY] Fraud case tracking:")
print(f"  Raw data IR-only cases: {ir_only:,}")
print(f"  RuleEngine INVOICED_NOT_DELIVERED: {label_dist.get('INVOICED_NOT_DELIVERED', 0):,}")
print(f"  RuleEngine FRAUD type: {type_dist.get('FRAUD', 0):,}")

if 'anomaly_type' in df_processed.columns:
    fraud_in_processed = (df_processed['anomaly_type'] == 'FRAUD').sum()
    print(f"  Processed data FRAUD: {fraud_in_processed:,}")
else:
    fraud_in_processed = 0
    print(f"  Processed data FRAUD: NOT AVAILABLE")

if ml_y_file.exists():
    fraud_in_ml = (df_ml_y[0] == 'FRAUD').sum()
    print(f"  ML data FRAUD: {fraud_in_ml:,}")

print("\n[CONCLUSION]:")
if ir_only == 0:
    print("  ✗ NO FRAUD CASES IN RAW DATA")
    print("  → Root cause: No IR-without-GR transactions in source data")
    print("  → Business impact: Either frauds don't exist or data is incomplete")
elif ir_only > 0 and label_dist.get('INVOICED_NOT_DELIVERED', 0) == 0:
    print("  ✗ FRAUD CASES EXIST IN RAW DATA BUT LOST DURING PROCESSING")
    print("  → Root cause: RuleEngine or aggregation logic issue")
    print("  → Business impact: Logic bug preventing fraud detection")
elif ir_only > 0 and label_dist.get('INVOICED_NOT_DELIVERED', 0) > 0:
    print("  ✓ FRAUD CASES DETECTED BY RULEENGINE")
    if fraud_in_processed == 0:
        print("  ✗ BUT LOST DURING FEATURE ENGINEERING OR EXPORT")
    elif fraud_in_ml == 0:
        print("  ✗ BUT LOST DURING ML PREPARATION")
    else:
        print("  ✓ ALL FRAUD CASES PRESENT IN FINAL ML DATA")

print("\n" + "="*100)
print("END OF DIAGNOSTIC")
print("="*100)
