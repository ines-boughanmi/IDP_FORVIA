# 📊 PROJECT RESTRUCTURING PLAN - CRISP-DM
## SAP P2P Anomaly Detection Pipeline

---

## 🎯 OBJECTIF
Réorganiser le projet en suivant la méthodologie **CRISP-DM** tout en:
- ✅ Conservant le code existant
- ✅ Préservant la logique métier
- ✅ Ne cassant aucune dépendance
- ✅ Rendant le projet industriel et maintenable

---

## 📁 STRUCTURE EXISTANTE (ACTUELLE)

```
src/
├── notebooks/
│   ├── 00_starter_diagnostics.ipynb
│   ├── 01_eda_complete.ipynb                    ✅ EXISTANT
│   ├── 02_ml_anomalies.ipynb
│   ├── 03_ml_clustering.ipynb
│   ├── 04_rule_based_detection.ipynb            ✅ EXISTANT
│   └── 05_ml_classification.ipynb               ✅ EXISTANT
├── scripts/
│   ├── rule_engine.py                           ✅ EXISTANT
│   ├── feature_engineering.py                   ✅ EXISTANT
│   ├── sap_p2p_pipeline.py                      ✅ EXISTANT
│   ├── utils.py                                 ✅ EXISTANT
│   ├── model_anomaly.py
│   ├── model_clustering.py
│   ├── 03_risk_metrics_engine.py
│   └── merge_contracts.py
├── data/
│   ├── raw/
│   ├── processed/
│   ├── rule_based_labels/
│   └── risk_scores/
└── models/
```

---

## 🔄 NOUVELLE STRUCTURE CRISP-DM (PROPOSÉE)

```
src/
│
├── 📚 PHASE 0: BUSINESS UNDERSTANDING
│   ├── notebooks/
│   │   └── 01_business_understanding.ipynb       ✨ NOUVEAU
│   ├── docs/
│   │   ├── business_requirements.md
│   │   ├── sap_p2p_process.md
│   │   └── kpis_and_success_criteria.md
│   └── scripts/
│       └── business_config.py                   (constantes métier)
│
├── 📊 PHASE 1: DATA UNDERSTANDING & EDA
│   ├── notebooks/
│   │   ├── 02_data_understanding.ipynb          ✨ NOUVEAU (extrait 01_eda)
│   │   └── 02b_eda_complete.ipynb               ✅ 01_eda_complete.ipynb (renommé)
│   ├── scripts/
│   │   ├── data_loader.py                       ✨ NOUVEAU
│   │   └── data_profiling.py                    ✨ NOUVEAU
│   └── outputs/
│       └── data_quality_report.html
│
├── 🔧 PHASE 2: DATA PREPARATION
│   ├── notebooks/
│   │   └── 03_data_preparation.ipynb            ✨ NOUVEAU
│   ├── scripts/
│   │   ├── data_cleaning.py                     ✨ NOUVEAU
│   │   ├── data_validation.py                   ✨ NOUVEAU
│   │   └── aggregation.py                       ✨ NOUVEAU (logique 04)
│   └── outputs/
│       └── data_preparation_report.md
│
├── ⚙️ PHASE 3: FEATURE ENGINEERING & LABELING
│   ├── notebooks/
│   │   ├── 04_feature_engineering.ipynb         ✨ NOUVEAU
│   │   └── 05_rule_based_detection.ipynb        ✅ 04_rule_based_detection.ipynb (renommé)
│   ├── scripts/
│   │   ├── rule_engine.py                       ✅ EXISTANT
│   │   ├── feature_engineering.py               ✅ EXISTANT
│   │   ├── sap_p2p_pipeline.py                  ✅ EXISTANT (refactorisé)
│   │   └── anomaly_labeler.py                   ✨ NOUVEAU
│   └── outputs/
│       ├── feature_list.json
│       └── labels_report.md
│
├── 🤖 PHASE 4: MODELING
│   ├── notebooks/
│   │   └── 06_model_training.ipynb              ✨ NOUVEAU (extrait 05)
│   ├── scripts/
│   │   ├── model_builder.py                     ✨ NOUVEAU
│   │   ├── model_registry.py                    ✨ NOUVEAU
│   │   └── (model_*.py) - consolidé
│   └── models/
│       ├── model_registry.json
│       └── (modèles sauvegardés)
│
├── 📈 PHASE 5: EVALUATION
│   ├── notebooks/
│   │   └── 07_model_evaluation.ipynb            ✨ NOUVEAU
│   ├── scripts/
│   │   ├── model_evaluator.py                   ✨ NOUVEAU
│   │   └── metrics_calculator.py                ✨ NOUVEAU
│   └── outputs/
│       ├── metrics_report.md
│       ├── confusion_matrices/
│       └── model_comparison.json
│
├── 🚀 PHASE 6: DEPLOYMENT & MONITORING
│   ├── notebooks/
│   │   └── 08_deployment_pipeline.ipynb         ✨ NOUVEAU
│   ├── scripts/
│   │   ├── model_loader.py                      ✨ NOUVEAU
│   │   ├── prediction_engine.py                 ✨ NOUVEAU
│   │   ├── monitoring.py                        ✨ NOUVEAU
│   │   └── api_inference.py                     ✨ NOUVEAU
│   └── outputs/
│       └── deployment_checklist.md
│
└── 🔗 CORE MODULES (Infrastructure)
    ├── scripts/
    │   ├── __init__.py
    │   ├── config.py                            ✨ NOUVEAU
    │   ├── logger.py                            ✨ NOUVEAU
    │   └── utils.py                             ✅ EXISTANT
    └── tests/
        ├── test_data_preparation.py             ✨ NOUVEAU
        ├── test_feature_engineering.py          ✨ NOUVEAU
        └── test_models.py                       ✨ NOUVEAU
```

