"""
PHASE 4: DATA QUALITY FIX
=========================
Targeted fixes for production datasets without re-running the full ML pipeline.

Issues fixed:
  1. Supplier risk_level was 100% "LOW" — now uses correct score thresholds
  2. 245 HIGH_RISK_SUPPLIERS had NULL risk_score — filled with cluster-appropriate default
  3. All supplier explanations were "No explanation available" — generated from features
  4. amount_gap_pct had ~10k negative values (formula bug) — fixed to abs/max formula
  5. 15,324 duplicate transaction rows — deduplicated
  6. supplier_risk_level in transactions was 100% "STANDARD" — corrected from supplier table
  7. supplier_risk_score in transactions was stale — synced with current supplier scores
  8. monitoring_dataset.csv regenerated with accurate metrics from fixed data
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# ── project path ─────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PRODUCTS_DIR  = PROJECT_ROOT / "src" / "data" / "products"
PROCESSED_DIR = PROJECT_ROOT / "src" / "data" / "processed"

# ── risk-level thresholds (suppliers, 0-100 scale) ───────────────────────────
# Derived from actual score distribution (mean=41.3, std=5.9, range 17-65)
# LOW    : < 38   (~25 % of suppliers — normal, minimal attention)
# MEDIUM : 38-45  (~50 % of suppliers — standard monitoring)
# HIGH   : 45-55  (~22 % of suppliers — enhanced monitoring needed)
# CRITICAL: > 55  (~ 3 % of suppliers — immediate review required)
SUP_LOW      = 38.0
SUP_MEDIUM   = 45.0
SUP_HIGH     = 55.0


def supplier_score_to_level(score: float) -> str:
    """Map a 0-100 supplier risk score to a risk level string."""
    if pd.isna(score):
        return "MEDIUM"          # unknown → default to monitored
    if score < SUP_LOW:
        return "LOW"
    elif score < SUP_MEDIUM:
        return "MEDIUM"
    elif score < SUP_HIGH:
        return "HIGH"
    else:
        return "CRITICAL"


# ── supplier explanation generation ─────────────────────────────────────────

def generate_explanation(row: pd.Series) -> str:
    """
    Build a concise, human-readable explanation for a supplier's risk profile.
    Uses features present in supplier_risk_table.csv.
    """
    parts = []

    risk_level = row.get("risk_level", "UNKNOWN")
    score      = row.get("risk_score", 0)

    # ── opening sentence ──────────────────────────────────────────────────
    parts.append(f"Supplier classified as {risk_level} risk (score {score:.1f}/100).")

    risk_drivers = []
    warnings_list = []
    strengths_list = []

    # Anomaly rate
    anomaly_rate = row.get("anomaly_rate", 0) or 0
    if anomaly_rate >= 0.50:
        risk_drivers.append(f"very high anomaly rate ({anomaly_rate:.0%} of transactions flagged)")
    elif anomaly_rate >= 0.20:
        risk_drivers.append(f"elevated anomaly rate ({anomaly_rate:.0%})")
    elif anomaly_rate >= 0.10:
        warnings_list.append(f"moderate anomaly rate ({anomaly_rate:.0%})")
    elif anomaly_rate == 0:
        strengths_list.append("no transaction anomalies detected")

    # Accounting issues
    acct_rate = row.get("accounting_issue_rate", 0) or 0
    if acct_rate >= 0.30:
        risk_drivers.append(f"frequent accounting issues ({acct_rate:.0%} of transactions)")
    elif acct_rate >= 0.10:
        warnings_list.append(f"accounting discrepancies in {acct_rate:.0%} of transactions")

    # Data quality issues
    data_rate = row.get("data_issue_rate", 0) or 0
    if data_rate >= 0.20:
        risk_drivers.append(f"data quality problems in {data_rate:.0%} of transactions")
    elif data_rate >= 0.05:
        warnings_list.append(f"data issues in {data_rate:.0%} of transactions")

    # Average aging
    avg_aging = row.get("avg_aging_days", 0) or 0
    if avg_aging >= 600:
        risk_drivers.append(f"critically aged transactions (avg {avg_aging:.0f} days)")
    elif avg_aging >= 450:
        warnings_list.append(f"high average transaction age ({avg_aging:.0f} days)")
    elif avg_aging < 200:
        strengths_list.append(f"low average transaction age ({avg_aging:.0f} days)")

    # Amount volatility
    volatility = row.get("amount_volatility", 0) or 0
    if volatility >= 3.0:
        risk_drivers.append(f"extreme amount volatility (CV={volatility:.1f})")
    elif volatility >= 1.5:
        warnings_list.append(f"high amount volatility (CV={volatility:.1f})")
    elif volatility < 0.5:
        strengths_list.append("stable transaction amounts")

    # Stability score
    stability = row.get("stability_score", 0) or 0
    if stability >= 0.8:
        strengths_list.append("consistent and stable processing behaviour")
    elif stability < 0.3:
        risk_drivers.append("unstable processing behaviour")

    # Transaction frequency
    freq = row.get("transaction_frequency", 0) or 0
    if freq >= 500:
        strengths_list.append(f"high transaction volume ({freq:,} transactions)")
    elif freq < 5:
        warnings_list.append(f"very low transaction volume ({freq} transaction{'s' if freq != 1 else ''}) — limited history")

    # ── build narrative ───────────────────────────────────────────────────
    if risk_drivers:
        parts.append("Risk driven by: " + "; ".join(risk_drivers) + ".")
    if warnings_list:
        parts.append("Warnings: " + "; ".join(warnings_list) + ".")
    if strengths_list:
        parts.append("Strengths: " + "; ".join(strengths_list) + ".")

    # ── recommendation ────────────────────────────────────────────────────
    if risk_level == "CRITICAL":
        parts.append("Action: Immediate review and escalation required.")
    elif risk_level == "HIGH":
        parts.append("Action: Investigate risk factors; schedule supplier review.")
    elif risk_level == "MEDIUM":
        parts.append("Action: Apply standard enhanced monitoring.")
    else:
        parts.append("Action: Maintain routine monitoring.")

    return " ".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Fix supplier_risk_table.csv
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 72)
print("PHASE 4: DATA QUALITY FIX")
print("=" * 72)

print("\n[1/4] Fixing supplier_risk_table.csv …")

sup = pd.read_csv(PRODUCTS_DIR / "supplier_risk_table.csv")
print(f"      Loaded {len(sup):,} suppliers")

# 1-a  Fill NULL risk_scores (245 HIGH_RISK_SUPPLIERS with 1 transaction)
#      Cluster label says HIGH_RISK → assign floor score of 50.0 (HIGH tier)
null_mask = sup["risk_score"].isna()
null_count = null_mask.sum()
sup.loc[null_mask & (sup["cluster_label"] == "HIGH_RISK_SUPPLIERS"), "risk_score"] = 50.0
sup.loc[null_mask & (sup["cluster_label"] != "HIGH_RISK_SUPPLIERS"), "risk_score"] = (
    sup["risk_score"].median()
)
print(f"      Fixed {null_count} NULL risk_scores")

# 1-b  Recalculate risk_level with correct thresholds
old_levels = sup["risk_level"].value_counts().to_dict()
sup["risk_level"] = sup["risk_score"].apply(supplier_score_to_level)
new_levels = sup["risk_level"].value_counts().to_dict()
print(f"      risk_level BEFORE: {old_levels}")
print(f"      risk_level AFTER : {new_levels}")

# 1-c  Also fill NULL aging_std_dev (same 245 rows) with cluster median
aging_null = sup["aging_std_dev"].isna().sum()
sup["aging_std_dev"] = sup["aging_std_dev"].fillna(sup["aging_std_dev"].median())
print(f"      Fixed {aging_null} NULL aging_std_dev values")

# 1-d  Generate explanations for every supplier
print("      Generating business explanations …")
sup["explanation"] = sup.apply(generate_explanation, axis=1)
blank_before = (sup["explanation"] == "No explanation available").sum()
print(f"      Replaced {blank_before} blank explanations with generated text")

# 1-e  Update timestamp
sup["created_timestamp"] = datetime.utcnow().isoformat()

sup.to_csv(PRODUCTS_DIR / "supplier_risk_table.csv", index=False)
print(f"      ✓ supplier_risk_table.csv saved ({len(sup):,} rows)")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Fix transactions_risk_table.csv
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[2/4] Fixing transactions_risk_table.csv …")

print("      Loading … (this may take ~30 s for 294k rows)")
txn = pd.read_csv(PRODUCTS_DIR / "transactions_risk_table.csv")
print(f"      Loaded {len(txn):,} transactions")

# 2-a  Fix amount_gap_pct (negative values from old GR-based denominator)
bad_gap = (txn["amount_gap_pct"] < 0).sum()
denom = txn[["gr_amount", "ir_amount"]].abs().max(axis=1).replace(0, np.nan)
txn["amount_gap_pct"] = (
    txn["amount_difference"].abs() / denom * 100
).fillna(0).round(4)
# Clamp to [0, 100]
txn["amount_gap_pct"] = txn["amount_gap_pct"].clip(0, 100)
print(f"      Fixed {bad_gap:,} negative amount_gap_pct values")
print(f"      amount_gap_pct new range: {txn['amount_gap_pct'].min():.2f}% – {txn['amount_gap_pct'].max():.2f}%")

# 2-b  Deduplicate rows
before_dedup = len(txn)
txn = txn.drop_duplicates(
    subset=["transaction_id", "supplier_id", "gr_amount", "ir_amount"],
    keep="first"
)
removed = before_dedup - len(txn)
print(f"      Removed {removed:,} exact duplicate rows ({removed/before_dedup*100:.1f}%)")

# 2-c  Update supplier_risk_score and supplier_risk_level from fixed supplier table
#      The stored column "supplier_risk_level" was the cluster description ("STANDARD"),
#      not the actual risk level. Fix by joining to the supplier table.
sup_lookup = sup.set_index("supplier_id")[["risk_score", "risk_level"]]
txn["supplier_risk_score"] = txn["supplier_id"].map(sup_lookup["risk_score"])
txn["supplier_risk_level"] = txn["supplier_id"].map(sup_lookup["risk_level"])

# Fill unmatched supplier IDs with sensible defaults
unmatched = txn["supplier_risk_level"].isna().sum()
txn["supplier_risk_score"] = txn["supplier_risk_score"].fillna(sup["risk_score"].median())
txn["supplier_risk_level"] = txn["supplier_risk_level"].fillna("MEDIUM")
print(f"      Updated supplier_risk_score / supplier_risk_level from supplier table")
print(f"      supplier_risk_level distribution: {txn['supplier_risk_level'].value_counts().to_dict()}")
if unmatched:
    print(f"      (Filled {unmatched:,} unmatched supplier IDs with median score / MEDIUM)")

# 2-d  Update timestamp
txn["created_timestamp"] = datetime.utcnow().isoformat()

txn.to_csv(PRODUCTS_DIR / "transactions_risk_table.csv", index=False)
sz = (PRODUCTS_DIR / "transactions_risk_table.csv").stat().st_size / 1024 / 1024
print(f"      ✓ transactions_risk_table.csv saved ({len(txn):,} rows, {sz:.1f} MB)")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Regenerate monitoring_dataset.csv
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[3/4] Regenerating monitoring_dataset.csv …")

metrics = []

# Volume
metrics.append({"metric_name": "total_transactions",  "metric_value": len(txn),                       "metric_type": "gauge", "category": "volume"})
metrics.append({"metric_name": "unique_suppliers",     "metric_value": txn["supplier_id"].nunique(),    "metric_type": "gauge", "category": "volume"})

# Risk distribution — transactions
for level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
    cnt = (txn["risk_level"] == level).sum()
    pct = round(cnt / len(txn) * 100, 2)
    metrics.append({"metric_name": f"transactions_{level.lower()}_count", "metric_value": int(cnt),  "metric_type": "gauge", "category": "risk_distribution"})
    metrics.append({"metric_name": f"transactions_{level.lower()}_pct",   "metric_value": pct,       "metric_type": "gauge", "category": "risk_distribution"})

# Aggregates
metrics.append({"metric_name": "avg_transaction_risk_score",    "metric_value": round(float(txn["risk_score"].mean()),   2), "metric_type": "gauge", "category": "aggregates"})
metrics.append({"metric_name": "median_transaction_risk_score", "metric_value": round(float(txn["risk_score"].median()), 2), "metric_type": "gauge", "category": "aggregates"})

# Anomalies
anomaly_cnt = int((txn["has_anomaly"] == 1).sum())
metrics.append({"metric_name": "transactions_with_anomalies_count", "metric_value": anomaly_cnt,                                  "metric_type": "gauge", "category": "anomalies"})
metrics.append({"metric_name": "transactions_with_anomalies_pct",   "metric_value": round(anomaly_cnt / len(txn) * 100, 2),        "metric_type": "gauge", "category": "anomalies"})

# Delays
delayed_cnt = int((txn["is_delayed"] == 1).sum())
metrics.append({"metric_name": "delayed_transactions_count", "metric_value": delayed_cnt,                                   "metric_type": "gauge", "category": "delays"})
metrics.append({"metric_name": "delayed_transactions_pct",   "metric_value": round(delayed_cnt / len(txn) * 100, 2),         "metric_type": "gauge", "category": "delays"})
metrics.append({"metric_name": "avg_days_in_system",         "metric_value": round(float(txn["days_in_system"].mean()), 2), "metric_type": "gauge", "category": "delays"})

# Supplier-level aggregates
metrics.append({"metric_name": "avg_supplier_risk_score", "metric_value": round(float(sup["risk_score"].mean()), 2), "metric_type": "gauge", "category": "supplier"})

# Supplier risk distribution
for level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
    cnt = (sup["risk_level"] == level).sum()
    pct = round(cnt / len(sup) * 100, 2)
    metrics.append({"metric_name": f"suppliers_{level.lower()}_count", "metric_value": int(cnt),  "metric_type": "gauge", "category": "supplier_risk_distribution"})
    metrics.append({"metric_name": f"suppliers_{level.lower()}_pct",   "metric_value": pct,       "metric_type": "gauge", "category": "supplier_risk_distribution"})

mon = pd.DataFrame(metrics)
mon.to_csv(PRODUCTS_DIR / "monitoring_dataset.csv", index=False)
print(f"      ✓ monitoring_dataset.csv saved ({len(mon)} metrics)")
print(f"      Key metrics:")
for _, row in mon.iterrows():
    if "pct" in row["metric_name"] or row["metric_name"] in ("avg_transaction_risk_score", "avg_supplier_risk_score"):
        print(f"        {row['metric_name']:45s} = {row['metric_value']}")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Regenerate JSONL files for RAG chatbot
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[4/4] Regenerating JSONL files for RAG chatbot …")

with open(PRODUCTS_DIR / "supplier_risk_table.jsonl", "w", encoding="utf-8") as f:
    for _, row in sup.iterrows():
        f.write(row.to_json() + "\n")
print("      ✓ supplier_risk_table.jsonl")

# Transactions JSONL: use top-5 000 by risk_score (same as RAG indexing strategy)
top_txn = txn.nlargest(5_000, "risk_score")
with open(PRODUCTS_DIR / "transactions_risk_table.jsonl", "w", encoding="utf-8") as f:
    for _, row in top_txn.iterrows():
        f.write(row.to_json() + "\n")
print(f"      ✓ transactions_risk_table.jsonl (top 5,000 by risk_score)")


# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 72)
print("PHASE 4 COMPLETE — PRODUCTION DATA QUALITY FIX")
print("=" * 72)

print("\n  SUPPLIER RISK TABLE:")
print(f"    Total suppliers : {len(sup):,}")
print(f"    Risk distribution: {sup['risk_level'].value_counts().to_dict()}")
print(f"    Score range     : {sup['risk_score'].min():.1f} – {sup['risk_score'].max():.1f}")
print(f"    With explanation: {(sup['explanation'] != 'No explanation available').sum():,}")

print("\n  TRANSACTION RISK TABLE:")
print(f"    Total rows      : {len(txn):,}")
print(f"    Risk distribution: {txn['risk_level'].value_counts().to_dict()}")
print(f"    supplier_risk_level: {txn['supplier_risk_level'].value_counts().to_dict()}")
gap_neg = (txn["amount_gap_pct"] < 0).sum()
print(f"    Negative amount_gap_pct remaining: {gap_neg}")

print("\n  FILES SAVED:")
for f in PRODUCTS_DIR.glob("*"):
    sz = f.stat().st_size
    unit = "KB" if sz < 1024*1024 else "MB"
    val = sz/1024 if sz < 1024*1024 else sz/1024/1024
    print(f"    {f.name:45s} {val:6.1f} {unit}")

print()
