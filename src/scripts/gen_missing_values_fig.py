"""
Figure : valeurs manquantes sur les donnees brutes (Documents1.csv)
"""
import warnings; warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

ROOT = Path("src/docs/figures")
(ROOT / "missing_values").mkdir(parents=True, exist_ok=True)

print("Chargement Documents1.csv...")
df = pd.read_csv("src/data/raw/Documents1.csv", low_memory=False)
n = len(df)
print(f"  {n:,} lignes  x  {len(df.columns)} colonnes")

miss     = df.isnull().sum()
miss_pct = (miss / n * 100).round(2)
result   = pd.DataFrame({"missing": miss, "pct": miss_pct})
result   = result[result["missing"] > 0].sort_values("pct", ascending=True)


def short(col):
    if "|_" in col:
        return col.split("|_")[0].strip().replace("_", " ").title()
    return col.replace("_", " ").title()


result.index = [short(c) for c in result.index]

FORVIA = {"critique": "#DA291C", "modere": "#FFCB05", "faible": "#78BE20"}

def color(pct):
    if pct >= 50:
        return FORVIA["critique"]
    if pct >= 10:
        return FORVIA["modere"]
    return FORVIA["faible"]

colors = [color(v) for v in result["pct"]]

fig, axes = plt.subplots(1, 2, figsize=(15, 6),
                         gridspec_kw={"width_ratios": [2, 1]})

# ---- Barplot horizontal ----
ax = axes[0]
bars = ax.barh(result.index, result["pct"], color=colors, edgecolor="white", linewidth=0.6)
for bar, pct, cnt in zip(bars, result["pct"], result["missing"]):
    ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
            f"{pct:.1f}%  ({int(cnt):,})",
            va="center", ha="left", fontsize=9.5, fontweight="bold")
ax.set_xlim(0, 115)
ax.set_xlabel("Taux de valeurs manquantes (%)", fontsize=11)
ax.set_title(
    f"Valeurs manquantes par colonne -- Donnees brutes\n"
    f"({n:,} lignes  |  {len(df.columns)} colonnes  |  {len(result)} colonnes avec NaN)",
    fontsize=12, fontweight="bold", pad=12
)
ax.axvline(50, color=FORVIA["critique"], lw=1.2, linestyle="--", alpha=0.6)
ax.axvline(10, color=FORVIA["modere"],   lw=1.2, linestyle="--", alpha=0.6)

p1 = mpatches.Patch(color=FORVIA["critique"], label=">= 50% (critique)")
p2 = mpatches.Patch(color=FORVIA["modere"],   label="10-49% (modere)")
p3 = mpatches.Patch(color=FORVIA["faible"],   label="< 10%  (faible)")
ax.legend(handles=[p1, p2, p3], loc="lower right", fontsize=9)
ax.grid(axis="x", linestyle="--", alpha=0.4)

# ---- Pie global ----
ax2 = axes[1]
total_cells   = n * len(df.columns)
total_missing = miss.sum()
total_present = total_cells - total_missing

wedges, texts, autotexts = ax2.pie(
    [total_present, total_missing],
    labels=[
        "Renseignees\n{:,}".format(total_present),
        "Manquantes\n{:,}".format(total_missing),
    ],
    colors=["#002D72", "#DA291C"],
    autopct="%1.1f%%",
    startangle=90,
    textprops={"fontsize": 10, "fontweight": "bold"},
)
for at in autotexts:
    at.set_color("white"); at.set_fontsize(11); at.set_fontweight("bold")

ax2.set_title(
    "Vue globale\n({:,} cellules totales)".format(total_cells),
    fontsize=11, fontweight="bold"
)

stats = (
    "Dataset : {:,} lignes x {} colonnes\n"
    "Colonnes sans NaN : {}\n"
    "Colonnes avec NaN : {}\n"
    "Completude globale : {:.1f}%\n"
    "Taux NaN global  : {:.1f}%"
).format(
    n, len(df.columns),
    int((miss == 0).sum()),
    int((miss > 0).sum()),
    total_present / total_cells * 100,
    total_missing / total_cells * 100,
)
ax2.text(0, -1.50, stats, ha="center", va="top", fontsize=9.5,
         bbox=dict(boxstyle="round,pad=0.5", facecolor="#f0f4ff",
                   edgecolor="#002D72", alpha=0.9))

plt.tight_layout()
out = ROOT / "missing_values" / "missing_values_raw.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved:", out)
