"""
============================================
SAP P2P COMPLETE PIPELINE
============================================

Pipeline ETL complet pour détection d'anomalies SAP P2P.
Orchestre: Rule Engine → Feature Engineering → Export

Flux:
1. Chargement données brutes
2. Application règles métier (Rule Engine)
3. Création features (Feature Engineering)
4. Nettoyage et préparation
5. Export résultats
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from rule_engine import RuleEngine
from feature_engineering import FeatureEngineer


class SAPP2PPipeline:
    """
    Pipeline SAP P2P complet d'analyse d'anomalies.
    """
    
    def __init__(self, data_dir='../data', verbose=True):
        """
        Initialisation du pipeline.
        
        Args:
            data_dir (str): Chemin dossier données
            verbose (bool): Afficher progression
        """
        self.data_dir = data_dir
        self.verbose = verbose
        self.raw_path = os.path.join(data_dir, 'raw', 'Documents1.csv')
        self.output_dir = os.path.join(data_dir, 'processed')
        
        # Créer dossiers sortie
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(data_dir, 'rule_based_labels'), exist_ok=True)
        os.makedirs(os.path.join(data_dir, 'risk_scores'), exist_ok=True)
        
        # Moteurs
        self.rule_engine = RuleEngine(verbose=verbose)
        self.feature_engineer = FeatureEngineer(verbose=verbose)
        
        # Données
        self.df_raw = None
        self.df_with_labels = None
        self.df_with_features = None
        self.df_final = None
    
    
    def log(self, msg):
        """Afficher message"""
        if self.verbose:
            print(f"📊 {msg}")
    
    
    # ============================================
    # ÉTAPE 1: CHARGEMENT
    # ============================================
    
    def load_data(self):
        """
        Charger données brutes.
        
        Returns:
            pd.DataFrame: Données brutes
        """
        self.log(f"\n{'='*80}")
        self.log("ÉTAPE 1: CHARGEMENT DONNÉES BRUTES")
        self.log(f"{'='*80}\n")
        
        self.log(f"Chemin: {self.raw_path}")
        
        if not os.path.exists(self.raw_path):
            raise FileNotFoundError(f"Fichier non trouvé: {self.raw_path}")
        
        self.log("Chargement Documents1.csv...")
        # Charger en forçant les colonnes fournisseur en string pour conserver zéros et espaces
        try:
            self.df_raw = pd.read_csv(self.raw_path, low_memory=False,
                                      dtype={
                                          'supplier_id': str,
                                          'supplier_name': str
                                      })
        except Exception:
            # Fallback si les colonnes n'existent pas ou dtype provoque une erreur
            self.df_raw = pd.read_csv(self.raw_path, low_memory=False)

        # Normaliser clés supplier en string (strip) pour éviter les conflits lors des joins
        if 'supplier_id' in self.df_raw.columns:
            self.df_raw['supplier_id'] = self.df_raw['supplier_id'].astype(str).str.strip()
        if 'supplier_name' in self.df_raw.columns:
            self.df_raw['supplier_name'] = self.df_raw['supplier_name'].astype(str).str.strip()
        
        self.log(f"✓ Données chargées: {self.df_raw.shape[0]:,} lignes, {self.df_raw.shape[1]} colonnes")
        self.log(f"✓ Taille: {os.path.getsize(self.raw_path) / 1e6:.1f} MB")
        self.log(f"✓ Mémoire: {self.df_raw.memory_usage(deep=True).sum() / 1e6:.1f} MB")
        
        return self.df_raw
    
    
    # ============================================
    # ÉTAPE 2: RÈGLES MÉTIER
    # ============================================
    
    def apply_business_rules(self):
        """
        Appliquer règles métier SAP.
        
        Returns:
            pd.DataFrame: Données avec labels anomalies
        """
        self.log(f"\n{'='*80}")
        self.log("ÉTAPE 2: APPLICATION RÈGLES MÉTIER")
        self.log(f"{'='*80}\n")
        
        if self.df_raw is None:
            raise ValueError("Données brutes non chargées. Appelez load_data() d'abord.")
        
        self.df_with_labels = self.rule_engine.detect_anomalies(self.df_raw)
        
        # Statistiques
        self.log(f"\n✓ Règles appliquées avec succès")
        
        return self.df_with_labels
    
    
    # ============================================
    # ÉTAPE 3: FEATURE ENGINEERING
    # ============================================
    
    def create_features(self):
        """
        Créer features pour ML.
        
        Returns:
            pd.DataFrame: Données avec features
        """
        self.log(f"\n{'='*80}")
        self.log("ÉTAPE 3: FEATURE ENGINEERING")
        self.log(f"{'='*80}\n")
        
        if self.df_with_labels is None:
            raise ValueError("Labels non créés. Appelez apply_business_rules() d'abord.")
        
        # Préserver les colonnes d'identification AVANT le feature engineering
        # ✅ Utiliser les vrais noms de colonnes qui existent dans les données
        id_cols = ['purchasing_document_|_ebeln', 'item_|_ebelp', 'supplier_|_lifnr', 
                   'supplier_name', 'anomaly_label', 'anomaly_severity', 'is_anomaly']
        preserved_cols = {col: self.df_with_labels[col].copy() 
                         for col in id_cols if col in self.df_with_labels.columns}
        
        self.df_with_features = self.feature_engineer.create_all_features(self.df_with_labels)
        
        # Restaurer les colonnes d'identification
        for col, data in preserved_cols.items():
            if col not in self.df_with_features.columns:
                self.df_with_features[col] = data
        
        return self.df_with_features
    
    
    # ============================================
    # ÉTAPE 4: SÉLECTION FEATURES ML
    # ============================================
    
    def select_ml_features(self):
        """
        Sélectionner features pour modèles ML.
        
        Returns:
            tuple: (X, y) pour modèles
        """
        self.log(f"\n{'='*80}")
        self.log("ÉTAPE 4: SÉLECTION FEATURES ML")
        self.log(f"{'='*80}\n")
        
        if self.df_with_features is None:
            raise ValueError("Features non créées. Appelez create_features() d'abord.")
        
        # Features numériques
        numeric_features = self.feature_engineer.get_numeric_features()
        
        # Features catégorielles encodées
        categorical_features = self.feature_engineer.get_categorical_features()
        
        # Garder seulement les colonnes disponibles
        available_numeric = [f for f in numeric_features if f in self.df_with_features.columns]
        available_categorical = [f for f in categorical_features if f in self.df_with_features.columns]
        
        ml_features = available_numeric + available_categorical
        
        self.log(f"Features numériques: {len(available_numeric)}")
        self.log(f"Features catégorielles: {len(available_categorical)}")
        self.log(f"Total features: {len(ml_features)}")
        
        # Créer X et y
        X = self.df_with_features[ml_features].copy()
        y = self.df_with_features['anomaly_label'].copy()
        
        # Gérer valeurs manquantes
        X = X.fillna(X.median(numeric_only=True))
        
        self.log(f"X shape: {X.shape}")
        self.log(f"y shape: {y.shape}")
        
        return X, y, ml_features
    
    
    # ============================================
    # ÉTAPE 5: EXPORT RÉSULTATS
    # ============================================
    
    def export_results(self, suffix=''):
        """
        Exporter résultats en CSV.
        
        Args:
            suffix (str): Suffixe pour nom fichiers
        """
        self.log(f"\n{'='*80}")
        self.log("ÉTAPE 5: EXPORT RÉSULTATS")
        self.log(f"{'='*80}\n")
        
        if self.df_with_features is None:
            raise ValueError("Données non traitées. Exécutez le pipeline complet d'abord.")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 1. Export complet
        output_file = os.path.join(
            self.output_dir,
            f'documents_with_labels_and_features{suffix}_{timestamp}.csv'
        )
        self.df_with_features.to_csv(output_file, index=False)
        self.log(f"✓ Export complet: {output_file}")
        
        # 2. Export labels uniquement
        labels_output = os.path.join(
            self.data_dir,
            'rule_based_labels',
            f'documents_labels{suffix}_{timestamp}.csv'
        )
        labels_df = self.df_with_features[[
            'purchasing_document_|_ebeln',
            'item_|_ebelp',
            'anomaly_label',
            'is_anomaly',
            'anomaly_type',
            'anomaly_severity',
            'anomaly_reason'
        ]].copy()
        labels_df.to_csv(labels_output, index=False)
        self.log(f"✓ Export labels: {labels_output}")
        
        # 3. Statistiques
        stats_file = os.path.join(
            self.output_dir,
            f'pipeline_statistics{suffix}_{timestamp}.txt'
        )
        
        with open(stats_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("SAP P2P PIPELINE STATISTICS\n")
            f.write("="*80 + "\n\n")
            
            f.write("DONNÉES BRUTES:\n")
            f.write(f"  Lignes: {len(self.df_raw):,}\n")
            f.write(f"  Colonnes: {len(self.df_raw.columns)}\n\n")
            
            f.write("APRÈS RÈGLES MÉTIER:\n")
            f.write(f"  Lignes: {len(self.df_with_labels):,}\n")
            f.write(f"  Réduction: {round((1 - len(self.df_with_labels)/len(self.df_raw))*100, 1)}%\n\n")
            
            f.write("DISTRIBUTION ANOMALIES:\n")
            for label, count in self.df_with_features['anomaly_label'].value_counts().items():
                pct = round(count / len(self.df_with_features) * 100, 2)
                f.write(f"  {label}: {count:,} ({pct}%)\n")
            
            f.write("\nFEATURES CRÉÉES:\n")
            for feature in self.feature_engineer.get_feature_list():
                f.write(f"  - {feature}\n")
        
        self.log(f"✓ Statistiques: {stats_file}")
        
        self.log("\n✅ EXPORT COMPLÉTÉ")
    
    
    # ============================================
    # PIPELINE COMPLET
    # ============================================
    
    def run_full_pipeline(self):
        """
        Exécuter pipeline complet.
        
        Returns:
            tuple: (df_final, X, y, features)
        """
        self.log("\n" + "🚀"*40)
        self.log("EXÉCUTION PIPELINE SAP P2P COMPLET")
        self.log("🚀"*40)
        
        # Étapes
        self.load_data()
        self.apply_business_rules()
        self.create_features()
        X, y, features = self.select_ml_features()
        self.export_results()
        
        self.df_final = self.df_with_features
        
        self.log("\n" + "✅"*40)
        self.log("PIPELINE RÉUSSI!")
        self.log("✅"*40 + "\n")
        
        return self.df_final, X, y, features
    
    
    # ============================================
    # UTILITAIRES
    # ============================================
    
    def get_anomalies_summary(self):
        """Résumé des anomalies détectées"""
        if self.df_with_features is None:
            return None
        
        summary = self.df_with_features['anomaly_label'].value_counts().to_dict()
        return summary
    
    
    def get_high_priority_anomalies(self, top_n=100):
        """Retourner anomalies haute priorité"""
        if self.df_with_features is None:
            return None
        
        high_priority = self.df_with_features[
            self.df_with_features['anomaly_severity'].isin(['CRITICAL', 'HIGH'])
        ].sort_values('anomaly_severity').head(top_n)
        
        if len(high_priority) == 0:
            return None
        
        # Build list of columns to select (only those that exist)
        cols_to_select = []
        
        # Core columns that must exist
        core_cols = ['purchasing_document_|_ebeln', 'item_|_ebelp', 'total_gr_amount', 
                     'total_ir_amount', 'anomaly_label', 'anomaly_severity']
        cols_to_select = [c for c in core_cols if c in high_priority.columns]
        
        # Supplier column (try both names) - add after item
        supplier_added = False
        if 'supplier_|_lifnr' in high_priority.columns:
            cols_to_select.insert(2, 'supplier_|_lifnr')
            supplier_added = True
        elif 'supplier_name' in high_priority.columns:
            cols_to_select.insert(2, 'supplier_name')
            supplier_added = True
        
        # If no supplier column, that's ok - just continue with available columns
        if not supplier_added:
            # Re-order to ensure core columns are in right positions
            cols_to_select = [c for c in core_cols if c in high_priority.columns]
        
        # Filter to only existing columns
        cols_to_select = [c for c in cols_to_select if c in high_priority.columns]
        
        if len(cols_to_select) > 0:
            return high_priority[cols_to_select]
        else:
            return high_priority
