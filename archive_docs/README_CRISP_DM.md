# 🚀 SAP P2P ANOMALY DETECTION PIPELINE

**A comprehensive Data Science solution for detecting procurement anomalies in SAP using CRISP-DM methodology**

---

## 📋 TABLE OF CONTENTS

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Pipeline Phases](#pipeline-phases)
- [Usage Guide](#usage-guide)
- [Configuration](#configuration)
- [Contributing](#contributing)

---

## 📊 PROJECT OVERVIEW

### Problem Statement
Detect anomalies in SAP Procure-to-Pay (P2P) process where:
- **GR (Goods Receipt)** and **IR (Invoice Receipt)** should be matched
- Unmatched transactions indicate:
  - 🚨 **Fraud Risk:** IR without GR (invoice without delivery)
  - ⚠️ **Accounting Risk:** GR without IR (goods not yet invoiced)
  - 💰 **Financial Risk:** Amount discrepancies between GR and IR

### Solution Approach

**Two-Phase Detection:**
1. **Phase 1: Rule-Based Detection** - Apply business logic to detect anomalies
2. **Phase 2: ML Classification** - Train models to detect patterns and edge cases

### Key Metrics
- ✅ **Accuracy:** >85%
- ✅ **Fraud Detection:** >90% recall
- ✅ **False Positives:** <10%
- ✅ **Processing:** 100K+ transactions

---

## 🏗️ ARCHITECTURE

### CRISP-DM Phases

```
01. Business Understanding      Define problem, objectives, KPIs
    ↓
02. Data Understanding & EDA    Explore data, quality assessment
    ↓
03. Data Preparation            Clean, aggregate, validate
    ↓
04. Feature Engineering         Create features, label anomalies
    ↓
05. Rule-Based Detection        Apply SAP business rules
    ↓
06. Modeling                    Train ML models (4 algorithms)
    ↓
07. Evaluation                  Validate performance, compare models
    ↓
08. Deployment                  Deploy pipeline, monitoring
```

### Tech Stack

| Component | Technology |
|-----------|------------|
| **Language** | Python 3.10+ |
| **Data** | Pandas, NumPy |
| **Visualization** | Matplotlib, Seaborn |
| **ML** | Scikit-learn, XGBoost, LightGBM |
| **Imbalance Handling** | SMOTE (imblearn) |
| **Notebook** | Jupyter |

---

## ⚡ QUICK START

### 1. Environment Setup

```bash
# Navigate to project
cd /path/to/IDP-Monitoring-Project

# Activate virtual environment
source env/bin/activate          # Linux/Mac
# or
env\Scripts\activate              # Windows

# Verify Python
python --version
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Pipeline (Sequential)

```bash
# Phase 1: Data Understanding
jupyter notebook src/notebooks/01_business_understanding.ipynb
jupyter notebook src/notebooks/02_data_understanding.ipynb

# Phase 2: Data Preparation
jupyter notebook src/notebooks/03_data_preparation.ipynb

# Phase 3: Feature Engineering & Labeling
jupyter notebook src/notebooks/04_feature_engineering.ipynb
jupyter notebook src/notebooks/05_rule_based_detection.ipynb

# Phase 4: Modeling
jupyter notebook src/notebooks/06_model_training.ipynb

# Phase 5: Evaluation
jupyter notebook src/notebooks/07_model_evaluation.ipynb

# Phase 6: Deployment
jupyter notebook src/notebooks/08_deployment_pipeline.ipynb
```

### 4. Quick Test (Python)

```python
from src.scripts.config import RAW_DATA_FILE
from src.scripts.sap_p2p_pipeline import SAPP2PPipeline

# Load and process data
pipeline = SAPP2PPipeline(data_dir='src/data', verbose=True)
df_raw = pipeline.load_data()
df_labeled = pipeline.apply_business_rules()
df_features = pipeline.create_features()

print(f"✅ Pipeline executed. Processed {len(df_features):,} transactions")
```

---

## 📁 PROJECT STRUCTURE

```
IDP-Monitoring-Project/
│
├── src/
│   ├── notebooks/                           # Jupyter notebooks (CRISP-DM phases)
│   │   ├── 01_business_understanding.ipynb  ← START HERE
│   │   ├── 02_data_understanding.ipynb
│   │   ├── 02b_eda_complete.ipynb          (Comprehensive EDA)
│   │   ├── 03_data_preparation.ipynb
│   │   ├── 04_feature_engineering.ipynb
│   │   ├── 05_rule_based_detection.ipynb   (Rule-based anomaly detection)
│   │   ├── 06_model_training.ipynb
│   │   ├── 07_model_evaluation.ipynb
│   │   └── 08_deployment_pipeline.ipynb
│   │
│   ├── scripts/                             # Python modules
│   │   ├── __init__.py
│   │   ├── config.py                        ⭐ Central configuration
│   │   ├── logger.py                        ⭐ Logging setup
│   │   ├── utils.py                         Utility functions
│   │   ├── rule_engine.py                   SAP business rules
│   │   ├── feature_engineering.py           Feature creation
│   │   ├── sap_p2p_pipeline.py             Main pipeline orchestration
│   │   │
│   │   ├── data/                            (Data handling)
│   │   │   ├── data_loader.py
│   │   │   ├── data_cleaner.py
│   │   │   └── data_validator.py
│   │   │
│   │   ├── models/                          (Model management)
│   │   │   ├── model_builder.py
│   │   │   ├── model_registry.py
│   │   │   └── model_evaluator.py
│   │   │
│   │   └── deployment/                      (Production pipeline)
│   │       ├── model_loader.py
│   │       ├── prediction_engine.py
│   │       └── monitoring.py
│   │
│   ├── data/
│   │   ├── raw/
│   │   │   └── Documents1.csv               ← INPUT: SAP export
│   │   ├── processed/
│   │   │   ├── ml_features_phase2_X.csv
│   │   │   ├── ml_features_phase2_y.csv
│   │   │   └── documents_with_labels_and_features_phase1.csv
│   │   ├── rule_based_labels/               (Phase 1 outputs)
│   │   └── risk_scores/                     (Risk calculations)
│   │
│   ├── models/                              (Trained models)
│   │   ├── logistic_regression_model.pkl
│   │   ├── random_forest_model.pkl
│   │   ├── xgboost_model.pkl
│   │   ├── lightgbm_model.pkl
│   │   └── model_registry.json
│   │
│   ├── outputs/                             (Results & reports)
│   │   ├── figures/                         (Visualizations)
│   │   ├── reports/                         (Analysis reports)
│   │   ├── predictions/                     (Batch predictions)
│   │   └── project_*.log                    (Log files)
│   │
│   └── docs/                                (Documentation)
│       ├── business_requirements.md
│       ├── sap_p2p_process.md
│       ├── architecture_guide.md
│       └── deployment_checklist.md
│
├── env/                                     (Virtual environment)
├── requirements.txt                         (Python dependencies)
├── PROJECT_RESTRUCTURING_PLAN.md            (This restructuring plan)
└── README.md                                (This file)
```

---

## 🔄 PIPELINE PHASES

### Phase 1: Business Understanding
**Goal:** Define problem and success criteria
- SAP P2P process overview
- Business objectives
- Anomaly types and risks
- Success metrics

### Phase 2: Data Understanding & EDA
**Goal:** Explore data structure and quality
- Data schema analysis
- GR/IR combination study
- Quality issues identification
- Statistical profiling

### Phase 3: Data Preparation
**Goal:** Clean and prepare data
- Remove invalid transactions
- Handle missing values
- Aggregate by PO+Item
- Data validation

### Phase 4: Feature Engineering & Labeling
**Goal:** Create features and label anomalies
- Apply SAP business rules
- Generate 30+ features
- Create anomaly labels
- Feature validation

**Outputs:**
- `ml_features_phase2_X.csv` - Features
- `ml_features_phase2_y.csv` - Labels
- `documents_with_labels_and_features_phase1.csv` - Complete dataset

### Phase 5: Modeling
**Goal:** Train ML models
- Test 4 algorithms: Logistic Regression, Random Forest, XGBoost, LightGBM
- Handle class imbalance (SMOTE)
- Cross-validation
- Hyperparameter tuning

### Phase 6: Evaluation
**Goal:** Assess model performance
- Test set metrics (Accuracy, Precision, Recall, F1, AUC)
- Confusion matrices
- ROC curves
- Feature importance
- Model comparison

### Phase 7: Deployment
**Goal:** Production-ready pipeline
- Model versioning
- Batch prediction
- Monitoring setup
- Retraining triggers

---

## 📖 USAGE GUIDE

### Running Individual Notebooks

1. **Start with Business Understanding**
```bash
cd src/notebooks
jupyter notebook 01_business_understanding.ipynb
```

2. **Then Data Understanding**
```bash
jupyter notebook 02_data_understanding.ipynb
```

3. **Continue sequentially through phases 03-08**

### Using Python Scripts

```python
from src.scripts.config import RAW_DATA_FILE
from src.scripts.sap_p2p_pipeline import SAPP2PPipeline
from src.scripts.logger import get_logger

logger = get_logger(__name__)

# Initialize pipeline
pipeline = SAPP2PPipeline(data_dir='src/data', verbose=True)

# Run all phases
df_raw = pipeline.load_data()
df_labeled = pipeline.apply_business_rules()
df_features = pipeline.create_features()
X, y, features = pipeline.select_ml_features()

logger.info(f"✅ Processed {len(df_features):,} transactions")
```

### Batch Prediction

```python
from src.scripts.deployment.prediction_engine import PredictionEngine

# Load production model
engine = PredictionEngine(model_path='src/models/best_model.pkl')

# Score new data
predictions = engine.predict_batch(new_data_csv='data/new_transactions.csv')

# Save results
predictions.to_csv('outputs/predictions/anomalies_detected.csv', index=False)
```

---

## ⚙️ CONFIGURATION

### Key Config Parameters

Edit `src/scripts/config.py`:

```python
# Data paths
RAW_DATA_FILE = "src/data/raw/Documents1.csv"
PROCESSED_DATA_DIR = "src/data/processed"

# Anomaly thresholds
ANOMALY_THRESHOLDS = {
    'amount_gap_pct': 5.0,        # Flag if >5% gap
    'high_risk_supplier': 0.20,   # Flag if >20% anomalies
    'days_threshold': 30,          # Flag if >30 days pending
}

# ML parameters
TEST_SIZE = 0.2
CV_FOLDS = 5
RANDOM_SEED = 42

# Model selection
MODELS_TO_TRAIN = ['logistic_regression', 'random_forest', 'xgboost', 'lightgbm']
```

### Environment Variables

```bash
# Set environment
export ENV=production              # or development, staging

# Set log level
export LOG_LEVEL=INFO              # or DEBUG, WARNING, ERROR
```

---

## 📊 KEY OUTPUTS

### After Phase 4 (Feature Engineering)
- `ml_features_phase2_X.csv` - Features matrix (4000+ rows × 30+ cols)
- `ml_features_phase2_y.csv` - Labels (OK, INCOMPLETE, DELIVERED_NOT_INVOICED)
- `documents_with_labels_and_features_phase1.csv` - Complete dataset with all columns

### After Phase 5 (Modeling)
- `src/models/logistic_regression_model.pkl`
- `src/models/random_forest_model.pkl`
- `src/models/xgboost_model.pkl`
- `src/models/lightgbm_model.pkl`
- `src/models/model_registry.json`

### After Phase 6 (Evaluation)
- `outputs/reports/model_comparison.json` - Performance metrics
- `outputs/figures/confusion_matrices/` - Confusion matrices
- `outputs/reports/metrics_report.md` - Detailed metrics

### Deployment
- Batch predictions in `outputs/predictions/`
- Monitoring dashboard in `outputs/monitoring/`

---

## 🔧 TROUBLESHOOTING

### Import Errors
```python
# Make sure to add scripts to path
import sys
sys.path.insert(0, '../scripts')

# Or install as package
pip install -e .
```

### Data Not Found
- Verify `Documents1.csv` exists in `src/data/raw/`
- Check `config.py` RAW_DATA_FILE path

### SMOTE Imbalance Error
- Ensure `imblearn` is installed: `pip install imbalanced-learn`
- Check minority class has >5 samples

### Out of Memory
- Process data in chunks
- Use LightGBM instead of XGBoost
- Reduce number of features

---

## 📚 DOCUMENTATION

Detailed documentation in `src/docs/`:
- `business_requirements.md` - Detailed business requirements
- `sap_p2p_process.md` - SAP P2P process documentation
- `architecture_guide.md` - Technical architecture
- `deployment_checklist.md` - Production deployment steps

---

## 👥 CONTRIBUTING

### Code Standards
- Follow PEP 8
- Use type hints
- Add docstrings
- Log important steps

### Adding Features
1. Update `config.py` with new constants
2. Implement in appropriate module
3. Add tests
4. Update documentation
5. Create PR

---

## 📝 CHANGELOG

### v1.0.0 (Current)
- ✅ Complete CRISP-DM restructuring
- ✅ Core infrastructure (config, logger)
- ✅ All 8 phase notebooks
- ✅ Rule-based detection
- ✅ 4 ML models
- ✅ Model registry & deployment

---

## 📞 SUPPORT

For issues or questions:
1. Check troubleshooting section
2. Review documentation in `src/docs/`
3. Check project logs in `outputs/project_*.log`

---

## 📄 LICENSE

Confidential - FORVIA Internal Use Only

---

**Last Updated:** May 19, 2026  
**Version:** 1.0.0  
**Maintained By:** Data Science Team
