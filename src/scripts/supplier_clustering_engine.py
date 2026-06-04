#!/usr/bin/env python
"""
PHASE 2 — Advanced Supplier Clustering
=======================================

Tasks 3-4: Clustering with validation
- KMeans clustering
- DBSCAN for outlier detection
- PCA for visualization
- Silhouette analysis
- Business interpretation
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, silhouette_samples
import matplotlib.pyplot as plt
from scipy.spatial.distance import pdist, squareform


class SupplierClusteringEngine:
    """
    Advanced clustering for supplier segmentation.
    Combines KMeans with DBSCAN for robust supplier grouping.
    """
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.scaler = StandardScaler()
        self.kmeans = None
        self.dbscan = None
        self.pca = None
        self.X_scaled = None
        self.X_pca = None
    
    def log(self, msg):
        if self.verbose:
            print(f"  {msg}")
    
    # =========================================================================
    # DATA PREPARATION
    # =========================================================================
    
    def prepare_features(self, df_features):
        """
        Prepare and scale supplier features for clustering.
        """
        self.log("Preparing features for clustering...")
        
        # Select numeric features (exclude supplier_id)
        numeric_cols = df_features.select_dtypes(include=[np.number]).columns.tolist()
        X = df_features[numeric_cols].fillna(0).values
        
        # Handle infinite values
        X = np.nan_to_num(X, nan=0, posinf=0, neginf=0)
        
        # Scale
        self.X_scaled = self.scaler.fit_transform(X)
        
        self.log(f"✓ Features scaled: {X.shape[0]} suppliers × {X.shape[1]} features")
        
        return self.X_scaled
    
    # =========================================================================
    # CLUSTERING ALGORITHMS
    # =========================================================================
    
    def fit_kmeans(self, X_scaled, n_clusters=4):
        """
        KMeans clustering with optimal k detection.
        """
        self.log(f"Fitting KMeans (k={n_clusters})...")
        
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        kmeans_labels = self.kmeans.fit_predict(X_scaled)
        
        # Silhouette score
        sil_score = silhouette_score(X_scaled, kmeans_labels)
        self.log(f"  Silhouette Score: {sil_score:.4f}")
        
        return kmeans_labels, sil_score
    
    def find_optimal_k(self, X_scaled, k_range=range(2, 11)):
        """
        Find optimal number of clusters using silhouette score.
        """
        self.log("Finding optimal k...")
        
        silhouette_scores = []
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X_scaled)
            score = silhouette_score(X_scaled, labels)
            silhouette_scores.append(score)
            self.log(f"  k={k}: {score:.4f}")
        
        optimal_k = k_range[np.argmax(silhouette_scores)]
        self.log(f"✓ Optimal k: {optimal_k} (score: {max(silhouette_scores):.4f})")
        
        return optimal_k, silhouette_scores
    
    def fit_dbscan(self, X_scaled, eps=0.5, min_samples=5):
        """
        DBSCAN clustering for outlier detection.
        """
        self.log(f"Fitting DBSCAN (eps={eps}, min_samples={min_samples})...")
        
        self.dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        dbscan_labels = self.dbscan.fit_predict(X_scaled)
        
        n_clusters = len(set(dbscan_labels)) - (1 if -1 in dbscan_labels else 0)
        n_outliers = (dbscan_labels == -1).sum()
        
        self.log(f"✓ Found {n_clusters} clusters, {n_outliers} outliers")
        
        return dbscan_labels
    
    # =========================================================================
    # DIMENSIONALITY REDUCTION
    # =========================================================================
    
    def fit_pca(self, X_scaled, n_components=2):
        """
        PCA for visualization.
        """
        self.log(f"Fitting PCA ({n_components} components)...")
        
        self.pca = PCA(n_components=n_components)
        self.X_pca = self.pca.fit_transform(X_scaled)
        
        explained_var = self.pca.explained_variance_ratio_.sum()
        self.log(f"✓ Explained variance: {explained_var:.2%}")
        
        return self.X_pca
    
    # =========================================================================
    # CLUSTER ANALYSIS
    # =========================================================================
    
    def analyze_clusters(self, df_features, kmeans_labels):
        """
        Detailed analysis of KMeans clusters.
        """
        self.log("Analyzing clusters...")
        
        df_analysis = df_features.copy()
        df_analysis['cluster'] = kmeans_labels
        
        cluster_stats = []
        for cluster_id in sorted(set(kmeans_labels)):
            cluster_data = df_analysis[df_analysis['cluster'] == cluster_id]
            
            stats = {
                'cluster_id': cluster_id,
                'cluster_size': len(cluster_data),
                'size_pct': len(cluster_data) / len(df_analysis) * 100,
                'avg_risk_score': cluster_data['supplier_risk_score'].mean() if 'supplier_risk_score' in df_analysis.columns else 0,
                'avg_anomaly_ratio': cluster_data['behavioral_anomaly_ratio'].mean() if 'behavioral_anomaly_ratio' in df_analysis.columns else 0,
                'avg_transaction_frequency': cluster_data['behavioral_transaction_frequency'].mean() if 'behavioral_transaction_frequency' in df_analysis.columns else 0,
                'avg_amount_volatility': cluster_data['financial_amount_volatility_cv'].mean() if 'financial_amount_volatility_cv' in df_analysis.columns else 0,
                'avg_aging_days': cluster_data['temporal_avg_aging_days'].mean() if 'temporal_avg_aging_days' in df_analysis.columns else 0,
            }
            
            cluster_stats.append(stats)
            
            self.log(f"\n  Cluster {cluster_id}:")
            self.log(f"    Size: {stats['cluster_size']} ({stats['size_pct']:.1f}%)")
            if 'supplier_risk_score' in df_analysis.columns:
                self.log(f"    Avg Risk: {stats['avg_risk_score']:.2f}")
            if 'behavioral_anomaly_ratio' in df_analysis.columns:
                self.log(f"    Avg Anomaly Ratio: {stats['avg_anomaly_ratio']:.2%}")
        
        return pd.DataFrame(cluster_stats)
    
    # =========================================================================
    # SILHOUETTE ANALYSIS
    # =========================================================================
    
    def silhouette_analysis(self, X_scaled, kmeans_labels):
        """
        Detailed silhouette analysis for cluster quality.
        """
        self.log("Performing silhouette analysis...")
        
        silhouette_vals = silhouette_samples(X_scaled, kmeans_labels)
        silhouette_avg = silhouette_score(X_scaled, kmeans_labels)
        
        self.log(f"  Average silhouette score: {silhouette_avg:.4f}")
        
        cluster_silhouettes = {}
        for cluster_id in sorted(set(kmeans_labels)):
            cluster_silhouette_vals = silhouette_vals[kmeans_labels == cluster_id]
            cluster_silhouettes[cluster_id] = {
                'mean': cluster_silhouette_vals.mean(),
                'min': cluster_silhouette_vals.min(),
                'max': cluster_silhouette_vals.max(),
                'std': cluster_silhouette_vals.std(),
            }
            self.log(f"  Cluster {cluster_id}: mean={cluster_silhouettes[cluster_id]['mean']:.4f}")
        
        return silhouette_avg, silhouette_vals, cluster_silhouettes
    
    # =========================================================================
    # CLUSTER LABELING & INTERPRETATION
    # =========================================================================
    
    def assign_cluster_labels(self, cluster_stats):
        """
        Assign business-meaningful labels to clusters.
        """
        self.log("Assigning cluster labels...")
        
        cluster_labels = {}
        
        for idx, row in cluster_stats.iterrows():
            cluster_id = row['cluster_id']
            risk_score = row['avg_risk_score']
            anomaly_ratio = row['avg_anomaly_ratio']
            frequency = row['avg_transaction_frequency']
            volatility = row['avg_amount_volatility']
            
            # Decision logic for labeling
            if risk_score < 25 and anomaly_ratio < 0.05:
                label = 'TRUSTED_SUPPLIERS'
                description = 'Stable, predictable, low anomaly'
            elif risk_score < 50 and anomaly_ratio < 0.15:
                label = 'STANDARD_SUPPLIERS'
                description = 'Normal operations, acceptable risk'
            elif risk_score < 70 and anomaly_ratio < 0.30:
                label = 'MONITORED_SUPPLIERS'
                description = 'Unstable trends, elevated anomalies'
            else:
                label = 'HIGH_RISK_SUPPLIERS'
                description = 'Strong volatility, suspicious patterns'
            
            cluster_labels[cluster_id] = {
                'label': label,
                'description': description,
            }
            
            self.log(f"  Cluster {cluster_id}: {label}")
        
        return cluster_labels


# =============================================================================
# TESTING
# =============================================================================

if __name__ == '__main__':
    print("="*80)
    print("PHASE 2 — ADVANCED SUPPLIER CLUSTERING")
    print("="*80)
    
    print("\nModules loaded:")
    print("  ✓ SupplierClusteringEngine")
    print("\nCapabilities:")
    print("  ✓ KMeans with optimal k detection")
    print("  ✓ DBSCAN outlier detection")
    print("  ✓ PCA visualization")
    print("  ✓ Silhouette analysis")
    print("  ✓ Business-meaningful labeling")