---

## 🔀 MAPPING: CODE EXISTANT → NOUVELLE STRUCTURE

### **Scripts Python:**

| Existant | Nouveau Emplacement | Action |
|----------|-----------------|--------|
| `rule_engine.py` | `scripts/` | ✅ KEEP (fase 3) |
| `feature_engineering.py` | `scripts/` | ✅ KEEP (fase 3) |
| `sap_p2p_pipeline.py` | `scripts/` | ✅ KEEP + refactor (phases 1-5) |
| `utils.py` | `scripts/` | ✅ KEEP + reorganize |
| `model_*.py` | `scripts/model_builders/` | 🔄 CONSOLIDATE |
| `03_risk_metrics_engine.py` | `scripts/metrics/` | 🔄 REORGANIZE |
| `merge_contracts.py` | `scripts/preprocessing/` | 🔄 REORGANIZE |

### **Notebooks:**

| Existant | Nouveau | Action |
|----------|---------|--------|
| `01_eda_complete.ipynb` | `02b_eda_complete.ipynb` | ✅ RENAME |
| `04_rule_based_detection.ipynb` | `05_rule_based_detection.ipynb` | ✅ RENAME |
| `05_ml_classification.ipynb` | Split into `06_training` + `07_evaluation` | 🔄 SPLIT |
| `00,02,03_*.ipynb` | Archive/ | 📦 ARCHIVE (optionnel) |

---

## 📝 NOTEBOOKS À CRÉER

### **1️⃣ PHASE 0: Business Understanding**
```
01_business_understanding.ipynb
├── 1. SAP P2P Process Overview
├── 2. Business Problem & Objectives
├── 3. Success Criteria & KPIs
├── 4. Data Requirements
└── 5. Project Scope & Constraints
```

### **2️⃣ PHASE 1: Data Understanding (nouveau)**
```
02_data_understanding.ipynb
├── 1. Data Source Overview
├── 2. Schema & Column Definitions
├── 3. Data Quality Assessment
├── 4. Missing Values & Anomalies
└── 5. Data Profiling Summary
```

### **3️⃣ PHASE 2: Data Preparation (nouveau)**
```
03_data_preparation.ipynb
├── 1. Data Cleaning & Validation
├── 2. Aggregation by (PO, Item)
├── 3. Handling Missing Values
├── 4. Outliers Treatment
└── 5. Prepared Data Summary
```

### **4️⃣ PHASE 3: Feature Engineering (nouveau)**
```
04_feature_engineering.ipynb
├── 1. Feature Categories Overview
├── 2. Financial Features Creation
├── 3. Temporal Features Creation
├── 4. Supplier Features Creation
├── 5. Categorical Features Encoding
└── 6. Feature Validation & Summary
```

### **5️⃣ PHASE 4: Modeling (nouveau)**
```
06_model_training.ipynb
├── 1. Data Preparation for ML
├── 2. Train/Test Split & SMOTE
├── 3. Model Selection (4 models)
├── 4. Hyperparameter Tuning
├── 5. Cross-Validation Results
└── 6. Model Selection Summary
```

