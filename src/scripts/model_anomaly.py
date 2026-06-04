# ============================================
# ANOMALY DETECTION MODULE
# ============================================
"""
Détection d'anomalies avec Isolation Forest pour les données FORVIA.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from scipy.stats import zscore
import warnings
warnings.filterwarnings('ignore')


class AnomalyDetector:
    """
    Détecteur d'anomalies multi-méthodes pour transactions d'achat.
    """
    
    def __init__(self, contamination=0.05, random_state=42):
        """
        Initialisation.
        
        Args:
            contamination (float): Ratio attendu d'anomalies (default: 5%)
            random_state (int): Seed pour reproductibilité
        """
        self.contamination = contamination
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.iso_forest = None
        self.results = None
    
    
    def fit(self, df, numeric_cols=None):
        """
        Entraînement du modèle Isolation Forest.
        
        Args:
            df (pd.DataFrame): Données d'entraînement
            numeric_cols (list): Colonnes numériques à utiliser
            
        Returns:
            self
        """
        if numeric_cols is None:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Préparation des données
        X = df[numeric_cols].fillna(df[numeric_cols].mean())
        X_scaled = self.scaler.fit_transform(X)
        
        # Entraînement
        self.iso_forest = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=100
        )
        self.iso_forest.fit(X_scaled)
        
        print(f"✅ IsolationForest fitted on {X.shape[0]} rows, {X.shape[1]} features")
        return self
    
    
    def predict(self, df, numeric_cols=None):
        """
        Prédiction des anomalies.
        
        Args:
            df (pd.DataFrame): Données à analyser
            numeric_cols (list): Colonnes numériques
            
        Returns:
            pd.DataFrame: Données avec colonnes anomaly_flag et anomaly_score
        """
        if self.iso_forest is None:
            raise ValueError("Model not fitted. Call fit() first.")
        
        if numeric_cols is None:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        result = df.copy()
        
        # Préparation
        X = df[numeric_cols].fillna(df[numeric_cols].mean())
        X_scaled = self.scaler.transform(X)
        
        # Prédiction
        predictions = self.iso_forest.predict(X_scaled)
        scores = self.iso_forest.score_samples(X_scaled)
        
        result['anomaly_if_prediction'] = predictions  # 1 = normal, -1 = anomaly
        result['anomaly_if_score'] = scores
        result['anomaly_if_flag'] = (predictions == -1).astype(int)
        
        self.results = result
        
        n_anomalies = (predictions == -1).sum()
        print(f"🚨 Anomalies detected: {n_anomalies}/{len(df)} ({n_anomalies/len(df)*100:.2f}%)")
        
        return result
    
    
    def zscore_detection(self, df, numeric_cols=None, threshold=3):
        """
        Détection statistique Z-score.
        
        Args:
            df (pd.DataFrame): Données
            numeric_cols (list): Colonnes numériques
            threshold (float): Seuil Z-score
            
        Returns:
            pd.DataFrame: Avec colonnes anomaly_zscore
        """
        if numeric_cols is None:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        result = df.copy() if self.results is None else self.results.copy()
        result['anomaly_zscore_flag'] = 0
        result['anomaly_zscore_reason'] = ''
        
        for col in numeric_cols:
            z_scores = np.abs(zscore(result[col].fillna(0)))
            outliers = z_scores > threshold
            
            result.loc[outliers, 'anomaly_zscore_flag'] += 1
            result.loc[outliers, 'anomaly_zscore_reason'] += f"{col}(z-score={threshold}); "
        
        n_flagged = (result['anomaly_zscore_flag'] > 0).sum()
        print(f"📊 Z-score anomalies: {n_flagged}")
        
        self.results = result
        return result
    
    
    def iqr_detection(self, df, numeric_cols=None, multiplier=1.5):
        """
        Détection IQR (Interquartile Range).
        
        Args:
            df (pd.DataFrame): Données
            numeric_cols (list): Colonnes numériques
            multiplier (float): Multiplicateur IQR (default: 1.5)
            
        Returns:
            pd.DataFrame: Avec colonnes anomaly_iqr
        """
        if numeric_cols is None:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        result = df.copy() if self.results is None else self.results.copy()
        result['anomaly_iqr_flag'] = 0
        result['anomaly_iqr_reason'] = ''
        
        for col in numeric_cols:
            Q1 = result[col].quantile(0.25)
            Q3 = result[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - multiplier * IQR
            upper = Q3 + multiplier * IQR
            
            outliers = (result[col] < lower) | (result[col] > upper)
            
            result.loc[outliers, 'anomaly_iqr_flag'] += 1
            result.loc[outliers, 'anomaly_iqr_reason'] += f"{col}:[{lower:.2f},{upper:.2f}]; "
        
        n_flagged = (result['anomaly_iqr_flag'] > 0).sum()
        print(f"📊 IQR anomalies: {n_flagged}")
        
        self.results = result
        return result
    
    
    def consistency_check(self, df, qty_col, price_col, amount_col, tolerance=0.05):
        """
        Vérification Quantité × Prix = Montant.
        
        Args:
            df (pd.DataFrame): Données
            qty_col (str): Colonne quantité
            price_col (str): Colonne prix
            amount_col (str): Colonne montant
            tolerance (float): Tolérance (5% par défaut)
            
        Returns:
            pd.DataFrame: Avec flag inconsistency
        """
        result = df.copy() if self.results is None else self.results.copy()
        
        if qty_col not in df.columns or price_col not in df.columns or amount_col not in df.columns:
            print(f"⚠️  Cannot check consistency: missing columns")
            return result
        
        result['expected_amount'] = result[qty_col] * result[price_col]
        inconsistent = np.abs(result[amount_col] - result['expected_amount']) > (result['expected_amount'] * tolerance)
        
        result['anomaly_consistency_flag'] = inconsistent.astype(int)
        
        n_inconsistent = inconsistent.sum()
        print(f"📊 Consistency anomalies: {n_inconsistent}")
        
        self.results = result
        return result
    
    
    def get_summary(self):
        """
        Résumé des anomalies détectées.
        
        Returns:
            dict: Statistiques des anomalies
        """
        if self.results is None:
            return {}
        
        return {
            'total_rows': len(self.results),
            'isolation_forest_anomalies': (self.results['anomaly_if_flag'] == 1).sum(),
            'zscore_anomalies': (self.results['anomaly_zscore_flag'] > 0).sum() if 'anomaly_zscore_flag' in self.results.columns else 0,
            'iqr_anomalies': (self.results['anomaly_iqr_flag'] > 0).sum() if 'anomaly_iqr_flag' in self.results.columns else 0,
            'consistency_anomalies': (self.results['anomaly_consistency_flag'] == 1).sum() if 'anomaly_consistency_flag' in self.results.columns else 0
        }
