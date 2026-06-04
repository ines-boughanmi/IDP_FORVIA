# ACTION PLAN - FRAUD DETECTION BLOCKER
## SAP P2P Anomaly Detection - Critical Path to Production

---

## SITUATION

**Status:** ML pipeline successfully executed but **PRIMARY OBJECTIVE NOT VALIDATED**

- ✅ 4 models trained (F1=1.0)
- ✅ 40 features engineered
- ✅ 294K records processed
- 🔴 **BLOCKER:** 0 fraud cases found (should have many)

---

## ROOT CAUSE: UNKNOWN

We need to determine WHY there are zero INVOICED_NOT_DELIVERED cases:

```
Is the problem in:
┌─ A. DATA SOURCE? 
│  └─ Raw SAP data has no IR-without-GR scenarios
│
├─ B. DATA PROCESSING?
│  └─ RuleEngine logic not detecting fraud correctly
│
└─ C. FEATURE ENGINEERING?
   └─ Aggregation or filtering hiding frauds
```

---

## PHASE 1: ROOT CAUSE ANALYSIS (24 HOURS)

### Task 1a: Check Raw Data
**Time:** 1 hour  
**Owner:** Data Engineer

**What to do:**
```python
import pandas as pd

# Load raw data
docs = pd.read_csv("src/data/raw/Documents1.csv")

# Count IR-without-GR cases
has_ir = (docs['has_ir'] == 1).sum()
has_gr = (docs['has_gr'] == 1).sum()
both = ((docs['has_ir'] == 1) & (docs['has_gr'] == 1)).sum()
ir_without_gr = ((docs['has_ir'] == 1) & (docs['has_gr'] == 0)).sum()

print(f"Has IR: {has_ir}")
print(f"Has GR: {has_gr}")
print(f"Has Both: {both}")
print(f"Has IR without GR: {ir_without_gr}")  # ← This is what we need
```

**Expected Results:**
- **If > 0:** Fraud cases exist in raw data → Problem is in processing
- **If = 0:** No frauds in raw data → Problem is in SAP/business

---

### Task 1b: Check RuleEngine Logic
**Time:** 1 hour  
**Owner:** Data Scientist

**What to do:**

1. Open [src/scripts/rule_engine.py](src/scripts/rule_engine.py)
2. Find `classify_anomalies()` method
3. Review the classification logic:

```python
# Expected logic should be:
if has_gr and not has_ir:
    return 'DELIVERED_NOT_INVOICED'
elif has_ir and not has_gr:
    return 'INVOICED_NOT_DELIVERED'  # ← This creates fraud labels
elif has_ir and has_gr:
    return 'MATCHED'  # or similar
else:
    return 'INCOMPLETE'
```

4. Check if this logic is present and correct
5. Verify 'INVOICED_NOT_DELIVERED' is in ANOMALY_TYPES

**Expected Issues to Find:**
- Logic might be inverted (checking has_gr instead of not has_gr)
- Condition might use AND instead of AND NOT
- Label name might be different
- Logic might be missing entirely

---

### Task 1c: Trace Data Through Pipeline
**Time:** 2 hours  
**Owner:** Data Engineer

**Steps:**

1. Check pipeline statistics files:
   ```
   src/data/
   ├── raw/
   ├── data_fuss/
   ├── data-fusion/
   ├── processed/
   └── risk_scores/
   ```

2. Look for intermediate statistics showing label distribution

3. Find WHERE fraud cases get lost:
   - Raw data → After cleaning → After fusion → After final processing

4. Create debug dataset with sample transactions

---

### Task 1d: Validate SAP Business Logic
**Time:** 2 hours  
**Owner:** SAP Business Analyst

**Steps:**

1. Review SAP P2P documentation
2. Verify when IR occurs without GR (fraud scenario)
3. Check if SAP system prevents this:
   - Required GR before IR?
   - Blocked transactions?
   - Alternative matching process?
4. Get sample transactions showing IR-without-GR pattern
5. Validate these are considered "fraud" in business

---

## PHASE 2: DECISION POINT (AFTER 24 HOURS)

### Scenario A: Fraud Cases Found in Raw Data
**What this means:** Problem is in data processing pipeline

**Action:**
1. Fix RuleEngine or feature engineering
2. Re-process all 294K records
3. Retrain models
4. Go to Phase 3

**Timeline:** 48 hours

---

### Scenario B: No Fraud Cases in Raw Data
**What this means:** Options:

**Option B1: Fraud Never Occurs (Positive)**
- Business controls prevent fraud
- System is working correctly
- Action: Retrain on 3 classes, accept this is the reality
- Timeline: 24 hours

