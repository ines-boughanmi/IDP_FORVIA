"""
Script de fusion entre Documents1 et Ariba Contracts
Objectif: Ajouter les noms de fournisseurs (ariba_erp_vendor_name) à Documents1
Clé de jointure: supplier_|_lifnr = ariba_erp_vendor_id
"""

import pandas as pd
import os

# Chemins des fichiers
ariba_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'Ariba Contract.csv')
contracts2_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'Documents1.csv')
output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'Documents1_with_vendor_names.csv')

print("=" * 80)
print("FUSION: Documents1 + Ariba Contract (noms des fournisseurs)")
print("=" * 80)

# Charger les datasets
print("\n1. Chargement des datasets...")
ariba = pd.read_csv(ariba_path)
contracts2 = pd.read_csv(contracts2_path)

print(f"   - Ariba Contract.csv: {ariba.shape[0]:,} lignes, {ariba.shape[1]} colonnes")
print(f"   - Documents1.csv: {contracts2.shape[0]:,} lignes, {contracts2.shape[1]} colonnes")

# Afficher les colonnes clés
print("\n2. Colonnes de jointure:")
print(f"   - Ariba: 'ariba_erp_vendor_id' (unique: {ariba['ariba_erp_vendor_id'].nunique()})")
print(f"   - Contracts2: 'supplier_|_lifnr' (unique: {contracts2['supplier_|_lifnr'].nunique()})")

# Préparer les données Ariba pour la jointure
# Garder seulement les colonnes nécessaires et supprimer les doublons
ariba_vendors = ariba[['ariba_erp_vendor_id', 'ariba_erp_vendor_name']].drop_duplicates()
print(f"\n3. Vendors uniques dans Ariba: {ariba_vendors.shape[0]:,}")

# Faire la jointure (LEFT JOIN pour garder toutes les lignes de Documents1)
print("\n4. Fusion (LEFT JOIN)...")
contracts2_merged = contracts2.merge(
    ariba_vendors,
    left_on='supplier_|_lifnr',
    right_on='ariba_erp_vendor_id',
    how='left'
)

print(f"   - Résultat: {contracts2_merged.shape[0]:,} lignes, {contracts2_merged.shape[1]} colonnes")

# Statistiques de la jointure
matched = contracts2_merged['ariba_erp_vendor_name'].notna().sum()
unmatched = contracts2_merged['ariba_erp_vendor_name'].isna().sum()

print(f"\n5. Résultats de la jointure:")
print(f"   - Fournisseurs appairés: {matched:,} lignes ({matched/len(contracts2_merged)*100:.2f}%)")
print(f"   - Fournisseurs non appairés: {unmatched:,} lignes ({unmatched/len(contracts2_merged)*100:.2f}%)")

# Afficher les fournisseurs sans correspondance (sample)
if unmatched > 0:
    print(f"\n   Top 10 fournisseurs sans correspondance:")
    no_match = contracts2_merged[contracts2_merged['ariba_erp_vendor_name'].isna()]['supplier_|_lifnr'].value_counts().head(10)
    for vendor_id, count in no_match.items():
        print(f"      - {vendor_id}: {count} occurrences")

# Sauvegarder le résultat
print(f"\n6. Sauvegarde du fichier fusionné...")
os.makedirs(os.path.dirname(output_path), exist_ok=True)
contracts2_merged.to_csv(output_path, index=False)
print(f"   ✓ Fichier sauvegardé: {output_path}")

print(f"\n7. Aperçu des données (5 premières lignes):")
print(contracts2_merged[['supplier_|_lifnr', 'ariba_erp_vendor_name', 'ariba_erp_vendor_id']].head())

# Ensure there is a `supplier_name` column for downstream processes
if 'supplier_name' not in contracts2_merged.columns:
    contracts2_merged['supplier_name'] = contracts2_merged['ariba_erp_vendor_name']
else:
    # Fill missing supplier_name values with ariba vendor name when available
    contracts2_merged['supplier_name'] = contracts2_merged['supplier_name'].fillna(contracts2_merged['ariba_erp_vendor_name'])

# Save again with supplier_name column ensured
contracts2_merged.to_csv(output_path, index=False)
print(f"   ✓ Updated file with 'supplier_name' column: {output_path}")

print("\n" + "=" * 80)
print("✓ Fusion terminée avec succès!")
print("=" * 80)