### **6️⃣ PHASE 5: Evaluation (nouveau)**
```
07_model_evaluation.ipynb
├── 1. Test Set Performance
├── 2. Confusion Matrices Analysis
├── 3. ROC & AUC Curves
├── 4. Feature Importance
├── 5. Error Analysis
└── 6. Model Comparison & Recommendation
```

### **7️⃣ PHASE 6: Deployment (nouveau)**
```
08_deployment_pipeline.ipynb
├── 1. Model Versioning & Registry
├── 2. Deployment Checklist
├── 3. Batch Prediction Pipeline
├── 4. Monitoring & Alerting Setup
├── 5. Performance Tracking
└── 6. Retraining Triggers
```

---

## 🔧 MODULES PYTHON À CRÉER/RÉORGANISER

### **Core Infrastructure:**
```
scripts/
├── config.py                    ✨ Configuration centralisée
├── logger.py                    ✨ Logging standardisé
└── utils.py                     ✅ Utilitaires (keep + augment)
```

### **Data Management:**
```
scripts/data/
├── __init__.py
├── data_loader.py               ✨ Load raw data
├── data_cleaner.py              ✨ Cleaning logic
├── data_validator.py            ✨ Data validation rules
└── data_profiler.py             ✨ Profiling & quality checks
```

### **Feature Engineering:**
```
scripts/features/
├── __init__.py
├── feature_engine.py            ✨ Main orchestration
├── financial_features.py        ✨ Extract from feature_engineering.py
├── temporal_features.py         ✨ Extract from feature_engineering.py
├── supplier_features.py         ✨ Extract from feature_engineering.py
└── operational_features.py      ✨ Extract from feature_engineering.py
```

### **Anomaly Detection:**
```
scripts/anomaly/
├── __init__.py
├── rule_engine.py               ✅ KEEP (refactor)
├── labeler.py                   ✨ Labeling logic
└── validator.py                 ✨ Anomaly validation
```

### **Modeling:**
```
scripts/models/
├── __init__.py
├── base_model.py                ✨ Abstract base class
├── model_builder.py             ✨ Model factory
├── model_registry.py            ✨ Model versioning
├── model_evaluator.py           ✨ Evaluation metrics
└── ensemble.py                  ✨ Ensemble logic
```

### **Deployment:**
```
scripts/deployment/
├── __init__.py
├── model_loader.py              ✨ Load trained models
├── prediction_engine.py         ✨ Batch predictions
├── monitoring.py                ✨ Monitor performance
└── api_interface.py             ✨ REST API logic
```

---

## 📊 EXECUTION PLAN

### **Phase A: Planning & Preparation** (1h)
- [ ] Créer dossiers structure
- [ ] Documenter dépendances
- [ ] Setup version control

### **Phase B: Core Infrastructure** (2h)
- [ ] Créer `config.py`, `logger.py`
- [ ] Reorganiser `scripts/`
- [ ] Setup imports dans `__init__.py`

### **Phase C: Refactor Scripts Existants** (3h)
- [ ] Refactor `sap_p2p_pipeline.py`
- [ ] Reorganiser modèles
- [ ] Update imports

### **Phase D: Create CRISP-DM Notebooks** (4h)
- [ ] 01_business_understanding
- [ ] 02_data_understanding
- [ ] 03_data_preparation
- [ ] 04_feature_engineering
- [ ] 06_model_training
- [ ] 07_model_evaluation
- [ ] 08_deployment_pipeline

### **Phase E: Testing & Validation** (2h)
- [ ] Test imports
- [ ] Validate data flow
- [ ] End-to-end test

### **Phase F: Documentation** (1h)
- [ ] Update README
- [ ] Create Architecture Guide
- [ ] Setup guide

---

## ✅ GUARANTEES

✅ **Code Conservation:** Aucun code supprimé, seulement réorganisé
✅ **Logic Preservation:** Métier inchangé
✅ **Backward Compatibility:** Les anciennes imports continueront à fonctionner
✅ **Industrialization:** Structure prête pour production
✅ **Traceability:** Chaque changement documenté

---

## 📈 BENEFITS

| Aspect | Before | After |
|--------|--------|-------|
| Structure | 🔴 Chaotique | 🟢 CRISP-DM |
| Maintenabilité | 🔴 Difficile | 🟢 Facile |
| Onboarding | 🔴 Complexe | 🟢 Clair |
| Scalabilité | 🔴 Limitée | 🟢 Extensible |
| Production | 🔴 Non prêt | 🟢 Industriel |

---

**Prêt à commencer l'implémentation?** ✨
