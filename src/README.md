# 🎓 PFE - Analyse Avancée des Données d'Achat

**Objectif:** Détection d'anomalies et clustering de fournisseurs

---

## 📂 Structure

```
src/
├── notebooks/           # Jupyter Notebooks interactifs
│   ├── 00_starter_diagnostics.ipynb       (Diagnostic)
│   ├── 01_eda_complete.ipynb              (925 KB - EDA COMPLÈTE!)
│   ├── 02_ml_anomalies.ipynb              (Détection anomalies)
│   ├── 03_ml_clustering.ipynb             (Clustering fournisseurs)
│   └── 04_data_fusion.ipynb               (Fusion données)
│
├── scripts/             # Modules Python ML (réutilisables)
│   ├── model_anomaly.py                   (Classe AnomalyDetector)
│   ├── model_clustering.py                (Classe SupplierClustering)
│   ├── utils.py                           (Fonctions utilitaires)
│   └── 03_risk_metrics_engine.py          (Métriques risque)
│
├── data/                # Données (brutes et traitées)
│   ├── raw/             (Données originales - 15.9 MB)
│   ├── processed/       (CSV nettoyées)
│   ├── data-fusion/     (Fusion données)
│   ├── data_cleaning/   (Historique nettoyage)
│   └── data_fuss/       (Données filtrées)
│
└── README.md            (Ce fichier)
```

---

## 🚀 Démarrage Rapide

### 1️⃣ **Diagnostic Initial** (5 mins)
```bash
jupyter notebook notebooks/00_starter_diagnostics.ipynb
```
Résultat: Profil rapide des données

### 2️⃣ **Exploration Complète** (15-20 mins)
```bash
jupyter notebook notebooks/01_eda_complete.ipynb
```
Résultat: Statistiques + graphiques + corrélations (925 KB)

### 3️⃣ **Détection d'Anomalies** (30 mins)
```bash
jupyter notebook notebooks/02_ml_anomalies.ipynb
```

**Ce qu'il fait:**
```python
from scripts.model_anomaly import AnomalyDetector

detector = AnomalyDetector(contamination=0.05)  # 5% d'anomalies
detector.fit(df)
detector.predict(df)
detector.zscore_detection(df)
detector.iqr_detection(df)
results = detector.get_summary()
results.to_csv('anomalies_detected.csv')
```

**Résultats:** CSV avec anomalies flaggées

### 4️⃣ **Segmentation Fournisseurs** (30 mins)
```bash
jupyter notebook notebooks/03_ml_clustering.ipynb
```

**Ce qu'il fait:**
```python
from scripts.model_clustering import SupplierClustering

clustering = SupplierClustering()
features = clustering.create_supplier_features(df, 'Supplier', 'Amount')
X_scaled = clustering.prepare_data(features)
clustering.fit(X_scaled, n_clusters=3)
results = clustering.label_clusters()
results.to_csv('suppliers_segmented.csv')
```

**Résultats:** CSV avec clusters (Tier1, Tier2, Tier3)

### 5️⃣ **Fusion de Données** (Variable)
```bash
jupyter notebook notebooks/04_data_fusion.ipynb
```
Fusionne plusieurs sources

---

## 🔧 Modules Python

### **model_anomaly.py**

```python
class AnomalyDetector:
    """Détecte les anomalies via 3 méthodes"""
    
    def fit(df)              # Entraîner
    def predict(df)          # Prédire anomalies
    def zscore_detection(df) # Détection Z-score
    def iqr_detection(df)    # Détection par quartiles
    def consistency_check(df) # Validation métier
    def get_summary()        # Résumé détaillé
```

### **model_clustering.py**

```python
class SupplierClustering:
    """Segmente les fournisseurs"""
    
    def create_supplier_features()  # Features par supplier
    def prepare_data()              # Normalisation
    def find_optimal_k()            # Elbow method
    def fit(n_clusters)             # K-Means
    def predict()                   # Prédictions
    def get_cluster_profiles()      # Profils clusters
    def label_clusters()            # Tier labeling
```

### **utils.py**

```python
load_data(path)        # Charger CSV
save_data(df, path)    # Sauvegarder
save_fig(fig, path)    # Sauvegarder graphique
get_profile(df)        # Profil rapide
log_step(num, desc)    # Log formaté
export_report(data)    # Export JSON/CSV
```

---

## 📊 Données

| Chemin | Contenu | Usage |
|--------|---------|-------|
| `data/raw/` | CSV brutes Ariba | Source |
| `data/processed/` | CSV nettoyées | Analyse |
| `data/data-fusion/` | Données fusionnées | Optional |
| `data/data_cleaning/` | Étapes de nettoyage | Reference |

---

## 📋 Résultats Attendus

Après exécution complète:

```
outputs/
├── anomalies_detected.csv        # Anomalies flaggées
├── suppliers_segmented.csv       # Fournisseurs en clusters
├── eda_report.html              # Rapport EDA
├── clustering_profiles.csv       # Profils clusters
└── visualizations/
    ├── anomalies_plot.png
    ├── clustering_dendrogram.png
    └── correlation_heatmap.png
```

---

## 🔄 Flux d'Exécution

```
1. Charger données (raw CSV)
     ↓
2. Diagnostic (00_starter_diagnostics)
     ↓
3. EDA complète (01_eda_complete)
     ↓
     ├→ Détection anomalies (02_ml_anomalies)
     │    ├ Isolation Forest
     │    ├ Z-score
     │    └ IQR
     │
     └→ Segmentation fournisseurs (03_ml_clustering)
          ├ Features engineering
          ├ Elbow method
          ├ K-Means
          └ Tier labeling
     ↓
4. Exporter résultats CSV
     ↓
5. (Optional) Fusion données (04_data_fusion)
```

---

## 📚 Documentation

- [Model Anomaly](scripts/model_anomaly.py) - Détection d'anomalies
- [Model Clustering](scripts/model_clustering.py) - Segmentation fournisseurs
- [Utils](scripts/utils.py) - Fonctions utilitaires

---

## 🛠️ Installation

```bash
pip install -r requirements.txt
jupyter notebook
```

**Dépendances essentielles:**
- pandas, numpy, scipy
- scikit-learn (Isolation Forest, K-Means)
- matplotlib, seaborn, plotly
- jupyter

---

## ✅ Checklist

- [ ] Données brutes chargées dans `data/raw/`
- [ ] Notebook 00 exécuté (diagnostic)
- [ ] Notebook 01 exécuté (EDA)
- [ ] Notebook 02 exécuté (anomalies)
- [ ] Notebook 03 exécuté (clustering)
- [ ] Résultats CSV générés
- [ ] Visualisations créées

---

**Date:** 04 Mai 2026  
**Statut:** ✅ OPÉRATIONNEL
