# ============================================
# SUPPLIER CLUSTERING MODULE
# ============================================
"""
Segmentation de fournisseurs avec K-Means pour FORVIA.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')


class SupplierClustering:
    """
    Segmentation des fournisseurs en clusters homogènes.
    """
    
    def __init__(self, random_state=42):
        """
        Initialisation.
        
        Args:
            random_state (int): Seed pour reproductibilité
        """
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.kmeans = None
        self.features = None
        self.supplier_profiles = None
        self.results = None
    
    
    def create_supplier_features(self, df, supplier_col, amount_col=None, 
                                qty_col=None, price_col=None):
        """
        Crée un DataFrame de features par fournisseur.
        
        Args:
            df (pd.DataFrame): Données brutes
            supplier_col (str): Colonne fournisseur
            amount_col (str): Colonne montant (optionnel)
            qty_col (str): Colonne quantité (optionnel)
            price_col (str): Colonne prix (optionnel)
            
        Returns:
            pd.DataFrame: Features par fournisseur
        """
        features = []
        
        for supplier in df[supplier_col].unique():
            supplier_data = df[df[supplier_col] == supplier]
            
            row = {'supplier': supplier}
            
            # Volume et fréquence
            row['transaction_count'] = len(supplier_data)
            
            # Montant
            if amount_col and amount_col in df.columns:
                row['total_amount'] = supplier_data[amount_col].sum()
                row['avg_amount'] = supplier_data[amount_col].mean()
                row['std_amount'] = supplier_data[amount_col].std()
            
            # Quantité
            if qty_col and qty_col in df.columns:
                row['total_qty'] = supplier_data[qty_col].sum()
                row['avg_qty'] = supplier_data[qty_col].mean()
            
            # Prix
            if price_col and price_col in df.columns:
                row['avg_price'] = supplier_data[price_col].mean()
                row['std_price'] = supplier_data[price_col].std()
                row['price_cv'] = (row['std_price'] / row['avg_price'] 
                                   if row['avg_price'] > 0 else 0)
            
            features.append(row)
        
        self.supplier_profiles = pd.DataFrame(features)
        print(f"✅ Created {len(self.supplier_profiles)} supplier profiles")
        
        return self.supplier_profiles
    
    
    def prepare_data(self, df_features, exclude_cols=['supplier']):
        """
        Prépare les données pour clustering.
        
        Args:
            df_features (pd.DataFrame): Features par supplier
            exclude_cols (list): Colonnes à exclure
            
        Returns:
            np.ndarray: Features normalisées
        """
        numeric_features = df_features.select_dtypes(include=[np.number]).columns.tolist()
        # Retirer les colonnes exclues
        numeric_features = [c for c in numeric_features if c not in exclude_cols]
        
        # Remplir les NaN
        X = df_features[numeric_features].fillna(0)
        
        # Normaliser
        X_scaled = self.scaler.fit_transform(X)
        
        self.features = df_features[numeric_features]
        
        print(f"✅ Data prepared: {X_scaled.shape[0]} suppliers, {X_scaled.shape[1]} features")
        
        return X_scaled
    
    
    def find_optimal_k(self, X_scaled, k_range=range(2, 8)):
        """
        Trouve le K optimal avec Elbow method + Silhouette.
        
        Args:
            X_scaled (np.ndarray): Features normalisées
            k_range (range): Range de K à tester
            
        Returns:
            dict: Scores pour chaque K
        """
        scores = {}
        
        for k in k_range:
            km = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            labels = km.fit_predict(X_scaled)
            
            inertia = km.inertia_
            silhouette = silhouette_score(X_scaled, labels)
            davies_bouldin = davies_bouldin_score(X_scaled, labels)
            
            scores[k] = {
                'inertia': inertia,
                'silhouette': silhouette,
                'davies_bouldin': davies_bouldin
            }
            
            print(f"K={k}: Inertia={inertia:.0f}, Silhouette={silhouette:.3f}, DB={davies_bouldin:.3f}")
        
        return scores
    
    
    def fit(self, X_scaled, n_clusters=3):
        """
        Entraînement K-Means final.
        
        Args:
            X_scaled (np.ndarray): Features normalisées
            n_clusters (int): Nombre de clusters
            
        Returns:
            self
        """
        self.kmeans = KMeans(n_clusters=n_clusters, 
                            random_state=self.random_state,
                            n_init=10)
        labels = self.kmeans.fit_predict(X_scaled)
        
        silhouette = silhouette_score(X_scaled, labels)
        print(f"✅ KMeans fitted: {n_clusters} clusters, Silhouette={silhouette:.3f}")
        
        return self
    
    
    def predict(self, df_features):
        """
        Attribue les clusters aux fournisseurs.
        
        Args:
            df_features (pd.DataFrame): Features par supplier
            
        Returns:
            pd.DataFrame: Avec colonne cluster
        """
        if self.kmeans is None:
            raise ValueError("Model not fitted. Call fit() first.")
        
        # Fill NaN values before scaling
        features_filled = self.features.fillna(self.features.median())
        X_scaled = self.scaler.transform(features_filled)
        clusters = self.kmeans.predict(X_scaled)
        
        result = df_features.copy()
        result['cluster'] = clusters
        
        self.results = result
        
        print(f"✅ Clusters assigned to {len(result)} suppliers")
        
        return result
    
    
    def get_cluster_profiles(self):
        """
        Génère le profil de chaque cluster.
        
        Returns:
            pd.DataFrame: Profils par cluster
        """
        if self.results is None:
            return None
        
        profiles = self.results.groupby('cluster').agg({
            'supplier': 'count',
            'transaction_count': ['mean', 'sum'],
            'total_amount': ['mean', 'sum'],
            'avg_price': 'mean',
            'std_price': 'mean'
        }).round(2)
        
        profiles.columns = ['_'.join(col).strip() for col in profiles.columns.values]
        profiles = profiles.rename(columns={'supplier_count': 'n_suppliers'})
        
        print(f"\n📊 CLUSTER PROFILES:")
        print(profiles)
        
        return profiles
    
    
    def label_clusters(self, labels_dict=None):
        """
        Attribue des labels métier aux clusters (Tier-1, Tier-2, etc.).
        
        Args:
            labels_dict (dict): Mapping cluster -> label (optionnel)
            
        Returns:
            pd.DataFrame: Résultats avec labels
        """
        if self.results is None:
            return None
        
        if labels_dict is None:
            # Labels par défaut basés sur le nombre de transactions
            cluster_sizes = self.results.groupby('cluster')['transaction_count'].sum()
            sorted_clusters = cluster_sizes.sort_values(ascending=False).index.tolist()
            
            labels_dict = {
                sorted_clusters[0]: 'Tier-1 (Strategic)',      # Largest volume
                sorted_clusters[1]: 'Tier-2 (Important)',       # Medium volume
            }
            if len(sorted_clusters) > 2:
                labels_dict[sorted_clusters[2]] = 'Tier-3 (Tactical)'
        
        result = self.results.copy()
        result['tier'] = result['cluster'].map(labels_dict)
        
        print(f"\n📊 SUPPLIER TIERS:")
        print(result.groupby('tier')['supplier'].count())
        
        self.results = result
        
        return result
    
    
    def export_results(self, filepath):
        """
        Exporte les résultats de clustering.
        """
        if self.results is not None:
            self.results.to_csv(filepath, index=False)
            print(f"✅ Results exported to {filepath}")
        else:
            print("❌ No results to export")
