# 📋 SAP P2P PHASE 1: RULE-BASED DETECTION

## 🎯 Objectif Phase 1

Créer une **détection d'anomalies basée sur les règles métier SAP**, sans Machine Learning, pour:
- ✅ Générer des **labels fiables** pour la Phase 2 (ML supervisé)
- ✅ Détecter les anomalies **P2P (Procure-to-Pay)** métier
- ✅ Créer des **features** pour les modèles ML
- ✅ Produire des **rapports d'audit** conformes

---

## 📊 Architecture Phase 1

```
INPUT: Documents1.csv
   ↓
[RULE ENGINE]
├─ Filtrage (amount > 0)
├─ Agrégation (PO + Item)
├─ Détection GR/IR
├─ Classification anomalies
└─ Flags détaillés
   ↓
[FEATURE ENGINEERING]
├─ Features Financières (GR, IR, écarts)
├─ Features Temporelles (dates, délais)
├─ Features Fournisseurs (historique)
├─ Features Opérationnelles
└─ Features Catégorielles (encodage)
   ↓
[PIPELINE]
├─ Export labels
├─ Export features
└─ Statistiques
   ↓
OUTPUT:
├─ documents_with_labels_and_features.csv
├─ documents_labels.csv
├─ ml_features_phase2_X.csv
├─ ml_features_phase2_y.csv
└─ pipeline_statistics.txt
```

---

## 🔧 Modules Créés

### 1. **rule_engine.py**

Module de détection basée sur les règles SAP.

**Classes:**
- `RuleEngine`: Moteur de règles métier

**Méthodes principales:**

```python
from rule_engine import RuleEngine

engine = RuleEngine(verbose=True)

# Filtrer les transactions valides
df = engine.filter_valid_transactions(df)

# Agréger par (PO, Item)
df = engine.aggregate_by_po_item(df)

# Détecter GR et IR
df = engine.detect_gr_ir(df)

# Classifier les anomalies
df = engine.classify_anomalies(df)

# Ajouter flags détaillés
df = engine.add_anomaly_details(df)

# Calculer écarts montants
df = engine.calculate_amount_gaps(df)

# Pipeline complet
df = engine.detect_anomalies(df)
```

**Règles implémentées:**

| Règle | Condition | Résultat |
|-------|-----------|----------|
| Filtrage | amount > 0 & NOT deleted | Transactions valides |
| Agrégation | GROUP BY (PO, Item) | Clé métier |
| GR Detection | amount > 0 | has_gr = 1 |
| IR Detection | invoice_value > 0 | has_ir = 1 |
| Classification | has_gr, has_ir | Anomaly Label |
| Amount Gap | \|IR - GR\| | Écart détecté |

**Labels générés:**

| Label | Condition | Signification |
|-------|-----------|---------------|
| OK | has_gr=1, has_ir=1 | Flux normal |
| DELIVERED_NOT_INVOICED | has_gr=1, has_ir=0 | GR sans IR (comptable) |
| INVOICED_NOT_DELIVERED | has_gr=0, has_ir=1 | IR sans GR (fraude) |
| INCOMPLETE | has_gr=0, has_ir=0 | Données incomplètes |

**Sévérités:**

- 🚨 CRITICAL: INVOICED_NOT_DELIVERED (paiement sans réception)
- 🔴 HIGH: DELIVERED_NOT_INVOICED (facture manquante)
- 🟡 MEDIUM: INCOMPLETE
- ✅ NONE: OK

---

### 2. **feature_engineering.py**

Module de création des features pour ML.

**Classes:**
- `FeatureEngineer`: Ingénierie des features

**Catégories de features créées:**

#### A. Features Financières

```
- total_gr_amount         : Montant total GR
- total_ir_amount         : Montant total IR
- gr_ir_difference        : IR - GR
- abs_gr_ir_diff          : |IR - GR|
- invoice_ratio           : IR / GR
- unit_price              : Prix unitaire
- total_quantity          : Quantité totale
- amount_per_qty          : Montant par unité
- gr_ir_gap_pct           : Écart en %
- blocked_amount          : Montant bloqué
```

#### B. Features Temporelles

