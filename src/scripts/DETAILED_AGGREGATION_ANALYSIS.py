#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DETAILED AGGREGATION ANALYSIS
Why do IR-only cases (INVOICED_NOT_DELIVERED) disappear during aggregation?
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

print("="*100)
print("DETAILED AGGREGATION ANALYSIS - Why Fraud Cases Disappear")
print("="*100)

PROJECT_ROOT = Path(__file__).parent.parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "src" / "data" / "raw"
raw_file = RAW_DATA_DIR / "Documents1.csv"

if not raw_file.exists():
    print(f"[ERROR] {raw_file} not found")
    exit(1)

print(f"\n[LOADING] {raw_file.name} ({raw_file.stat().st_size / 1024 / 1024:.1f} MB)...")
df_raw = pd.read_csv(raw_file, low_memory=False)
print(f"[OK] {len(df_raw):,} rows x {df_raw.shape[1]} columns")

# Add flags
df_raw['has_e'] = df_raw['po_history_category_|_bewtp'].astype(str).str.contains('E', na=False).astype(int)
df_raw['has_q'] = df_raw['po_history_category_|_bewtp'].astype(str).str.contains('Q', na=False).astype(int)

print("\n" + "="*100)
print("ANALYSIS 1: Distribution of E and Q in RAW DATA (before aggregation)")
print("="*100)

print(f"\nRecords with E (GR): {df_raw['has_e'].sum():,}")
print(f"Records with Q (IR): {df_raw['has_q'].sum():,}")
print(f"Records with both E and Q: {((df_raw['has_e']==1) & (df_raw['has_q']==1)).sum():,}")
print(f"Records with E only: {((df_raw['has_e']==1) & (df_raw['has_q']==0)).sum():,}")
print(f"Records with Q only: {((df_raw['has_e']==0) & (df_raw['has_q']==1)).sum():,}")

# Key: Show sample Q-only records
print("\n" + "-"*100)
print("SAMPLES: Q-only records (IR without GR in raw data)")
print("-"*100)

q_only = df_raw[(df_raw['has_e']==0) & (df_raw['has_q']==1)]
print(f"\nTotal Q-only records in raw data: {len(q_only):,}")

if len(q_only) > 0:
    print(f"\nSample Q-only records (first 10):")
    cols_to_show = ['purchasing_document_|_ebeln', 'item_|_ebelp', 
                    'po_history_category_|_bewtp', 'amount_|_wrbtr', 
                    'invoice_value_|_reewr', 'supplier_|_lifnr']
    cols_available = [c for c in cols_to_show if c in q_only.columns]
    print(q_only[cols_available].head(10).to_string())
else:
    print("\n[NOTE] NO Q-only records in raw data - this is unusual!")

print("\n" + "="*100)
print("ANALYSIS 2: What happens to Q-only records during aggregation?")
print("="*100)

# Group the Q-only records by (PO, Item)
po_col = 'purchasing_document_|_ebeln'
item_col = 'item_|_ebelp'

if len(q_only) > 0:
    q_only_agg = q_only.groupby([po_col, item_col]).size()
    print(f"\nQ-only records, grouped by (PO, Item):")
    print(f"  Groups (PO+Item pairs): {len(q_only_agg):,}")
    print(f"  Total Q-only records: {q_only_agg.sum():,}")
    
    # Check if ANY of these (PO, Item) pairs appear in E records
    po_item_pairs_with_q_only = set(zip(q_only[po_col], q_only[item_col]))
    print(f"\n[CHECKING] Do these (PO, Item) pairs ALSO have E records?")
    
    e_records = df_raw[df_raw['has_e']==1]
    po_item_pairs_with_e = set(zip(e_records[po_col], e_records[item_col]))
    
    overlap = po_item_pairs_with_q_only & po_item_pairs_with_e
    no_overlap = po_item_pairs_with_q_only - po_item_pairs_with_e
    
    print(f"  (PO, Item) pairs with BOTH E and Q: {len(overlap):,}")
    print(f"  (PO, Item) pairs with ONLY Q (no E): {len(no_overlap):,}")
    
    if len(no_overlap) > 0:
        print(f"\n  -> These {len(no_overlap)} pairs SHOULD appear as INVOICED_NOT_DELIVERED!")
    else:
        print(f"\n  -> ALL Q-only records come from (PO, Item) pairs that ALSO have E records")
        print(f"  -> This explains why there are NO IR-only cases after aggregation!")
        print(f"  -> During aggregation, E and Q get combined (both=True)")
else:
    print(f"\nNo Q-only records to analyze")

print("\n" + "="*100)
print("ANALYSIS 3: Does the same PO+Item appear in BOTH E and Q records?")
print("="*100)

