#!/usr/bin/env python
"""
PHASE 2 — Complete Supplier Intelligence Implementation
========================================================

Orchestrates all tasks:
1. Supplier behavioral feature engineering
2. Advanced supplier risk scoring
3. Advanced clustering
4. Cluster validation
5. Supplier explainability
6. Dataset generation
7. Visualization preparation
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import warnings
warnings.filterwarnings('ignore')

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from supplier_intelligence_core import (
    SupplierBehavioralFeatures,
    AdvancedSupplierRiskEngine
)
from supplier_clustering_engine import SupplierClusteringEngine
from supplier_explainability_engine import SupplierExplainabilityEngine

print("="*80)
print("PHASE 2 — ADVANCED SUPPLIER INTELLIGENCE PLATFORM")
print("="*80)

# ============================================================================
# STEP 1: Load Data
# ============================================================================
print("\n[STEP 1] LOADING DATA")
print("-" * 80)

df_ml = pd.read_csv('src/data/processed/p2p_ml_dataset.csv')
df_monitoring_v2 = pd.read_csv('src/data/processed/p2p_monitoring_dataset_phase2.csv')

print(f"ML dataset: {df_ml.shape[0]:,} transactions × {df_ml.shape[1]} columns")
print(f"Monitoring v2: {df_monitoring_v2.shape[0]:,} transactions × {df_monitoring_v2.shape[1]} columns")

# Merge to add supplier_id to ML features
df_ml = pd.concat([
    df_ml,
    df_monitoring_v2[['supplier_id']]
], axis=1)

# ============================================================================
# STEP 2: Feature Engineering
# ============================================================================
print("\n[STEP 2] SUPPLIER BEHAVIORAL FEATURE ENGINEERING")
print("-" * 80)

feature_engine = SupplierBehavioralFeatures(verbose=True)
df_supplier_features = feature_engine.create_supplier_feature_matrix(df_ml)

print(f"\nFeature Matrix Shape: {df_supplier_features.shape}")
print(f"Suppliers: {len(df_supplier_features):,}")
print(f"Features: {len(df_supplier_features.columns) - 1}")

# Display sample features
print("\nSample Supplier (first row):")
for col in df_supplier_features.columns[:10]:
    print(f"  {col}: {df_supplier_features[col].iloc[0]:.2f}")

# ============================================================================
# STEP 3: Advanced Risk Scoring
# ============================================================================
print("\n[STEP 3] ADVANCED SUPPLIER RISK SCORING")
print("-" * 80)

risk_engine = AdvancedSupplierRiskEngine(verbose=True)
df_supplier_risks = risk_engine.compute_supplier_risk(df_supplier_features)

print(f"\nSupplier Risk Distribution:")
print(df_supplier_risks['supplier_risk_level'].value_counts())

print(f"\nSupplier Risk Score Statistics:")
print(f"  Mean:   {df_supplier_risks['supplier_risk_score'].mean():.2f}")
print(f"  Median: {df_supplier_risks['supplier_risk_score'].median():.2f}")
print(f"  Std:    {df_supplier_risks['supplier_risk_score'].std():.2f}")

# ============================================================================
# STEP 4: Clustering
# ============================================================================
print("\n[STEP 4] SUPPLIER CLUSTERING")
print("-" * 80)

clustering_engine = SupplierClusteringEngine(verbose=True)

# Prepare features
X_scaled = clustering_engine.prepare_features(df_supplier_risks)

# Find optimal k
print("\nFinding optimal number of clusters...")
optimal_k, silhouette_scores = clustering_engine.find_optimal_k(X_scaled)

# Fit KMeans
print("\nFitting KMeans with optimal k...")
kmeans_labels, sil_score = clustering_engine.fit_kmeans(X_scaled, n_clusters=optimal_k)

# Fit DBSCAN for outlier detection
print("\nFitting DBSCAN for outlier detection...")
dbscan_labels = clustering_engine.fit_dbscan(X_scaled, eps=1.5, min_samples=3)

# Add clusters to dataframe
df_supplier_risks['kmeans_cluster'] = kmeans_labels
df_supplier_risks['dbscan_cluster'] = dbscan_labels

# ============================================================================
# STEP 5: Cluster Analysis
# ============================================================================
print("\n[STEP 5] CLUSTER ANALYSIS & VALIDATION")
print("-" * 80)

cluster_stats = clustering_engine.analyze_clusters(df_supplier_risks, kmeans_labels)

# Silhouette analysis
sil_avg, sil_vals, cluster_sil = clustering_engine.silhouette_analysis(X_scaled, kmeans_labels)

print(f"\nCluster Quality Metrics:")
print(f"  Overall Silhouette Score: {sil_avg:.4f}")
for cid, metrics in cluster_sil.items():
    print(f"  Cluster {cid} silhouette: {metrics['mean']:.4f}")

# Cluster labeling
cluster_labels = clustering_engine.assign_cluster_labels(cluster_stats)

# Add cluster labels to dataframe
df_supplier_risks['cluster_label'] = df_supplier_risks['kmeans_cluster'].map(
    {cid: info['label'] for cid, info in cluster_labels.items()}
)
df_supplier_risks['cluster_description'] = df_supplier_risks['kmeans_cluster'].map(
    {cid: info['description'] for cid, info in cluster_labels.items()}
)

# ============================================================================
# STEP 6: PCA Visualization Prep
# ============================================================================
print("\n[STEP 6] PCA FOR VISUALIZATION")
print("-" * 80)

X_pca = clustering_engine.fit_pca(X_scaled, n_components=2)
df_supplier_risks['pca_component_1'] = X_pca[:, 0]
df_supplier_risks['pca_component_2'] = X_pca[:, 1]

print(f"PCA components prepared for visualization")

# ============================================================================
# STEP 7: Explainability
# ============================================================================
print("\n[STEP 7] SUPPLIER EXPLAINABILITY")
print("-" * 80)

explainability_engine = SupplierExplainabilityEngine(verbose=True)
df_with_explanations = explainability_engine.generate_supplier_explanations_batch(
    df_supplier_risks
)

# Compute explanation statistics
explanation_stats = explainability_engine.compute_explanation_statistics(df_with_explanations)

print(f"\nExplanation Statistics:")
for stat_name, stat_value in explanation_stats.items():
    print(f"  {stat_name}: {stat_value:.2f}")

# ============================================================================
# STEP 8: Create Final Datasets
# ============================================================================
print("\n[STEP 8] CREATING OUTPUT DATASETS")
print("-" * 80)

# Dataset 1: Complete Supplier Intelligence
print("\nCreating supplier_intelligence_dataset.csv...")
intelligence_cols = [
    'supplier_id',
    'supplier_risk_score',
    'supplier_risk_level',
    'kmeans_cluster',
    'cluster_label',
    'cluster_description',
    'behavioral_transaction_frequency',
    'behavioral_anomaly_ratio',
    'behavioral_accounting_issue_ratio',
    'behavioral_data_issue_ratio',
    'behavioral_supplier_stability_score',
    'temporal_avg_aging_days',
    'temporal_temporal_consistency',
    'financial_amount_volatility_cv',
    'financial_abnormal_amount_ratio',
    'business_business_diversity',
    'risk_temporal',
    'risk_financial',
    'risk_behavioral',
    'risk_business',
    'reason_count',
    'warning_count',
    'strength_count',
]

available_cols = [c for c in intelligence_cols if c in df_with_explanations.columns]
df_intelligence = df_with_explanations[available_cols].copy()

intelligence_file = 'src/data/processed/supplier_intelligence_dataset.csv'
df_intelligence.to_csv(intelligence_file, index=False)
print(f"  OK Saved: {intelligence_file}")
print(f"     Rows: {len(df_intelligence):,}, Cols: {len(df_intelligence.columns)}")

# Dataset 2: Cluster Summary
print("\nCreating supplier_cluster_summary.csv...")
cluster_summary_data = []
for cid in sorted(set(kmeans_labels)):
    cluster_suppliers = df_with_explanations[df_with_explanations['kmeans_cluster'] == cid]
    
    summary = {
        'cluster_id': cid,
        'cluster_label': cluster_suppliers['cluster_label'].iloc[0] if len(cluster_suppliers) > 0 else 'UNKNOWN',
        'cluster_description': cluster_suppliers['cluster_description'].iloc[0] if len(cluster_suppliers) > 0 else '',
        'supplier_count': len(cluster_suppliers),
        'avg_risk_score': cluster_suppliers['supplier_risk_score'].mean(),
        'avg_anomaly_ratio': cluster_suppliers['behavioral_anomaly_ratio'].mean(),
        'avg_transaction_frequency': cluster_suppliers['behavioral_transaction_frequency'].mean(),
        'avg_aging_days': cluster_suppliers['temporal_avg_aging_days'].mean(),
        'silhouette_score': cluster_sil[cid]['mean'] if cid in cluster_sil else 0,
    }
    cluster_summary_data.append(summary)

df_cluster_summary = pd.DataFrame(cluster_summary_data)
cluster_file = 'src/data/processed/supplier_cluster_summary.csv'
df_cluster_summary.to_csv(cluster_file, index=False)
print(f"  OK Saved: {cluster_file}")
print(f"     Rows: {len(df_cluster_summary)}, Cols: {len(df_cluster_summary.columns)}")

# Dataset 3: Risk Monitoring
print("\nCreating supplier_risk_monitoring.csv...")
monitoring_cols = [
    'supplier_id',
    'supplier_risk_score',
    'supplier_risk_level',
    'cluster_label',
    'behavioral_anomaly_ratio',
    'behavioral_accounting_issue_ratio',
    'temporal_avg_aging_days',
    'financial_amount_volatility_cv',
    'explanation',
]

available_mon_cols = [c for c in monitoring_cols if c in df_with_explanations.columns]
df_monitoring_export = df_with_explanations[available_mon_cols].copy()

monitoring_file = 'src/data/processed/supplier_risk_monitoring.csv'
df_monitoring_export.to_csv(monitoring_file, index=False)
print(f"  OK Saved: {monitoring_file}")
print(f"     Rows: {len(df_monitoring_export):,}, Cols: {len(df_monitoring_export.columns)}")

# ============================================================================
# STEP 9: Summary Statistics
# ============================================================================
print("\n[STEP 9] SUMMARY STATISTICS")
print("-" * 80)

print(f"\nCluster Distribution:")
for label in sorted(set(df_with_explanations['cluster_label'])):
    count = (df_with_explanations['cluster_label'] == label).sum()
    pct = count / len(df_with_explanations) * 100
    print(f"  {label:25} {count:4,} ({pct:5.1f}%)")

print(f"\nRisk Level Distribution:")
for level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
    count = (df_with_explanations['supplier_risk_level'] == level).sum()
    pct = count / len(df_with_explanations) * 100
    print(f"  {level:20} {count:4,} ({pct:5.1f}%)")

print(f"\nTop 10 Riskiest Suppliers:")
top_10 = df_with_explanations.nlargest(10, 'supplier_risk_score')[
    ['supplier_id', 'supplier_risk_score', 'supplier_risk_level', 'cluster_label',
     'behavioral_anomaly_ratio', 'behavioral_transaction_frequency']
]
print(top_10.to_string(index=False))

print(f"\nBottom 10 Safest Suppliers:")
bottom_10 = df_with_explanations.nsmallest(10, 'supplier_risk_score')[
    ['supplier_id', 'supplier_risk_score', 'supplier_risk_level', 'cluster_label',
     'behavioral_anomaly_ratio', 'behavioral_transaction_frequency']
]
print(bottom_10.to_string(index=False))

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "="*80)
print("PHASE 2 — SUPPLIER INTELLIGENCE IMPLEMENTATION COMPLETE")
print("="*80)

print(f"""
DELIVERABLES:

Datasets Created:
  [OK] supplier_intelligence_dataset.csv ({len(df_intelligence):,} suppliers)
  [OK] supplier_cluster_summary.csv ({len(df_cluster_summary)} clusters)
  [OK] supplier_risk_monitoring.csv ({len(df_monitoring_export):,} suppliers)

Behavioral Features Engineered:
  [OK] Temporal features (6 metrics)
  [OK] Financial features (7 metrics)
  [OK] Behavioral features (10 metrics)
  [OK] Business features (4 metrics)
  [OK] TOTAL: 27 engineered features per supplier

Clustering:
  [OK] Optimal k: {optimal_k}
  [OK] KMeans silhouette: {sil_score:.4f}
  [OK] DBSCAN outliers detected: {(dbscan_labels == -1).sum()}
  [OK] PCA visualization prepared

Risk Scoring:
  [OK] Independent supplier risk engine
  [OK] 4 risk components weighted
  [OK] Percentile-based risk levels

Explainability:
  [OK] {len(df_with_explanations):,} suppliers explained
  [OK] Avg {explanation_stats['avg_reasons_per_supplier']:.1f} reasons per supplier
  [OK] Business-readable explanations

Status: READY FOR DASHBOARD & VISUALIZATION
""")

print("="*80)
