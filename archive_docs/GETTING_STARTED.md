# 🚀 GETTING STARTED - 5 MINUTES

**Quick reference to get the project running immediately**

---

## ⚡ THE FASTEST WAY

### 1. Setup (2 minutes)

```bash
# Navigate to project
cd /path/to/IDP-Monitoring-Project

# Activate environment
source env/bin/activate              # Linux/Mac
# or
env\Scripts\activate                 # Windows
```

### 2. Verify Data (1 minute)

```bash
# Check that raw data exists
ls src/data/raw/Documents1.csv

# If not found: 
# Copy Documents1.csv to src/data/raw/
```

### 3. Run Pipeline (2 minutes)

**Option A: Via Jupyter (Interactive)**
```bash
cd src/notebooks
jupyter notebook 01_business_understanding.ipynb
# Then run cells sequentially through each notebook
```

**Option B: Via Python Script (Automated)**
```bash
python -c "
import sys
sys.path.insert(0, 'src/scripts')
from sap_p2p_pipeline import SAPP2PPipeline

pipeline = SAPP2PPipeline(data_dir='src/data', verbose=True)
df = pipeline.load_data()
df = pipeline.apply_business_rules()
df = pipeline.create_features()
print('✅ Pipeline complete!')
"
```

---

## 📊 WHAT HAPPENS?

| Step | What | Output | Time |
|------|------|--------|------|
| 1 | Load data | 100K+ transactions | 1 min |
| 2 | Apply rules | Anomalies labeled | 2 min |
| 3 | Create features | 30+ features | 3 min |
| 4 | Export | CSV files ready | 1 min |

**Total:** ~7 minutes for full processing

---

## 📁 WHERE'S MY OUTPUT?

After running, find:

```
✅ src/data/processed/
   ├── ml_features_phase2_X.csv         (Features)
   ├── ml_features_phase2_y.csv         (Labels)
   └── documents_with_labels_and_features_phase1.csv

✅ src/outputs/
   ├── figures/                         (Visualizations)
   ├── reports/                         (Analysis)
   └── project_*.log                    (Logs)

✅ src/models/
   ├── logistic_regression_model.pkl
   ├── random_forest_model.pkl
   ├── xgboost_model.pkl
   └── lightgbm_model.pkl
```

---

## 🔍 WHAT'S IN THE PROJECT?

### Code Files (Keep - Already Optimized)
- ✅ `rule_engine.py` - SAP business rules
- ✅ `feature_engineering.py` - Feature creation
- ✅ `sap_p2p_pipeline.py` - Main orchestration
- ✅ `utils.py` - Utilities

### New Infrastructure
- ✨ `config.py` - Central configuration
- ✨ `logger.py` - Logging setup
- ✨ `__init__.py` - Package structure

### Notebooks (Organized by CRISP-DM)

| # | Notebook | Phase | Time |
|---|----------|-------|------|
| 01 | business_understanding | Phase 0 | 10 min |
| 02 | data_understanding | Phase 1 | 15 min |
| 03 | data_preparation | Phase 2 | 15 min |
| 04 | feature_engineering | Phase 3a | 30 min |
| 05 | rule_based_detection | Phase 3b | 30 min |
| 06 | model_training | Phase 4 | 30 min |
| 07 | model_evaluation | Phase 5 | 15 min |
| 08 | deployment_pipeline | Phase 6 | 10 min |

**Total execution time:** ~2.5-3 hours

---

## 🎯 RECOMMENDED FLOW FOR JURY

```
1. Show Business Understanding       (5 min)
   → Explain SAP P2P process
   → Show business problem
   → Explain success criteria

2. Show Rule-Based Detection         (10 min)
   → Run Phase 3-4
   → Show anomalies detected
   → Show statistics

3. Show ML Modeling                  (10 min)
   → Run Phase 5-6
   → Show model metrics
   → Show comparison

4. Show Results                       (5 min)
   → Show outputs directory
   → Show model registry
   → Show deployment ready
```

**Total presentation:** ~30 minutes

---

## ⚠️ COMMON ISSUES & FIXES

### Import Error
```python
# Add this at top of notebook
import sys
sys.path.insert(0, '../scripts')
```

### Data Not Found
```bash
# Make sure file exists
ls src/data/raw/Documents1.csv

# If missing, check original location and copy
```

### Out of Memory
```python
# Use LightGBM instead of XGBoost (faster, less RAM)
# Or process in chunks
```

### SMOTE Error
```python
# Check if minority class exists
y.value_counts()

# If <5 samples, SMOTE will fail
# Skip SMOTE or increase data
```

---

## 🔧 QUICK CONFIGURATION

Edit `src/scripts/config.py` to change:

```python
# Data paths
RAW_DATA_FILE = "src/data/raw/Documents1.csv"

# ML parameters
TEST_SIZE = 0.2
RANDOM_SEED = 42

# Models to train
MODEL_PARAMS = {
    'xgboost': { ... },      # ← Best performance
    'lightgbm': { ... },     # ← Fastest
    'random_forest': { ... },# ← Most interpretable
}

# Anomaly thresholds
ANOMALY_THRESHOLDS = {
    'amount_gap_pct': 5.0,   # Alert if >5% difference
    'high_risk_supplier': 0.20,  # >20% anomalies = risky
}
```

---

## 📖 DOCUMENTATION

For more details, read:

| Document | Purpose |
|----------|---------|
| [README_CRISP_DM.md](README_CRISP_DM.md) | Complete guide |
| [PROJECT_RESTRUCTURING_PLAN.md](PROJECT_RESTRUCTURING_PLAN.md) | Detailed plan |
| [MIGRATION_EXECUTION_GUIDE.md](MIGRATION_EXECUTION_GUIDE.md) | How to run |
| [src/docs/](src/docs/) | Specialized docs |

---

## ✅ CHECKLIST: Before Presenting

- [ ] Data file exists: `src/data/raw/Documents1.csv`
- [ ] Environment activated
- [ ] Notebooks runnable (no import errors)
- [ ] At least Phase 3 outputs generated
- [ ] Model files saved
- [ ] Logs created
- [ ] README reviewed
- [ ] Structure understood

---

## 🎓 FOR JURY PRESENTATION

### Key Points to Highlight

1. **Clear Structure**
   - "Following CRISP-DM methodology"
   - "8 phases, clearly documented"

2. **Existing Code Preserved**
   - "No code deleted, only reorganized"
   - "All business logic intact"

3. **Modular & Industrial**
   - "Configuration-driven"
   - "Logger integrated"
   - "Deployment-ready"

4. **Results**
   - Show Phase 3 anomalies detected
   - Show Phase 5 model performance
   - Show Phase 6 deployment pipeline

---

## 🚀 NEXT STEPS

1. **Run notebook 01:** See business context
2. **Run notebook 05:** See anomalies detected
3. **Run notebook 07:** See model performance
4. **Check outputs/:** See generated results
5. **Read README_CRISP_DM.md:** Deep dive

---

**Ready to start?**

```bash
cd src/notebooks
jupyter notebook 01_business_understanding.ipynb
```

✨ That's it! You're running CRISP-DM!