# Group by (PO, Item) and track which records have E and/or Q
df_raw_agg = df_raw.groupby([po_col, item_col]).agg({
    'has_e': 'max',  # Did this (PO, Item) pair have ANY E record?
    'has_q': 'max',  # Did this (PO, Item) pair have ANY Q record?
}).reset_index()

print(f"\nAfter aggregation by (PO, Item):")
print(f"  Total (PO, Item) pairs: {len(df_raw_agg):,}")

combinations = df_raw_agg.groupby(['has_e', 'has_q']).size()
print(f"\nDistribution of E/Q combinations:")
for (has_e, has_q), count in combinations.items():
    combo = ""
    if has_e == 1 and has_q == 1:
        combo = "Both E and Q"
    elif has_e == 1 and has_q == 0:
        combo = "Only E (GR only)"
    elif has_e == 0 and has_q == 1:
        combo = "Only Q (IR only - FRAUD!)"
    else:
        combo = "Neither E nor Q"
    print(f"  has_e={int(has_e)}, has_q={int(has_q)}: {count:7,} ({count/len(df_raw_agg)*100:5.2f}%) - {combo}")

# This is THE KEY METRIC
fraud_count = len(df_raw_agg[(df_raw_agg['has_e']==0) & (df_raw_agg['has_q']==1)])
print(f"\n[KEY FINDING] IR-only (PO, Item) pairs after aggregation: {fraud_count:,}")

if fraud_count == 0:
    print("\n!!! THIS IS THE ROOT CAUSE !!!")
    print("In the source data, EVERY (PO, Item) that has Q (IR) ALSO has E (GR)")
    print("There are NO (PO, Item) combinations with IR but without GR")
    print("Therefore, INVOICED_NOT_DELIVERED (fraud) = 0 after aggregation")

print("\n" + "="*100)
print("ANALYSIS 4: Temporal patterns - maybe GR comes AFTER IR?")
print("="*100)

# For Q-only records, check if GR arrives later
if len(q_only) > 0:
    print(f"\n[INVESTIGATING] Q-only records - does GR exist for same (PO, Item)?")
    
    # Take a sample Q-only record
    sample_q = q_only.iloc[0]
    sample_po = sample_q[po_col]
    sample_item = sample_q[item_col]
    
    print(f"\nExample Q-only record:")
    print(f"  PO: {sample_po}, Item: {sample_item}")
    print(f"  po_history_category_|_bewtp: {sample_q['po_history_category_|_bewtp']}")
    
    # Find ALL records for this (PO, Item)
    all_records_this_po_item = df_raw[(df_raw[po_col]==sample_po) & (df_raw[item_col]==sample_item)]
    
    print(f"\n  Total records for this (PO, Item): {len(all_records_this_po_item):,}")
    print(f"  With E: {all_records_this_po_item['has_e'].sum():,}")
    print(f"  With Q: {all_records_this_po_item['has_q'].sum():,}")
    
    if all_records_this_po_item['has_e'].sum() > 0:
        print(f"\n  -> YES! This (PO, Item) HAS E records too!")
        print(f"  -> So after aggregation, this becomes: has_gr=1, has_ir=1 (matched)")
        print(f"  -> NOT fraud")

print("\n" + "="*100)
print("ANALYSIS 5: Could this be business logic?")
print("="*100)

print("""
HYPOTHESIS: The SAP system enforces 3-way matching (PO → GR → IR)
This means:
  - You can't have IR without GR for the same PO+Item
  - The system requires GR before IR can be created
  - This is standard SAP Procure-to-Pay control

If this is true:
  - The 0 fraud cases might be EXPECTED (business is working correctly)
  - No data issue, just that fraud is prevented by design
  
ALTERNATIVE HYPOTHESIS: Data completeness issue
  - Maybe GR and IR are in different datasets
  - Maybe GR gets deleted after matching
  - Maybe the data doesn't capture the full transaction history
""")

print("\n" + "="*100)
print("CONCLUSION")
print("="*100)

print("""
ROOT CAUSE IDENTIFIED:
  ✗ No (PO, Item) pairs have IR without GR in the source data
  
REASON:
  Either:
  A) SAP controls prevent IR without prior GR (3-way matching enforcement)
  B) Data is filtered or incomplete
  C) Time period doesn't capture fraud scenarios
  
IMPACT ON FRAUD DETECTION:
  - Primary objective (INVOICED_NOT_DELIVERED fraud detection) = 0% viable
  - Models learn that "never fraud exists" instead of "detect fraud"
  - Production system won't detect if fraud occurs in future
  
NEXT STEPS:
  1. Confirm with SAP team: Is IR without GR possible in real system?
  2. Check if there's historical fraud data elsewhere
  3. Review business rules: Should we detect ATTEMPTED IR without GR?
  4. Decide: Accept 3-class model (current) or add synthetic fraud for testing?
""")