**Option B2: Data Doesn't Cover Fraud Period**
- Historical data predates fraud incidents
- Need more recent data
- Action: Request newer transaction data
- Timeline: 72 hours for data acquisition

**Option B3: Fraud Cases Excluded by Filters**
- Data cleaning removed suspicious transactions
- Need to investigate what was filtered
- Action: Review filtering logic, restore suspicious cases
- Timeline: 48 hours

---

## PHASE 3: FIX & RETRAIN (48-72 HOURS AFTER DECISION)

### If Fraud Cases Found: Fix Processing

```python
# Step 1: Verify fix works
fixed_data = pd.read_csv("src/data/processed/ml_features_phase2_y.csv")
fraud_count = (fixed_data == 'INVOICED_NOT_DELIVERED').sum()
print(f"Fraud cases after fix: {fraud_count}")
# Should show > 0

# Step 2: Retrain models with fixed data
python src/scripts/ml_validation_clean.py

# Step 3: Verify new label distribution
import json
with open('src/outputs/data/ml_validation_report.json') as f:
    report = json.load(f)
    print(report['label_distribution'])
    # Should show 4 classes now
```

### If Fraud Rare But Valid: Accept & Retrain

```python
# Step 1: Understand new distribution
# Might be: NONE 95%, ACCOUNTING 2%, DATA 2%, FRAUD 1%

# Step 2: Adjust SMOTE parameters for rare fraud
from imblearn.over_sampling import SMOTE
smote = SMOTE(k_neighbors=3, random_state=42)  # Reduce k for rare class
X_resampled, y_resampled = smote.fit_resample(X_train, y_train)

# Step 3: Lower confidence thresholds for fraud detection
# Be more aggressive in identifying potential fraud
```

---

## PHASE 4: VALIDATION (48 HOURS)

### If Fraud Cases Found

**New Model Performance:**
- F1 will be < 1.0 (realistic)
- Fraud precision/recall important
- Expected F1 for fraud: 0.70-0.90 (realistic range)

**Tests:**
1. ✅ Fraud precision: How many predicted frauds are actual?
2. ✅ Fraud recall: How many frauds do we find?
3. ✅ ROC curve: Trade-off between detection and false positives
4. ✅ Confusion matrix: All 4 classes represented

**Acceptance Criteria:**
- Fraud recall > 70% (find 7 of 10 frauds)
- Fraud precision > 80% (correctly identify fraud 8/10 times)
- ROC AUC > 0.85 (good discrimination)
- No data leakage detected

---

### If Fraud Cases Not Found

**Accept Current State:**
```
Project successfully validates:
✅ 3-class anomaly detection (ACCOUNTING, DATA, NONE)
✅ Data quality checks
✅ Unusual transaction patterns
⚠️ Cannot detect INVOICED_NOT_DELIVERED (doesn't exist)
```

**Deployment Caveat:**
- Document that fraud class doesn't exist in historical data
- Alert system if new fraud pattern emerges
- Plan to retrain if frauds found in future

---

## PHASE 5: PRODUCTION PREP (72 HOURS)

### Once Models Validated

**Setup Monitoring:**
```python
# Monitor 4 things:
1. Model performance drift (compare new predictions to baseline)
2. Data distribution shift (feature distributions changing)
3. Fraud detection rate (% transactions flagged)
4. False positive rate (legitimate transactions flagged)
```

**Create Alerts:**
- If fraud detection drops below 70% threshold
- If false positives exceed 5% threshold
- If data distribution shifts significantly
- If new label patterns appear

**Runbook Creation:**
- How to retrain if model drifts
- How to investigate false positives
- How to handle new fraud types
- How to rollback if issues found

---

## TIMELINE SUMMARY

| Phase | Duration | Owner | Status |
|-------|----------|-------|--------|
| **1. Root Cause** | 24h | Cross-team | ⏳ START HERE |
| **2. Decision** | 0h | Review | ⏳ AFTER PHASE 1 |
| **3. Fix/Retrain** | 48-72h | Data Science | ⏳ AFTER PHASE 2 |
| **4. Validate** | 48h | Data Science | ⏳ AFTER PHASE 3 |
| **5. Production** | 72h | DevOps + ML | ⏳ AFTER PHASE 4 |
| **TOTAL** | ~10 days | | 🔄 IN PROGRESS |

---

## WHAT TO DO RIGHT NOW (TODAY)

### Priority 1: Start Root Cause Analysis
**Owner:** Whoever is reading this

