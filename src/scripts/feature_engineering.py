"""
============================================
SAP P2P FEATURE ENGINEERING MODULE
============================================

Construction des features pour modèles ML.
Combine features métier (financières, temporelles, fournisseurs, opérationnelles).

Catégories de features:
A. Features Financières
B. Features Temporelles  
C. Features Fournisseurs
D. Features Opérationnelles
E. Features Catégorielles (encodage)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class FeatureEngineer:
    """
    Ingénierie des features pour modèles ML SAP P2P.
    """
    
    def __init__(self, verbose=True):
        """
        Initialisation.
        
        Args:
            verbose (bool): Afficher progression
        """
        self.verbose = verbose
        self.features_created = []
        self.feature_stats = {}
    
    
    def log(self, msg):
        """Afficher message si verbose"""
        if self.verbose:
            print(f"  🔧 {msg}")
    
    
    # ============================================
    # CATÉGORIE A: FEATURES FINANCIÈRES
    # ============================================
    
    def create_financial_features(self, df):
        """
        Créer features financières.
        
        Features:
        - total_gr_amount: Somme des montants GR
        - total_ir_amount: Somme des montants IR
        - gr_ir_difference: Écart IR - GR
        - abs_gr_ir_diff: Valeur absolue écart
        - invoice_ratio: IR / GR
        - unit_price: Prix unitaire
        - total_quantity: Quantité totale
        - amount_per_qty: Montant par unité
        
        Args:
            df (pd.DataFrame): Données
            
        Returns:
            pd.DataFrame: Données enrichies
        """
        self.log("FEATURES FINANCIÈRES...")
        
        df = df.copy()
        
        # Montants
        gr_col = 'amount_|_wrbtr_sum' if 'amount_|_wrbtr_sum' in df.columns else 'amount_|_wrbtr'
        ir_col = 'invoice_value_|_reewr_sum' if 'invoice_value_|_reewr_sum' in df.columns else 'invoice_value_|_reewr'
        
        df['total_gr_amount'] = df[gr_col].fillna(0)
        df['total_ir_amount'] = df[ir_col].fillna(0)
        df['gr_ir_difference'] = df['total_ir_amount'] - df['total_gr_amount']
        df['abs_gr_ir_diff'] = df['gr_ir_difference'].abs()
        
        # Ratio (gestion division par zéro)
        df['invoice_ratio'] = np.where(
            df['total_gr_amount'] > 0,
            df['total_ir_amount'] / df['total_gr_amount'],
            np.nan
        )
        
        # Prix et quantité
        df['unit_price'] = df.get('net_order_price_|_netpr', 0)
        qty_col = 'quantity_|_menge_sum' if 'quantity_|_menge_sum' in df.columns else 'quantity_|_menge'
        df['total_quantity'] = df[qty_col].fillna(0)
        
        # Montant par unité
        df['amount_per_qty'] = np.where(
            df['total_quantity'] > 0,
            df['total_gr_amount'] / df['total_quantity'],
            np.nan
        )
        
        # Pourcentage d'écart
        df['gr_ir_gap_pct'] = np.where(
            df['total_gr_amount'] > 0,
            (df['abs_gr_ir_diff'] / df['total_gr_amount'] * 100),
            0
        )
        
        # Montant bloqué
        df['blocked_amount'] = np.where(
            df['total_gr_amount'] > df['total_ir_amount'],
            df['total_gr_amount'] - df['total_ir_amount'],
            0
        )
        
        features_added = [
            'total_gr_amount', 'total_ir_amount', 'gr_ir_difference',
            'abs_gr_ir_diff', 'invoice_ratio', 'unit_price', 'total_quantity',
            'amount_per_qty', 'gr_ir_gap_pct', 'blocked_amount'
        ]
        
        self.features_created.extend(features_added)
        self.log(f"✓ {len(features_added)} features financières ajoutées")
        
        return df
    
    
    # ============================================
    # CATÉGORIE B: FEATURES TEMPORELLES
    # ============================================
    
    def create_temporal_features(self, df, reference_date=None):
        """
        Créer features temporelles.
        
        Features:
        - posting_date: Date comptable
        - document_date: Date document
        - days_in_system: Ancienneté
        - planned_delay: Retard vs planifié
        - posting_month: Mois (saisonnalité)
        - posting_quarter: Trimestre fiscal
        
        Args:
            df (pd.DataFrame): Données
            reference_date (datetime): Date de référence (défaut: aujourd'hui)
            
        Returns:
            pd.DataFrame: Données enrichies
        """
        self.log("FEATURES TEMPORELLES...")
        
        df = df.copy()
        
        if reference_date is None:
            reference_date = datetime.now()
        
        # Dates
        posting_col = 'posting_date_|_budat_min' if 'posting_date_|_budat_min' in df.columns else 'posting_date_|_budat'
        
        # Convertir en datetime
        df['posting_date'] = pd.to_datetime(df[posting_col], errors='coerce')
        
        # Jours dans le système
        df['days_in_system'] = (reference_date - df['posting_date']).dt.days
        df['days_in_system'] = df['days_in_system'].fillna(0).astype(int)
        
        # Features cycliques
        df['posting_month'] = df['posting_date'].dt.month
        df['posting_quarter'] = df['posting_date'].dt.quarter
        df['posting_day_of_week'] = df['posting_date'].dt.dayofweek
        df['posting_year'] = df['posting_date'].dt.year
        
        # Vieillissement GR/IR
        df['gr_ir_delay_flag'] = np.where(df['days_in_system'] > 30, 1, 0)
        df['gr_ir_critical_delay'] = np.where(df['days_in_system'] > 90, 1, 0)
        
        # Délai planifié vs réel
        if 'planned_deliv_time_|_plifz' in df.columns:
            df['planned_delay_days'] = df.get('planned_deliv_time_|_plifz', 0).fillna(0).astype(int)
        else:
            df['planned_delay_days'] = 0
        
        features_added = [
            'posting_date', 'days_in_system', 'posting_month', 'posting_quarter',
            'posting_day_of_week', 'posting_year', 'gr_ir_delay_flag',
            'gr_ir_critical_delay', 'planned_delay_days'
        ]
        
        self.features_created.extend(features_added)
        self.log(f"✓ {len(features_added)} features temporelles ajoutées")
        
        return df
    
    
    # ============================================
    # CATÉGORIE C: FEATURES FOURNISSEURS
    # ============================================
    
    def create_supplier_features(self, df):
        """
        Créer features au niveau fournisseur.
        
        Features:
        - supplier_transaction_count: Nb transactions du fournisseur
        - supplier_avg_amount: Montant moyen
        - supplier_anomaly_rate: Taux anomalies
        - supplier_delivery_delay_rate: Taux retard livraison
        
        Args:
            df (pd.DataFrame): Données
            
        Returns:
            pd.DataFrame: Données enrichies
        """
        self.log("FEATURES FOURNISSEURS...")
        
        df = df.copy()
        
        # Robust supplier column detection: prefer explicit lifnr, fall back to variants
        supplier_col = None

        if 'supplier_|_lifnr' in df.columns:
            supplier_col = 'supplier_|_lifnr'
        else:
            # look for any column containing 'lifnr' (e.g. 'supplier_|_lifnr_first')
            lifnr_candidates = [c for c in df.columns if 'lifnr' in c.lower()]
            if lifnr_candidates:
                supplier_col = lifnr_candidates[0]
            else:
                # look for supplier name style columns
                name_candidates = [c for c in df.columns if 'supplier' in c.lower() and 'name' in c.lower()]
                if name_candidates:
                    supplier_col = name_candidates[0]
                else:
                    # as a last resort, any 'name' column
                    any_name = [c for c in df.columns if 'name' in c.lower()]
                    if any_name:
                        supplier_col = any_name[0]

        # Vérifier si colonne exists
        if supplier_col is None or supplier_col not in df.columns:
            self.log(f"⚠️  Colonne fournisseur non trouvée: expected variants of 'supplier' or 'lifnr'")
            return df
        
        # Statistiques par fournisseur
        supplier_stats = df.groupby(supplier_col).agg({
            'total_gr_amount': ['sum', 'mean', 'std'],
            'is_anomaly': 'mean',  # Taux anomalies
            'days_in_system': 'mean',  # Ancienneté moyenne
        }).reset_index()
        
        # Flatten columns
        supplier_stats.columns = [
            supplier_col, 'supplier_total_spend',
            'supplier_avg_amount', 'supplier_std_amount',
            'supplier_anomaly_rate', 'supplier_avg_aging'
        ]
        
        # Merge back
        df = df.merge(supplier_stats, on=supplier_col, how='left')
        
        # Comptage transactions
        df['supplier_transaction_count'] = df.groupby(supplier_col)[supplier_col].transform('count')
        
        # Flags
        df['supplier_high_risk'] = np.where(df['supplier_anomaly_rate'] > 0.2, 1, 0)  # >20% anomalies
        df['supplier_high_volume'] = np.where(df['supplier_total_spend'] > df['supplier_total_spend'].quantile(0.75), 1, 0)
        
        features_added = [
            'supplier_transaction_count', 'supplier_total_spend',
            'supplier_avg_amount', 'supplier_std_amount',
            'supplier_anomaly_rate', 'supplier_avg_aging',
            'supplier_high_risk', 'supplier_high_volume'
        ]
        
        self.features_created.extend(features_added)
        self.log(f"✓ {len(features_added)} features fournisseur ajoutées")
        
        return df
    
    
    # ============================================
    # CATÉGORIE D: FEATURES OPÉRATIONNELLES
    # ============================================
    
    def create_operational_features(self, df):
        """
        Créer features opérationnelles.
        
        Features:
        - delivery_completed: Livraison complète
        - deletion_indicator: Article supprimé
        - has_outline_agreement: Accord-cadre
        - movement_type_count: Nb mouvements SAP
        
        Args:
            df (pd.DataFrame): Données
            
        Returns:
            pd.DataFrame: Données enrichies
        """
        self.log("FEATURES OPÉRATIONNELLES...")
        
        df = df.copy()
        
        # Livraison complète
        if 'delivery_completed_|_elikz_ekpo_max' in df.columns:
            df['delivery_completed'] = df['delivery_completed_|_elikz_ekpo_max']
        elif 'delivery_completed_|_elikz_ekpo' in df.columns:
            df['delivery_completed'] = df['delivery_completed_|_elikz_ekpo']
        else:
            df['delivery_completed'] = 0
        
        # Dates document
        date_cols = [col for col in df.columns if 'date' in col.lower()]
        if len(date_cols) > 0:
            df['document_date_known'] = 1
        else:
            df['document_date_known'] = 0
        
        # Accord-cadre
        if 'outline_agreement_|_konnr' in df.columns:
            df['has_outline_agreement'] = df['outline_agreement_|_konnr'].notna().astype(int)
        else:
            df['has_outline_agreement'] = 0
        
        # Termes de paiement
        if 'terms_of_payment_|_zterm' in df.columns:
            df['has_payment_terms'] = df['terms_of_payment_|_zterm'].notna().astype(int)
        else:
            df['has_payment_terms'] = 0
        
        features_added = [
            'delivery_completed', 'document_date_known',
            'has_outline_agreement', 'has_payment_terms'
        ]
        
        self.features_created.extend(features_added)
        self.log(f"✓ {len(features_added)} features opérationnelles ajoutées")
        
        return df
    
    
    # ============================================
    # CATÉGORIE E: FEATURES CATÉGORIELLES
    # ============================================
    
    def create_categorical_features(self, df):
        """
        Créer features catégorielles.
        
        Features:
        - plant: Usine
        - material_group: Groupe matériel
        - purch_org: Organisation achat
        - supplier_id: Fournisseur
        - po_type: Type de commande
        
        Args:
            df (pd.DataFrame): Données
            
        Returns:
            pd.DataFrame: Données enrichies
        """
        self.log("FEATURES CATÉGORIELLES...")
        
        df = df.copy()
        
        categorical_cols = [
            'plant_|_werks',
            'material_group_|_matkl',
            'purch_organization_|_ekorg',
            'supplier_|_lifnr',
            'purchasing_doc_type_|_bsart'
        ]
        
        features_added = []
        
        for col in categorical_cols:
            if col in df.columns:
                try:
                    df[col + '_encoded'] = pd.factorize(df[col])[0]
                    features_added.append(col + '_encoded')
                except Exception as e:
                    self.log(f"⚠️  Erreur encoding {col}: {str(e)}")
        
        self.features_created.extend(features_added)
        self.log(f"✓ {len(features_added)} features catégorielles ajoutées")
        
        return df
    
    
    # ============================================
    # PIPELINE COMPLET
    # ============================================
    
    def create_all_features(self, df, reference_date=None):
        """
        Pipeline complet de feature engineering.
        
        Args:
            df (pd.DataFrame): Données
            reference_date (datetime): Date de référence
            
        Returns:
            pd.DataFrame: Données enrichies
        """
        self.log("\n" + "="*80)
        self.log("FEATURE ENGINEERING COMPLET")
        self.log("="*80 + "\n")
        
        df = self.create_financial_features(df)
        df = self.create_temporal_features(df, reference_date)
        df = self.create_supplier_features(df)
        df = self.create_operational_features(df)
        df = self.create_categorical_features(df)
        
        self.log("\n" + "="*80)
        self.log(f"✅ {len(self.features_created)} FEATURES CRÉÉES")
        self.log("="*80 + "\n")
        
        return df
    
    
    def get_feature_list(self):
        """Retourner la liste des features créées"""
        return self.features_created
    
    
    def get_numeric_features(self):
        """Retourner features numériques"""
        numeric_features = [
            'total_gr_amount', 'total_ir_amount', 'gr_ir_difference',
            'abs_gr_ir_diff', 'invoice_ratio', 'unit_price', 'total_quantity',
            'amount_per_qty', 'gr_ir_gap_pct', 'blocked_amount',
            'days_in_system', 'posting_month', 'posting_quarter',
            'supplier_transaction_count', 'supplier_total_spend',
            'supplier_avg_amount', 'supplier_std_amount',
            'supplier_anomaly_rate', 'supplier_avg_aging'
        ]
        return numeric_features
    
    
    def get_categorical_features(self):
        """Retourner features catégorielles"""
        categorical_features = [
            'plant_|_werks_encoded',
            'material_group_|_matkl_encoded',
            'purch_organization_|_ekorg_encoded',
            'supplier_|_lifnr_encoded',
            'purchasing_doc_type_|_bsart_encoded'
        ]
        return categorical_features