```
- posting_date            : Date comptable
- days_in_system          : Ancienneté (jours)
- posting_month           : Mois (saisonnalité)
- posting_quarter         : Trimestre fiscal
- posting_day_of_week     : Jour semaine
- posting_year            : Année
- gr_ir_delay_flag        : Retard > 30j
- gr_ir_critical_delay    : Retard > 90j
- planned_delay_days      : Délai planifié
```

#### C. Features Fournisseurs

```
- supplier_transaction_count    : Nb transactions
- supplier_total_spend          : Dépense totale
- supplier_avg_amount           : Montant moyen
- supplier_std_amount           : Écart-type
- supplier_anomaly_rate         : Taux anomalies
- supplier_avg_aging            : Ancienneté moyenne
- supplier_high_risk            : Flag risque (>20% anomalies)
- supplier_high_volume          : Flag volume élevé
```

#### D. Features Opérationnelles

```
- delivery_completed            : Livraison complète
- document_date_known           : Date connue
- has_outline_agreement         : Accord-cadre
- has_payment_terms             : Termes paiement
```

#### E. Features Catégorielles (Encodées)

```
- plant_|_werks_encoded         : Usine
- material_group_|_matkl_encoded: Groupe matériel
- purch_organization_|_ekorg_encoded: Org achat
- supplier_|_lifnr_encoded      : Fournisseur
- purchasing_doc_type_|_bsart_encoded: Type PO
```

**Utilisation:**

```python
from feature_engineering import FeatureEngineer

engineer = FeatureEngineer(verbose=True)

# Créer toutes les features
df = engineer.create_all_features(df, reference_date=None)

# Récupérer listes
numeric_features = engineer.get_numeric_features()
categorical_features = engineer.get_categorical_features()
all_features = engineer.get_feature_list()
```

---

### 3. **sap_p2p_pipeline.py**

Pipeline ETL complet orchestrant Rule Engine + Feature Engineering.

**Classes:**
- `SAPP2PPipeline`: Pipeline SAP P2P complet

**Utilisation:**

```python
from sap_p2p_pipeline import SAPP2PPipeline

# Initialiser
pipeline = SAPP2PPipeline(data_dir='../data', verbose=True)

# Exécuter pipeline complet
df_final, X, y, features = pipeline.run_full_pipeline()

# Ou étape par étape
df_raw = pipeline.load_data()
df_labels = pipeline.apply_business_rules()
df_features = pipeline.create_features()
X, y, features = pipeline.select_ml_features()
pipeline.export_results(suffix='_custom')
```

**Sorties:**

- `documents_with_labels_and_features_*.csv`: Dataset complet
- `documents_labels_*.csv`: Labels uniquement
- `pipeline_statistics_*.txt`: Statistiques
- `ml_features_phase2_X.csv`: Features pour ML
- `ml_features_phase2_y.csv`: Target pour ML

---

### 4. **utils.py** (Enrichi)

Helpers SAP P2P ajoutés:

```python
# Mapping colonnes SAP
mapping = get_sap_column_mapping()

# Description anomalies
desc = describe_anomaly('DELIVERED_NOT_INVOICED')

# Codes mouvements SAP
movements = get_sap_movement_types()

# Calcul risk score
score = calculate_anomaly_risk_score(row)

# Définitions KPI
kpis = get_kpi_definitions()
```

---

## 📓 Notebook 04: rule_based_detection.ipynb

**Contenu:**

1. **Imports & Setup** - Chargement modules
2. **Load & Explore** - Données brutes
3. **Apply Business Rules** - Rule Engine
4. **Anomaly Distribution** - Stats labels
5. **Anomaly Details** - Description par type
6. **Create Features** - Feature Engineering
7. **Financial Analysis** - Analyses montants
8. **Top Anomalies** - Cas critiques
9. **Supplier Analysis** - Fournisseurs
10. **Temporal Analysis** - Tendances dates
11. **Export & ML Features** - Préparation Phase 2
12. **Summary** - Résumé complet

**Visualisations générées:**

- `04_anomaly_distribution.png` - Distribution des anomalies
- `04_financial_analysis.png` - Analyses montants GR/IR
- `04_supplier_anomalies.png` - Top fournisseurs
- `04_temporal_analysis.png` - Tendances temporelles

