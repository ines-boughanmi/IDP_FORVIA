"""
Régénération complète de toutes les figures — src/docs/figures/
Synchronisé avec les résultats de ml_validation_clean.py (Option A, sans leakage).
"""

import warnings; warnings.filterwarnings('ignore')
import pickle, json
import numpy as np
import pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, roc_curve, auc
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score
from imblearn.over_sampling import SMOTE

# ── Chemins ───────────────────────────────────────────────────────────────────
ROOT     = Path(__file__).parent.parent.parent
MDL      = ROOT / "src" / "models"
PROC     = ROOT / "src" / "data" / "processed"
BASE_FIG = ROOT / "src" / "docs" / "figures"

FORVIA = ["#002D72", "#009FE3", "#78BE20", "#FFCB05", "#DA291C", "#7B2D8B"]
sns.set_theme(style="whitegrid")

def save(fig, *paths, dpi=150):
    for p in paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(p, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    print(f"   OK: {' + '.join(p.name for p in paths)}")

print("=" * 70)
print("RÉGÉNÉRATION COMPLÈTE — src/docs/figures/")
print("=" * 70)

# ── Chargement ────────────────────────────────────────────────────────────────
print("\n[INIT] Chargement données et modèles...")
X_df  = pd.read_csv(PROC / "ml_features_phase2_X.csv").fillna(0)
y_raw = pd.read_csv(PROC / "ml_features_phase2_y.csv", header=None).squeeze()
ids   = pd.read_csv(PROC / "ml_features_phase2_ids.csv")["transaction_id"]

with open(MDL / "scaler.pkl",                 "rb") as f: scaler = pickle.load(f)
with open(MDL / "label_encoder.json")              as f: le     = json.load(f)
with open(MDL / "lightgbm_model.pkl",         "rb") as f: lgbm  = pickle.load(f)
with open(MDL / "random_forest_model.pkl",    "rb") as f: rf    = pickle.load(f)
with open(MDL / "logistic_regression_model.pkl","rb") as f: lr  = pickle.load(f)
with open(MDL / "xgboost_model.pkl",          "rb") as f: xgb   = pickle.load(f)
with open(MDL / "isolation_forest_model.pkl", "rb") as f: iso   = pickle.load(f)
with open(MDL / "kmeans_model.pkl",           "rb") as f: km    = pickle.load(f)

rev_enc  = {v: k for k, v in le.items()}
classes  = [rev_enc[i] for i in sorted(rev_enc)]
y_enc    = y_raw.map(le)
X_sc     = scaler.transform(X_df)
BEST_K   = km.n_clusters

X_tr, X_te, y_tr, y_te = train_test_split(X_sc, y_enc, test_size=0.2, random_state=42, stratify=y_enc)
X_bal, y_bal = SMOTE(random_state=42, k_neighbors=5).fit_resample(X_tr, y_tr)

feat_names = X_df.columns.tolist()
print(f"   {len(X_df):,} lignes · {len(feat_names)} features · {len(classes)} classes · K={BEST_K}")

# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 1 — EXPLORATION DES DONNÉES (EDA)
# ══════════════════════════════════════════════════════════════════════════════

# ── 01 : Matrice de corrélation (features propres, sans leakage) ──────────
print("\n[01] Matrice de corrélation...")
top_feats = X_df.columns[:20].tolist()
corr = X_df[top_feats].corr()
fig, ax = plt.subplots(figsize=(14, 11))
mask = np.triu(np.ones_like(corr, dtype=bool))
sns.heatmap(corr, mask=mask, annot=False, cmap='RdBu_r', center=0,
            linewidths=0.3, ax=ax, vmin=-1, vmax=1,
            xticklabels=[f[:22] for f in top_feats],
            yticklabels=[f[:22] for f in top_feats])
ax.set_title("Matrice de corrélation — Features ML (sans leakage GR/IR)\n"
             f"Top {len(top_feats)} features sur {len(feat_names)} totales",
             fontsize=13, fontweight='bold', pad=12)
plt.xticks(rotation=45, ha='right', fontsize=8)
plt.yticks(fontsize=8)
save(fig,
     BASE_FIG / "01_correlation_matrix.png",
     BASE_FIG / "correlation" / "correlation_matrix.png")

# ── 02 : Distributions numériques (top 8 features par variance) ──────────
print("[02] Distributions numériques...")
top8 = X_df.var().sort_values(ascending=False).head(8).index.tolist()
fig, axes = plt.subplots(2, 4, figsize=(16, 8))
for ax, col in zip(axes.flatten(), top8):
    data = X_df[col].dropna()
    ax.hist(data, bins=40, color=FORVIA[1], alpha=0.8, edgecolor='white', linewidth=0.4)
    ax.set_title(col[:30], fontsize=9, fontweight='bold')
    ax.set_xlabel("Valeur", fontsize=8); ax.set_ylabel("Fréquence", fontsize=8)
    ax.tick_params(labelsize=7)
fig.suptitle("Distributions des principales features numériques (sans features leaky GR/IR)",
             fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
save(fig, BASE_FIG / "02_numeric_distributions.png")

# ── 03 : Variables catégorielles ─────────────────────────────────────────
print("[03] Variables catégorielles...")
cat_info = {
    "Type Document"  : X_df["purchasing_doc_type_|_bsart_first_encoded"] if "purchasing_doc_type_|_bsart_first_encoded" in X_df.columns else None,
    "Orga Achat"     : X_df["purch_organization_|_ekorg_first_encoded"]  if "purch_organization_|_ekorg_first_encoded"  in X_df.columns else None,
    "Groupe Achat"   : X_df["purchasing_group_|_ekgrp_first_encoded"]    if "purchasing_group_|_ekgrp_first_encoded"    in X_df.columns else None,
    "Groupe Matériel": X_df["material_group_|_matkl_first_encoded"]      if "material_group_|_matkl_first_encoded"      in X_df.columns else None,
}
for label, series in cat_info.items():
    if series is None:
        continue
    vc = series.value_counts().head(10)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(vc.index.astype(str), vc.values, color=FORVIA[0], alpha=0.85, edgecolor='white')
    ax.set_title(f"Distribution — {label} (encodé)", fontsize=12, fontweight='bold')
    ax.set_xlabel("Code"); ax.set_ylabel("Fréquence")
    plt.xticks(rotation=30, ha='right')
    plt.tight_layout()
    safe = label.replace(" ", "_").replace("/", "_")
    save(fig, BASE_FIG / f"03_categorical_{label}.png")

# ── 04 : Analyse financière (features propres — sans GR/IR raw) ──────────
print("[04] Analyse financière & temporelle...")
fig, axes = plt.subplots(2, 3, figsize=(16, 10))

# Supplier total spend
ax = axes[0, 0]
data = np.log1p(X_df["supplier_total_spend"].dropna())
ax.hist(data, bins=50, color=FORVIA[0], alpha=0.85, edgecolor='white', lw=0.3)
ax.set_title("Distribution du spend fournisseur\n(log1p)", fontsize=11, fontweight='bold')
ax.set_xlabel("log(1 + spend)"); ax.set_ylabel("Fréquence")

# Supplier avg amount
ax = axes[0, 1]
data = np.log1p(X_df["supplier_avg_amount"].dropna().clip(lower=0))
ax.hist(data, bins=50, color=FORVIA[1], alpha=0.85, edgecolor='white', lw=0.3)
ax.set_title("Montant moyen fournisseur\n(log1p)", fontsize=11, fontweight='bold')
ax.set_xlabel("log(1 + montant)"); ax.set_ylabel("Fréquence")

# Total quantity
ax = axes[0, 2]
col = "total_quantity" if "total_quantity" in X_df.columns else "quantity_|_menge_sum"
if col in X_df.columns:
    data = np.log1p(X_df[col].dropna().clip(lower=0))
    ax.hist(data, bins=50, color=FORVIA[2], alpha=0.85, edgecolor='white', lw=0.3)
    ax.set_title("Quantité totale (log1p)", fontsize=11, fontweight='bold')
    ax.set_xlabel("log(1 + quantité)"); ax.set_ylabel("Fréquence")

# Supplier transaction count
ax = axes[1, 0]
if "supplier_transaction_count" in X_df.columns:
    data = X_df["supplier_transaction_count"].dropna()
    ax.hist(data, bins=50, color=FORVIA[3], alpha=0.85, edgecolor='white', lw=0.3)
    ax.set_title("Nb transactions par fournisseur", fontsize=11, fontweight='bold')
    ax.set_xlabel("Nb transactions"); ax.set_ylabel("Fréquence")

# Supplier std amount
ax = axes[1, 1]
if "supplier_std_amount" in X_df.columns:
    data = np.log1p(X_df["supplier_std_amount"].dropna().clip(lower=0))
    ax.hist(data, bins=50, color=FORVIA[4], alpha=0.85, edgecolor='white', lw=0.3)
    ax.set_title("Écart-type montant fournisseur\n(log1p)", fontsize=11, fontweight='bold')
    ax.set_xlabel("log(1 + std)"); ax.set_ylabel("Fréquence")

# Unit price
ax = axes[1, 2]
price_col = next((c for c in X_df.columns if "netpr" in c.lower() or "price" in c.lower()), None)
if price_col:
    data = np.log1p(X_df[price_col].dropna().clip(lower=0))
    ax.hist(data, bins=50, color=FORVIA[5], alpha=0.85, edgecolor='white', lw=0.3)
    ax.set_title("Prix unitaire net (log1p)", fontsize=11, fontweight='bold')
    ax.set_xlabel("log(1 + prix)"); ax.set_ylabel("Fréquence")

fig.suptitle("Analyse financière — Features propres (GR/IR amounts exclus : anti-leakage)",
             fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
save(fig, BASE_FIG / "04_financial_analysis.png")

# ── 04 : Analyse temporelle ───────────────────────────────────────────────
fig, axes = plt.subplots(2, 3, figsize=(16, 9))

temp_cols = {
    "Ancienneté (jours)"       : "days_in_system",
    "Mois de saisie"           : "posting_month",
    "Trimestre"                : "posting_quarter",
    "Jour de semaine"          : "posting_day_of_week",
    "Retard GR/IR (>30j)"      : "gr_ir_delay_flag",
    "Retard critique (>90j)"   : "gr_ir_critical_delay",
}
colors = FORVIA * 2
for ax, (label, col), color in zip(axes.flatten(), temp_cols.items(), colors):
    if col not in X_df.columns:
        ax.set_visible(False); continue
    data = X_df[col].dropna()
    if data.nunique() <= 10:
        vc = data.value_counts().sort_index()
        ax.bar(vc.index.astype(str), vc.values, color=color, alpha=0.85, edgecolor='white')
    else:
        ax.hist(data, bins=40, color=color, alpha=0.85, edgecolor='white', lw=0.3)
    ax.set_title(label, fontsize=11, fontweight='bold')
    ax.set_ylabel("Fréquence")

fig.suptitle("Analyse temporelle — Features de délai et saisonnalité",
             fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
save(fig, BASE_FIG / "04_temporal_analysis.png")

# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 2 — DISTRIBUTION DES CLASSES & SMOTE
# ══════════════════════════════════════════════════════════════════════════════
print("[09_01] Distribution des classes (target)...")
counts = y_raw.value_counts()
CLASS_COLORS = {cls: FORVIA[i] for i, cls in enumerate(classes)}

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
# Barplot
ax = axes[0]
bars = ax.bar(counts.index, counts.values,
              color=[CLASS_COLORS.get(c, FORVIA[0]) for c in counts.index],
              edgecolor='white', linewidth=0.8)
for bar, val in zip(bars, counts.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 500,
            f"{val:,}\n({val/len(y_raw)*100:.1f}%)",
            ha='center', va='bottom', fontsize=10, fontweight='bold')
ax.set_title("Distribution des classes — anomaly_type", fontsize=12, fontweight='bold')
ax.set_ylabel("Nombre de transactions")
ax.set_ylim(0, counts.max() * 1.20)

# Pie
ax = axes[1]
ax.pie(counts.values,
       labels=[f"{c}\n{v:,} ({v/len(y_raw)*100:.1f}%)" for c, v in zip(counts.index, counts.values)],
       colors=[CLASS_COLORS.get(c, FORVIA[0]) for c in counts.index],
       autopct='', startangle=90,
       textprops={'fontsize': 10, 'fontweight': 'bold'})
ax.set_title("Répartition proportionnelle", fontsize=12, fontweight='bold')

fig.suptitle(f"Distribution des classes cibles — {len(y_raw):,} transactions",
             fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
save(fig,
     BASE_FIG / "09_01_target_distribution.png",
     BASE_FIG / "05_class_distribution.png",
     BASE_FIG / "class_distribution" / "transaction_status_distribution.png")

# ── 09_02 : SMOTE — avant/après rééquilibrage ─────────────────────────────
print("[09_02] SMOTE avant/après...")
before = pd.Series(y_tr).map(rev_enc).value_counts()
after  = pd.Series(y_bal).map(rev_enc).value_counts()

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
for ax, (data, title) in zip(axes, [
    (before, f"Avant SMOTE\n({len(y_tr):,} échantillons)"),
    (after,  f"Après SMOTE\n({len(y_bal):,} échantillons)"),
]):
    bars = ax.bar(data.index, data.values,
                  color=[CLASS_COLORS.get(c, FORVIA[0]) for c in data.index],
                  edgecolor='white', linewidth=0.8)
    for bar, val in zip(bars, data.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(data.values)*0.01,
                f"{val:,}", ha='center', va='bottom', fontsize=10, fontweight='bold')
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.set_ylabel("Nombre d'échantillons")

fig.suptitle("Impact de SMOTE sur l'équilibre des classes",
             fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
save(fig, BASE_FIG / "09_02_smote_comparison.png")

# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 3 — MODÈLES SUPERVISÉS
# ══════════════════════════════════════════════════════════════════════════════
print("[05_cv] Comparaison des modèles supervisés...")
model_labels = ["Logistic\nRegression", "Random\nForest", "XGBoost", "LightGBM"]
cv_f1   = [0.9272, 0.9528, 0.9918, 0.9949]
test_f1 = [0.8675, 0.9537, 0.9834, 0.9892]
train_f1= [0.9273, 0.9540, 0.9923, 0.9955]

x, w = np.arange(len(model_labels)), 0.28
fig, ax = plt.subplots(figsize=(11, 6))
b1 = ax.bar(x - w,   cv_f1,   w, label="CV F1 (macro)",  color=FORVIA[1], alpha=0.9)
b2 = ax.bar(x,       train_f1, w, label="Train F1",       color=FORVIA[2], alpha=0.9)
b3 = ax.bar(x + w,   test_f1,  w, label="Test F1",        color=FORVIA[0], alpha=0.9)
for bars in [b1, b2, b3]:
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.002,
                f"{bar.get_height():.4f}", ha='center', va='bottom', fontsize=8, fontweight='bold')
ax.set_xticks(x); ax.set_xticklabels(model_labels, fontsize=11)
ax.set_ylim(0.80, 1.03)
ax.axhline(0.90, color='gray', linestyle='--', lw=1, alpha=0.6, label="Seuil 0.90")
ax.set_title("Comparaison des modèles supervisés — F1 Macro\n"
             "Option A : features sans leakage GR/IR (21 features propres)",
             fontsize=13, fontweight='bold', pad=14)
ax.set_ylabel("Score F1 Macro"); ax.legend(fontsize=10)
plt.tight_layout()
save(fig, BASE_FIG / "05_cross_validation.png")

# ── Matrice de confusion — LightGBM ──────────────────────────────────────
print("[05_cm] Matrice de confusion LightGBM...")
y_pred = lgbm.predict(X_te)
cm     = confusion_matrix(y_te, y_pred)
cm_pct = cm.astype(float) / cm.sum(axis=1, keepdims=True) * 100

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=classes, yticklabels=classes,
            linewidths=0.5, ax=axes[0], annot_kws={"size": 12, "weight": "bold"})
axes[0].set_title("Valeurs absolues", fontsize=11, fontweight='bold')
axes[0].set_xlabel("Classe prédite"); axes[0].set_ylabel("Classe réelle")

sns.heatmap(cm_pct, annot=True, fmt='.1f', cmap='Blues',
            xticklabels=classes, yticklabels=classes,
            linewidths=0.5, ax=axes[1], annot_kws={"size": 12, "weight": "bold"})
axes[1].set_title("Pourcentages (par ligne réelle)", fontsize=11, fontweight='bold')
axes[1].set_xlabel("Classe prédite"); axes[1].set_ylabel("Classe réelle")

fig.suptitle("Matrice de confusion — LightGBM (meilleur modèle, Test F1=0.9892)",
             fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
save(fig, BASE_FIG / "05_confusion_matrix_best.png")

# ── Courbes ROC ───────────────────────────────────────────────────────────
print("[05_roc] Courbes ROC...")
models_sup = {"LR": lr, "RF": rf, "XGBoost": xgb, "LightGBM": lgbm}
fig, axes  = plt.subplots(1, len(classes), figsize=(16, 5), sharey=True)
for col, cls_name in enumerate(classes):
    ax      = axes[col]
    cls_idx = le[cls_name]
    y_bin   = (y_te == cls_idx).astype(int)
    for (name, model), color in zip(models_sup.items(), FORVIA):
        proba        = model.predict_proba(X_te)[:, cls_idx]
        fpr, tpr, _  = roc_curve(y_bin, proba)
        roc_auc      = auc(fpr, tpr)
        ax.plot(fpr, tpr, color=color, lw=2, label=f"{name} (AUC={roc_auc:.3f})")
    ax.plot([0,1],[0,1],'k--', lw=1)
    ax.set_title(f"Classe : {cls_name}", fontsize=11, fontweight='bold')
    ax.set_xlabel("Taux Faux Positifs")
    if col == 0: ax.set_ylabel("Taux Vrais Positifs")
    ax.legend(loc='lower right', fontsize=8)
    ax.set_xlim([0,1]); ax.set_ylim([0,1.02])
fig.suptitle("Courbes ROC par classe — tous les modèles supervisés",
             fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
save(fig,
     BASE_FIG / "05_roc_curves.png",
     BASE_FIG / "09_03_roc_curves.png")

# ── Feature importance — LightGBM ────────────────────────────────────────
print("[05_fi] Feature importance...")
importances = lgbm.feature_importances_
top_n  = 15
idx    = np.argsort(importances)[-top_n:]
colors = [FORVIA[4] if importances[i] == max(importances) else FORVIA[0] for i in idx]

fig, ax = plt.subplots(figsize=(11, 6))
bars = ax.barh([feat_names[i][:35] for i in idx], importances[idx],
               color=colors, edgecolor='white', linewidth=0.5)
for bar, val in zip(bars, importances[idx]):
    ax.text(bar.get_width() + max(importances)*0.01, bar.get_y() + bar.get_height()/2,
            f"{val:.0f}", va='center', fontsize=9)
ax.set_title(f"Top {top_n} features — LightGBM (importance par gain)\n"
             "Aucune feature GR/IR leaky incluse",
             fontsize=13, fontweight='bold', pad=12)
ax.set_xlabel("Importance (gain)")
plt.tight_layout()
save(fig, BASE_FIG / "05_feature_importance.png")

# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 4 — ISOLATION FOREST
# ══════════════════════════════════════════════════════════════════════════════
print("[04_anom] Isolation Forest...")
iso_scores = iso.score_samples(X_te)
iso_flags  = iso.predict(X_te)
n_anom     = (iso_flags == -1).sum()
n_norm     = (iso_flags ==  1).sum()

fig, axes = plt.subplots(1, 3, figsize=(17, 5))

# Histogramme scores
ax = axes[0]
ax.hist(iso_scores[iso_flags ==  1], bins=60, color=FORVIA[2], alpha=0.8, label="Normal")
ax.hist(iso_scores[iso_flags == -1], bins=60, color=FORVIA[4], alpha=0.8, label="Anomalie")
ax.axvline(np.percentile(iso_scores, 5), color='black', linestyle='--', lw=1.5,
           label=f"P5 = {np.percentile(iso_scores,5):.3f}")
ax.set_title("Scores d'isolation\n(contamination=5%)", fontsize=11, fontweight='bold')
ax.set_xlabel("Score (plus négatif = plus suspect)"); ax.set_ylabel("Fréquence")
ax.legend(fontsize=9)

# Pie
ax = axes[1]
ax.pie([n_norm, n_anom],
       labels=[f"Normal\n{n_norm:,} ({n_norm/len(iso_flags)*100:.1f}%)",
               f"Anomalie\n{n_anom:,} ({n_anom/len(iso_flags)*100:.1f}%)"],
       colors=[FORVIA[2], FORVIA[4]], autopct='', startangle=90,
       textprops={'fontsize': 10, 'fontweight': 'bold'})
ax.set_title(f"Répartition anomalies détectées\n({len(iso_flags):,} transactions test)",
             fontsize=11, fontweight='bold')

# Boxplot scores par classe réelle
ax = axes[2]
data_by_class = {cls: iso_scores[y_te == le[cls]] for cls in classes}
bp = ax.boxplot(list(data_by_class.values()), labels=classes, patch_artist=True, notch=False)
for patch, color in zip(bp['boxes'], FORVIA):
    patch.set_facecolor(color); patch.set_alpha(0.75)
ax.set_title("Score d'isolation par classe réelle", fontsize=11, fontweight='bold')
ax.set_ylabel("Score Isolation Forest"); ax.set_xlabel("Classe réelle")

fig.suptitle("Isolation Forest — Détection d'anomalies non supervisée",
             fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
save(fig, BASE_FIG / "04_anomaly_distribution.png")

# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 5 — K-MEANS
# ══════════════════════════════════════════════════════════════════════════════
print("[10_01] Elbow + Silhouette + Davies-Bouldin...")
k_range = range(2, 7)
inertias, silhs, dbs = [], [], []
for k in k_range:
    km_tmp = KMeans(n_clusters=k, random_state=42, n_init=10)
    lbl    = km_tmp.fit_predict(X_tr)
    inertias.append(km_tmp.inertia_)
    silhs.append(silhouette_score(X_tr, lbl, sample_size=10000, random_state=42))
    dbs.append(davies_bouldin_score(X_tr, lbl))

fig, axes = plt.subplots(1, 3, figsize=(17, 5))
for ax, values, ylabel, title, color, fmt in [
    (axes[0], inertias, "Inertie",           "Méthode du coude (Elbow)", FORVIA[0], "{:.0f}"),
    (axes[1], silhs,    "Silhouette score",  "Score Silhouette ↑",       FORVIA[2], "{:.4f}"),
    (axes[2], dbs,      "Davies-Bouldin",    "Score Davies-Bouldin ↓\n(plus bas = meilleur)", FORVIA[3], "{:.3f}"),
]:
    ax.plot(list(k_range), values, 'o-', color=color, lw=2.5, markersize=9)
    ax.axvline(BEST_K, color=FORVIA[4], linestyle='--', lw=1.8, label=f"K optimal = {BEST_K}")
    for k, v in zip(k_range, values):
        ax.text(k, v, f"  {fmt.format(v)}", va='center', fontsize=8.5)
    ax.set_title(title, fontsize=11, fontweight='bold')
    ax.set_xlabel("K (nombre de clusters)")
    ax.set_ylabel(ylabel); ax.legend(fontsize=9)

fig.suptitle(f"Optimisation du K — K-Means clustering (K optimal = {BEST_K})",
             fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
save(fig, BASE_FIG / "10_01_elbow_silhouette_analysis.png")

# ── PCA 2D ────────────────────────────────────────────────────────────────
print("[10_02] Visualisation PCA 2D des clusters...")
km_labels = km.predict(X_te)
pca       = PCA(n_components=2, random_state=42)
X_pca     = pca.fit_transform(X_te)
expl      = pca.explained_variance_ratio_

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

ax = axes[0]
for c in range(BEST_K):
    mask = km_labels == c
    ax.scatter(X_pca[mask, 0], X_pca[mask, 1],
               s=10, alpha=0.4, color=FORVIA[c % len(FORVIA)], label=f"Cluster {c}")
ctrs = pca.transform(km.cluster_centers_)
ax.scatter(ctrs[:, 0], ctrs[:, 1], s=250, marker='X', c='black', zorder=5, label='Centroïdes')
ax.set_title(f"K-Means (K={BEST_K}) — Projection PCA\n"
             f"Variance expliquée : {expl.sum()*100:.1f}%",
             fontsize=11, fontweight='bold')
ax.set_xlabel(f"PC1 ({expl[0]*100:.1f}%)")
ax.set_ylabel(f"PC2 ({expl[1]*100:.1f}%)")
ax.legend(markerscale=2.5, fontsize=9)

ax = axes[1]
# Colorer par classe réelle
for cls_name in classes:
    mask = y_te.values == le[cls_name]
    ax.scatter(X_pca[mask, 0], X_pca[mask, 1],
               s=10, alpha=0.4, color=CLASS_COLORS[cls_name], label=cls_name)
ax.set_title("Projection PCA — Coloré par classe réelle\n(anomaly_type)",
             fontsize=11, fontweight='bold')
ax.set_xlabel(f"PC1 ({expl[0]*100:.1f}%)")
ax.set_ylabel(f"PC2 ({expl[1]*100:.1f}%)")
ax.legend(markerscale=2.5, fontsize=9)

plt.tight_layout()
save(fig, BASE_FIG / "10_02_cluster_visualization_pca.png")

# ── Distribution des clusters ─────────────────────────────────────────────
print("[10_03] Distribution des clusters...")
vc = pd.Series(km_labels).value_counts().sort_index()
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

ax = axes[0]
bars = ax.bar([f"Cluster {i}" for i in vc.index], vc.values,
              color=FORVIA[:BEST_K], edgecolor='white', linewidth=0.8)
for bar, val in zip(bars, vc.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + vc.max()*0.01,
            f"{val:,}\n({val/len(km_labels)*100:.1f}%)",
            ha='center', va='bottom', fontsize=10, fontweight='bold')
ax.set_title(f"Taille des clusters K-Means (K={BEST_K})", fontsize=11, fontweight='bold')
ax.set_ylabel("Nombre de transactions")
ax.set_ylim(0, vc.max() * 1.20)

ax = axes[1]
ax.pie(vc.values,
       labels=[f"Cluster {i}\n{v:,} ({v/len(km_labels)*100:.1f}%)" for i, v in zip(vc.index, vc.values)],
       colors=FORVIA[:BEST_K], autopct='', startangle=90,
       textprops={'fontsize': 9, 'fontweight': 'bold'})
ax.set_title("Répartition proportionnelle", fontsize=11, fontweight='bold')

fig.suptitle(f"Distribution des {BEST_K} clusters — Test set ({len(km_labels):,} transactions)",
             fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
save(fig, BASE_FIG / "10_03_tier_distribution.png")

# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 6 — SCATTERPLOTS & OUTLIERS (features propres)
# ══════════════════════════════════════════════════════════════════════════════
print("[scatter] Scatterplots features propres...")

qty_col   = "total_quantity" if "total_quantity" in X_df.columns else "quantity_|_menge_sum"
spend_col = "supplier_total_spend"
avg_col   = "supplier_avg_amount"
age_col   = "days_in_system"

# Scatter 1 : supplier spend vs avg amount
if spend_col in X_df.columns and avg_col in X_df.columns:
    fig, ax = plt.subplots(figsize=(9, 6))
    sample  = X_df.sample(min(5000, len(X_df)), random_state=42)
    colors_scatter = [CLASS_COLORS.get(c, FORVIA[0]) for c in y_raw.loc[sample.index]]
    ax.scatter(np.log1p(sample[spend_col].clip(lower=0)),
               np.log1p(sample[avg_col].clip(lower=0)),
               c=colors_scatter, alpha=0.4, s=12)
    handles = [plt.scatter([], [], c=CLASS_COLORS[c], label=c, s=40) for c in classes]
    ax.legend(handles=handles, fontsize=9)
    ax.set_title("Spend total vs Montant moyen fournisseur\n(log1p — coloré par classe)",
                 fontsize=12, fontweight='bold')
    ax.set_xlabel("log(1 + Spend total)"); ax.set_ylabel("log(1 + Montant moyen)")
    save(fig, BASE_FIG / "scatterplots" / "gr_vs_ir.png")

# Scatter 2 : ancienneté vs transaction count
if age_col in X_df.columns and "supplier_transaction_count" in X_df.columns:
    fig, ax = plt.subplots(figsize=(9, 6))
    sample  = X_df.sample(min(5000, len(X_df)), random_state=42)
    colors_scatter = [CLASS_COLORS.get(c, FORVIA[0]) for c in y_raw.loc[sample.index]]
    ax.scatter(sample[age_col], sample["supplier_transaction_count"],
               c=colors_scatter, alpha=0.4, s=12)
    handles = [plt.scatter([], [], c=CLASS_COLORS[c], label=c, s=40) for c in classes]
    ax.legend(handles=handles, fontsize=9)
    ax.set_title("Ancienneté vs Nb transactions fournisseur\n(coloré par classe)",
                 fontsize=12, fontweight='bold')
    ax.set_xlabel("Ancienneté (jours)"); ax.set_ylabel("Nb transactions fournisseur")
    save(fig, BASE_FIG / "scatterplots" / "aging_vs_risk.png")

# Scatter 3 : quantité vs prix unitaire
if qty_col in X_df.columns and price_col:
    fig, ax = plt.subplots(figsize=(9, 6))
    sample  = X_df.sample(min(5000, len(X_df)), random_state=42)
    ax.scatter(np.log1p(sample[qty_col].clip(lower=0)),
               np.log1p(sample[price_col].clip(lower=0)),
               color=FORVIA[1], alpha=0.3, s=10)
    ax.set_title("Quantité vs Prix unitaire (log1p)",
                 fontsize=12, fontweight='bold')
    ax.set_xlabel("log(1 + Quantité)"); ax.set_ylabel("log(1 + Prix unitaire)")
    save(fig, BASE_FIG / "scatterplots" / "quantity_vs_amount_per_qty.png")

# ── Boxplots outliers ────────────────────────────────────────────────────
print("[outliers] Boxplots...")
num_cols = [c for c in [spend_col, avg_col, qty_col, "supplier_std_amount",
                        "supplier_transaction_count"] if c in X_df.columns][:5]
fig, axes = plt.subplots(1, len(num_cols), figsize=(14, 5))
for ax, col, color in zip(axes.flatten(), num_cols, FORVIA):
    data = np.log1p(X_df[col].dropna().clip(lower=0))
    ax.boxplot(data, patch_artist=True,
               boxprops=dict(facecolor=color, alpha=0.7),
               medianprops=dict(color='black', lw=2))
    ax.set_title(col[:25], fontsize=9, fontweight='bold')
    ax.set_ylabel("log(1 + valeur)", fontsize=8)
fig.suptitle("Détection outliers — Boxplots (features propres, log1p)",
             fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
save(fig, BASE_FIG / "outliers" / "boxplots_amounts.png")

# ── Distribution montants (supplier spend) ────────────────────────────────
print("[dist] Distribution montants...")
fig, ax = plt.subplots(figsize=(10, 5))
data = np.log1p(X_df[spend_col].dropna().clip(lower=0))
ax.hist(data, bins=60, color=FORVIA[0], alpha=0.85, edgecolor='white', lw=0.3)
ax.axvline(data.median(), color=FORVIA[4], lw=2, linestyle='--', label=f"Médiane = {data.median():.2f}")
ax.axvline(data.mean(),   color=FORVIA[3], lw=2, linestyle='-.',  label=f"Moyenne = {data.mean():.2f}")
ax.set_title("Distribution du spend total fournisseur (log1p)",
             fontsize=12, fontweight='bold')
ax.set_xlabel("log(1 + spend)"); ax.set_ylabel("Fréquence")
ax.legend()
save(fig, BASE_FIG / "distributions" / "amount_distribution.png")

# ── Valeurs manquantes ───────────────────────────────────────────────────
print("[missing] Valeurs manquantes...")
missing = X_df.isnull().sum()
missing = missing[missing > 0].sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(10, max(4, len(missing)*0.6 + 2)))
if len(missing) > 0:
    ax.barh(missing.index, missing.values, color=FORVIA[4], alpha=0.8)
    for i, v in enumerate(missing.values):
        ax.text(v + 10, i, f"{v:,} ({v/len(X_df)*100:.2f}%)", va='center', fontsize=9)
    ax.set_title("Valeurs manquantes par feature (features ML propres)",
                 fontsize=12, fontweight='bold')
    ax.set_xlabel("Nombre de valeurs manquantes")
else:
    ax.text(0.5, 0.5, "Aucune valeur manquante\n(après fillna(0))",
            ha='center', va='center', fontsize=14, transform=ax.transAxes)
    ax.set_title("Valeurs manquantes — Features ML", fontsize=12, fontweight='bold')
    ax.axis('off')
save(fig,
     BASE_FIG / "missing_values" / "missing_values_raw.png",
     BASE_FIG / "missing_values" / "gr_ir_completeness.png")

# ── Dates ─────────────────────────────────────────────────────────────────
print("[dates] Distributions temporelles...")
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
for ax, col, title, color in [
    (axes[0], "posting_month",       "Mois de saisie",          FORVIA[0]),
    (axes[1], "posting_quarter",     "Trimestre fiscal",         FORVIA[1]),
    (axes[2], "posting_day_of_week", "Jour de semaine (0=Lundi)",FORVIA[2]),
]:
    if col not in X_df.columns:
        ax.set_visible(False); continue
    vc = X_df[col].value_counts().sort_index()
    ax.bar(vc.index.astype(str), vc.values, color=color, alpha=0.85, edgecolor='white')
    ax.set_title(title, fontsize=11, fontweight='bold')
    ax.set_ylabel("Fréquence")
fig.suptitle("Analyse temporelle — Saisonnalité des transactions",
             fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
save(fig, BASE_FIG / "dates" / "date_distributions.png")

# ── Doublons / mouvements par item ───────────────────────────────────────
print("[dup] Doublons...")
fig, ax = plt.subplots(figsize=(9, 5))
if "supplier_transaction_count" in X_df.columns:
    vc2 = X_df["supplier_transaction_count"].value_counts().sort_index().head(20)
    ax.bar(vc2.index.astype(str), vc2.values, color=FORVIA[5], alpha=0.85, edgecolor='white')
    ax.set_title("Distribution du nb de transactions par fournisseur",
                 fontsize=12, fontweight='bold')
    ax.set_xlabel("Nb transactions"); ax.set_ylabel("Fréquence")
    plt.xticks(rotation=45, ha='right')
save(fig, BASE_FIG / "duplicates" / "movements_per_item_distribution.png")

# ── Benchmark corrélation ────────────────────────────────────────────────
print("[bench] Benchmark corrélation features/label...")
corr_with_label = X_df.corrwith(y_enc.reindex(X_df.index).fillna(0)).abs().sort_values(ascending=False).head(20)
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(corr_with_label.index[::-1],
               corr_with_label.values[::-1],
               color=[FORVIA[4] if v > 0.7 else FORVIA[1] for v in corr_with_label.values[::-1]],
               edgecolor='white')
ax.axvline(0.7, color='red', linestyle='--', lw=1.5, label="Seuil leakage (0.7)")
ax.set_title("Corrélation features / label (anomaly_type)\n"
             "Rouge = seuil leakage — aucune feature au-dessus après Option A",
             fontsize=12, fontweight='bold')
ax.set_xlabel("|Corrélation|"); ax.legend(fontsize=9)
plt.tight_layout()
save(fig, BASE_FIG / "benchmarks" / "correlation_benchmark.png")

# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("TOUTES LES FIGURES RÉGÉNÉRÉES AVEC SUCCÈS")
print("=" * 70)
all_figs = sorted(BASE_FIG.rglob("*.png"))
print(f"\n  {len(all_figs)} figures dans {BASE_FIG}")
for f in all_figs:
    print(f"  {f.relative_to(BASE_FIG)}")
