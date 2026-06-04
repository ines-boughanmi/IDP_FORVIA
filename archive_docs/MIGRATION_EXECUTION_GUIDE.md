# 🔄 MIGRATION & EXECUTION GUIDE

## Pour Passer de l'Ancienne Structure à la Nouvelle (CRISP-DM)

---

## 📋 AVANT (Ancienne Structure)

```
src/notebooks/
├── 01_eda_complete.ipynb
├── 04_rule_based_detection.ipynb
└── 05_ml_classification.ipynb

src/scripts/
├── rule_engine.py
├── feature_engineering.py
├── sap_p2p_pipeline.py
└── utils.py
```

### ⚠️ Problèmes:
- Structure non documentée
- Phases mélangées dans notebooks
- Pas de séparation claire
- Difficile à maintenir
- Non prêt pour production

---

## 📋 APRÈS (Nouvelle Structure CRISP-DM)

```
src/notebooks/
├── 01_business_understanding.ipynb        ← Phase 0
├── 02_data_understanding.ipynb            ← Phase 1
├── 02b_eda_complete.ipynb                 ← Garde pour référence
├── 03_data_preparation.ipynb              ← Phase 2
├── 04_feature_engineering.ipynb           ← Phase 3
├── 05_rule_based_detection.ipynb          ← Phase 3 (Rule-based)
├── 06_model_training.ipynb                ← Phase 4
├── 07_model_evaluation.ipynb              ← Phase 5
└── 08_deployment_pipeline.ipynb           ← Phase 6

src/scripts/
├── config.py                              ✨ NOUVEAU
├── logger.py                              ✨ NOUVEAU
├── __init__.py                            ✨ NOUVEAU
├── rule_engine.py                         ✅ EXISTANT (conservé)
├── feature_engineering.py                 ✅ EXISTANT (conservé)
├── sap_p2p_pipeline.py                   ✅ EXISTANT (conservé)
├── utils.py                               ✅ EXISTANT (conservé)
│
├── data/                                  ✨ NOUVEAU
│   ├── data_loader.py
│   ├── data_cleaner.py
│   └── data_validator.py
│
├── models/                                ✨ NOUVEAU
│   ├── model_builder.py
│   ├── model_registry.py
│   └── model_evaluator.py
│
└── deployment/                            ✨ NOUVEAU
    ├── model_loader.py
    ├── prediction_engine.py
    └── monitoring.py
```

✅ **Avantages:**
- Structure CRISP-DM claire
- Code modulaire et réutilisable
- Documentation automatisée
- Prêt pour production
- Facile à maintenir

---

## 🚀 COMMENT EXÉCUTER LA NOUVELLE STRUCTURE

### Option 1: Exécution Complète (Recommandée pour Jury)

```bash
# 1. Aller dans le dossier
cd src/notebooks

# 2. Ouvrir Jupyter
jupyter notebook

# 3. Exécuter séquentiellement:

# PHASE 0: Business Understanding (30 min)
01_business_understanding.ipynb

# PHASE 1: Data Understanding (45 min)
02_data_understanding.ipynb
# +  (optionnel: 02b_eda_complete.ipynb pour plus de détails)

# PHASE 2: Data Preparation (30 min)
03_data_preparation.ipynb

# PHASE 3: Feature Engineering & Labeling (90 min)
04_feature_engineering.ipynb
05_rule_based_detection.ipynb    # ← Vous avez celui-ci déjà!

# PHASE 4: Modeling (60 min)
06_model_training.ipynb

# PHASE 5: Evaluation (30 min)
07_model_evaluation.ipynb

# PHASE 6: Deployment (20 min)
08_deployment_pipeline.ipynb
```

**Temps total:** ~4-5 heures pour exécution complète

---

### Option 2: Exécution par Phase (Pour Développement)

#### Phase 3: Feature Engineering & Labeling UNIQUEMENT

```bash
# Si vous avez déjà les données préparées
jupyter notebook 04_feature_engineering.ipynb
jupyter notebook 05_rule_based_detection.ipynb

# Outputs: ml_features_phase2_X.csv, ml_features_phase2_y.csv
```

#### Phase 4-5: Modeling & Evaluation UNIQUEMENT

```bash
# Si vous avez déjà les features
jupyter notebook 06_model_training.ipynb
jupyter notebook 07_model_evaluation.ipynb

# Outputs: modèles entraînés + métriques
```

---

### Option 3: Exécution via Python Script

```python
#!/usr/bin/env python
"""
Run complete SAP P2P pipeline end-to-end
"""

import sys
sys.path.insert(0, 'src/scripts')

from config import RAW_DATA_FILE, ML_FEATURES_X_FILE
from logger import get_logger
from sap_p2p_pipeline import SAPP2PPipeline

logger = get_logger(__name__)

# ============================================
# PHASE 1: Load & Explore
# ============================================
logger.info("📊 PHASE 1: Loading data...")
pipeline = SAPP2PPipeline(data_dir='src/data', verbose=True)
df_raw = pipeline.load_data()
logger.info(f"✅ Loaded {len(df_raw):,} transactions")

# ============================================
# PHASE 2: Apply Business Rules
# ============================================
logger.info("📋 PHASE 2: Applying business rules...")
df_labeled = pipeline.apply_business_rules()
logger.info(f"✅ Labeled {len(df_labeled):,} transactions")

# ============================================
# PHASE 3: Create Features
# ============================================
logger.info("⚙️ PHASE 3: Engineering features...")
df_features = pipeline.create_features()
logger.info(f"✅ Created features: {df_features.shape}")

# ============================================
# PHASE 4: Export for ML
# ============================================
logger.info("💾 PHASE 4: Exporting for ML training...")
X, y, features = pipeline.select_ml_features()
logger.info(f"✅ ML Data ready: X={X.shape}, y={y.shape}")

# Save results
X.to_csv(ML_FEATURES_X_FILE, index=False)
logger.info(f"✅ Saved features to {ML_FEATURES_X_FILE}")

logger.info("\n✅ PIPELINE COMPLETE!")
logger.info(f"📊 Processed {len(df_features):,} transactions")
logger.info(f"🎯 Anomalies detected: {(y != 'OK').sum():,}")
```