---

## 🚀 Comment Exécuter Phase 1

### Option 1: Exécuter le notebook

```bash
cd src
jupyter notebook notebooks/04_rule_based_detection.ipynb
```

Puis exécuter toutes les cellules dans l'ordre.

### Option 2: Exécuter le pipeline en Python

```python
from scripts.sap_p2p_pipeline import SAPP2PPipeline

pipeline = SAPP2PPipeline(data_dir='./data', verbose=True)
df_final, X, y, features = pipeline.run_full_pipeline()
```

### Option 3: Exécution personnalisée

```python
from scripts.rule_engine import RuleEngine
from scripts.feature_engineering import FeatureEngineer

# Étape 1: Règles
engine = RuleEngine()
df = pd.read_csv('data/raw/Documents1.csv')
df = engine.detect_anomalies(df)

# Étape 2: Features
engineer = FeatureEngineer()
df = engineer.create_all_features(df)

# Étape 3: Export
df.to_csv('data/processed/results.csv', index=False)
```

---

## 📊 Sorties Phase 1

### Fichiers générés

```
data/
├── processed/
│   ├── documents_with_labels_and_features_*.csv  (Dataset complet)
│   ├── ml_features_phase2_X.csv                  (Features pour ML)
│   ├── ml_features_phase2_y.csv                  (Target pour ML)
│   └── pipeline_statistics_*.txt                 (Statistiques)
└── rule_based_labels/
    └── documents_labels_*.csv                    (Labels uniquement)

docs/figures/
├── 04_anomaly_distribution.png
├── 04_financial_analysis.png
├── 04_supplier_anomalies.png
└── 04_temporal_analysis.png
```

### Statistiques típiques

```
Total Transactions: 64,167
├─ OK: 55,201 (86.0%)
├─ DELIVERED_NOT_INVOICED: 6,382 (9.9%) ⚠️
├─ INVOICED_NOT_DELIVERED: 2,124 (3.3%) 🚨
└─ INCOMPLETE: 460 (0.7%)

Financial Impact:
├─ Total GR: $123,456,789
├─ Total IR: $119,234,567
└─ Blocked Amount: $4,222,222 💰

Features Created: 50+
├─ Numeric: 30
└─ Categorical: 20+
```

---

## ✅ Validation Phase 1

Avant de passer à Phase 2, vérifier:

- [ ] Notebook 04 exécuté sans erreurs
- [ ] Fichiers CSV générés dans `data/processed/`
- [ ] Visualisations sauvegardées dans `docs/figures/`
- [ ] Distribution labels vérifiée (86% OK vs 14% anomalies)
- [ ] Features ML générées (X et y chargés)
- [ ] Rapport statistiques généré

---

## 🔗 Phase 2 (Prochaine)

Une fois Phase 1 complétée:

1. **XGBoost Classification** - Modèles supervisés
2. **Model Comparison** - XGBoost vs LightGBM vs CatBoost
3. **Feature Importance** - Comprendre les drivers
4. **Cross-Validation** - Validation robuste
5. **Risk Scoring** - Scores de risque par transaction

**Input Phase 2:**
- `ml_features_phase2_X.csv`
- `ml_features_phase2_y.csv`

**Output Phase 2:**
- Modèles ML entraînés
- Prédictions sur test set
- Explications anomalies
- Risk scores

---

## 📚 Références

- **SAP P2P Process**: Purchase Order → Goods Receipt → Invoice Receipt → GR/IR Clearing
- **Anomalies Métier**: Incohérences GR/IR, fraude, retards
- **Rule-Based Approach**: Labels fiables pour ML supervisé

---

## 🎓 Notes Pédagogiques

Cette Phase 1 démontre:

✅ **Rule-Based Detection** - Approche métier avant ML
✅ **Feature Engineering** - Création features métier + temporelle
✅ **ETL Pipeline** - Orchestration complète
✅ **Business Value** - Détecte anomalies réelles SAP
✅ **Auditabilité** - Chaque anomalie a une règle explicable

Approche idéale pour contextes industriels comme **Forvia**!