```python
# Run this TODAY:
import pandas as pd

raw = pd.read_csv("src/data/raw/Documents1.csv")
processed = pd.read_csv("src/data/processed/ml_features_phase2_y.csv")

# Question 1: Do frauds exist in raw data?
fraud_in_raw = (
    (raw['has_ir'] == 1) & 
    (raw['has_gr'] == 0)
).sum()

# Question 2: What's the processed distribution?
import json
with open('src/outputs/data/ml_validation_report.json') as f:
    report = json.load(f)
    print("Processed labels:", report['label_distribution'])

print(f"Potential frauds in raw: {fraud_in_raw}")
print(f"Frauds in processed: {report['label_distribution'].get('INVOICED_NOT_DELIVERED', 0)}")

if fraud_in_raw > 0 and report['label_distribution'].get('INVOICED_NOT_DELIVERED', 0) == 0:
    print("\n>>> ISSUE: Fraud cases lost during processing!")
    print(">>> FIX: Review RuleEngine and data processing pipeline")
```

### Priority 2: Meeting with Stakeholders
**Owner:** Project Manager

Discuss:
1. Where are fraud cases in actual SAP system?
2. Has anyone validated fraud detection needed?
3. What's the business impact of missing fraud detection?
4. Decision: Can we proceed with 3-class model or must we find frauds?

### Priority 3: Schedule Debugging Session
**Owner:** Data Science + SAP Team

When: Today or tomorrow  
Duration: 4 hours  
Goal: Determine root cause and next steps

---

## DECISION TREE

```
START HERE: Do fraud cases exist in raw data?
│
├─ YES (fraud_in_raw > 0)
│  └─ Problem is in PROCESSING
│     ├─ Fix RuleEngine OR
│     ├─ Fix feature engineering OR
│     └─ Fix aggregation logic
│     └─ THEN: Retrain models (Phase 3)
│
└─ NO (fraud_in_raw == 0)
   └─ Problem is in DATA or BUSINESS LOGIC
      ├─ Fraud prevents in SAP? 
      │  └─ Accept and deploy 3-class model
      ├─ Fraud exists elsewhere?
      │  └─ Get additional data source
      └─ Fraud definition wrong?
         └─ Revise business requirements
```

---

## RISK MATRIX

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Fraud cases lost in processing | HIGH | CRITICAL | Phase 1a diagnosis |
| Fraud doesn't exist in business | MEDIUM | HIGH | Phase 1d validation |
| Data is incomplete | LOW | HIGH | Phase 1b investigation |
| Models overfit on 3 classes | HIGH | MEDIUM | Retrain with correct data |
| Deployment blocked forever | LOW | CRITICAL | Timeline discipline |

---

## SUCCESS CRITERIA

**Phase 1 Success:**
- ✅ Root cause identified
- ✅ Stakeholders agree on path forward
- ✅ No blockers to Phase 2

**Phase 2 Success:**
- ✅ Decision made (fraud found vs fraud doesn't exist)
- ✅ Action plan confirmed
- ✅ Resources allocated

**Phase 3 Success:**
- ✅ Data fixed or processed correctly
- ✅ Models retrained
- ✅ New validation report generated

**Phase 4 Success:**
- ✅ Fraud detection validated (if applicable)
- ✅ Performance realistic and acceptable
- ✅ Stakeholder sign-off received

**Phase 5 Success:**
- ✅ Monitoring configured
- ✅ Alerts tested
- ✅ Runbooks documented
- ✅ Ready for production deployment

---

## BLOCKERS PREVENTING DEPLOYMENT

| Blocker | Severity | Resolution |
|---------|----------|-----------|
| No fraud cases in training data | CRITICAL | Find root cause (Phase 1) |
| Can't validate fraud detection | CRITICAL | Must have test cases (Phase 4) |
| Perfect model scores suspicious | HIGH | Retrain with real fraud (Phase 3) |
| Monitoring not setup | HIGH | Setup before deployment (Phase 5) |

---

## NEXT IMMEDIATE ACTION

**READ THIS:**
- [ML_VALIDATION_REPORT_FINAL.md](ML_VALIDATION_REPORT_FINAL.md) - Detailed technical analysis
- [ML_VALIDATION_EXECUTIVE_SUMMARY.md](ML_VALIDATION_EXECUTIVE_SUMMARY.md) - Executive overview

**DO THIS TODAY:**
1. Run diagnostic Python script (see Priority 1 above)
2. Schedule 1-hour meeting with SAP expert
3. Document findings in this action plan
4. Decide: Which scenario (A, B1, B2, B3)?

**BY TOMORROW:**
- Root cause identified
- Phase 2 decision made
- Phase 3 timeline set

---

**Action Plan Status:** READY TO EXECUTE  
**Prepared:** May 27, 2026  
**Next Review:** 24 hours (after Phase 1)