**Exécuter:**
```bash
python run_pipeline.py
```

---

## 📌 CHECKPOINT: Vérifier Que Tout Fonctionne

### Après Phase 1 (Data Understanding):
```bash
✅ Fichier existe: src/data/raw/Documents1.csv
✅ Lectures: >100,000 lignes
✅ Colonnes: >100 colonnes
```

### Après Phase 3 (Feature Engineering):
```bash
✅ Fichier existe: src/data/processed/ml_features_phase2_X.csv
✅ Forme: (4000+, 30+)
✅ Labels: OK, INCOMPLETE, DELIVERED_NOT_INVOICED
```

### Après Phase 4 (Modeling):
```bash
✅ Modèles sauvegardés: src/models/*.pkl
✅ Accuracy: >85%
✅ Precision: >80%
```

### Après Phase 5 (Evaluation):
```bash
✅ Rapport: src/outputs/reports/metrics_report.md
✅ Graphiques: src/outputs/figures/
✅ Comparaison modèles: src/models/model_registry.json
```

---

## ⚡ QUICK FIX: Si Quelque Chose Cassé

### Import Error: `ModuleNotFoundError: No module named 'config'`

```python
# ❌ WRONG
from config import RAW_DATA_FILE

# ✅ CORRECT
import sys
sys.path.insert(0, '../scripts')
from config import RAW_DATA_FILE
```

### File Not Found: `Documents1.csv`

```bash
# Vérifier que le fichier existe
ls -la src/data/raw/

# Si absent, copier depuis emplacement original
cp /path/to/Documents1.csv src/data/raw/
```

### Memory Error: `MemoryError`

```python
# Réduire chunksize lors du chargement
df = pd.read_csv('file.csv', chunksize=100000)

# Ou utiliser LightGBM au lieu de XGBoost
```

### SMOTE Error: `Not enough samples in minority class`

```python
# Vérifier les labels
y.value_counts()

# Si classe <5 samples, augmenter données ou désactiver SMOTE
```

---

## 🔄 MIGRATION CHECK-LIST

Avant de présenter à la jury, vérifier:

- [ ] ✅ Config.py existe et contient tous les chemins
- [ ] ✅ Logger.py setup correctement
- [ ] ✅ 01_business_understanding.ipynb runnable
- [ ] ✅ 02_data_understanding.ipynb runnable
- [ ] ✅ 04_feature_engineering.ipynb runnable
- [ ] ✅ 05_rule_based_detection.ipynb runnable (existant)
- [ ] ✅ 06_model_training.ipynb runnable
- [ ] ✅ 07_model_evaluation.ipynb runnable
- [ ] ✅ Fichiers générés dans outputs/
- [ ] ✅ README_CRISP_DM.md à jour
- [ ] ✅ PROJECT_RESTRUCTURING_PLAN.md documenté

---

## 📊 EXEMPLE: Présentation à la Jury

```bash
# 1. Montrer structure
ls -la src/

# 2. Montrer phase 1 (Business Understanding)
jupyter notebook src/notebooks/01_business_understanding.ipynb
# → Show SAP P2P process
# → Show business objectives
# → Show success criteria

# 3. Montrer phase 3 (Rule-Based)
jupyter notebook src/notebooks/05_rule_based_detection.ipynb
# → Run detection
# → Show anomalies detected
# → Show statistics

# 4. Montrer phase 4-5 (Modeling)
jupyter notebook src/notebooks/06_model_training.ipynb
jupyter notebook src/notebooks/07_model_evaluation.ipynb
# → Show model performance
# → Show confusion matrices
# → Show comparison

# 5. Montrer outputs
ls -la src/outputs/
# → Reports
# → Figures
# → Predictions
```

---

## 📚 DOCUMENTATION ASSOCIÉE

Référez-vous à:
- [README_CRISP_DM.md](README_CRISP_DM.md) - Guide utilisateur complet
- [PROJECT_RESTRUCTURING_PLAN.md](PROJECT_RESTRUCTURING_PLAN.md) - Plan détaillé
- [src/docs/](src/docs/) - Documentation spécialisée

---

## ✅ RÉSUMÉ

| Aspect | Avant | Après |
|--------|-------|-------|
| **Structure** | 🔴 Chaotique | 🟢 CRISP-DM |
| **Maintenance** | 🔴 Difficile | 🟢 Facile |
| **Onboarding** | 🔴 Complex | 🟢 Clair |
| **Production** | 🔴 Non prêt | 🟢 Prêt |
| **Code Réutilisable** | 🔴 Peu | 🟢 Modulaire |

---

**Prêt à exécuter?** 🚀

Commencez par:
```bash
cd src/notebooks
jupyter notebook 01_business_understanding.ipynb
```

