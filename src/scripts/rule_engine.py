"""
============================================
SAP P2P RULE-BASED ANOMALY DETECTION ENGINE
============================================

Détection d'anomalies basée sur les règles métier SAP.
Flux : PO → GR (Goods Receipt) → IR (Invoice Receipt) → GR/IR Clearing

Concept clé:
- GR = Livraison (Goods Receipt) - movement_type = 101
- IR = Facture (Invoice Receipt) - invoice_value > 0
- Anomalie = GR sans IR, IR sans GR, écarts montants

Reference: SAP P2P Process (Procure-to-Pay)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class RuleEngine:
    """
    Moteur de détection d'anomalies basé sur les règles SAP métier.
    """
    
    def __init__(self, verbose=True):
        """
        Initialisation du moteur de règles.
        
        Args:
            verbose (bool): Afficher les statistiques
        """
        self.verbose = verbose
        self.rules_applied = {}
        self.anomaly_stats = {}
    
    
    def log(self, msg):
        """Afficher message si verbose=True"""
        if self.verbose:
            print(f"  📌 {msg}")
    
    
    # ============================================
    # RÈGLE 1: FILTRAGE DONNÉES BRUTES
    # ============================================
    
    def filter_valid_transactions(self, df):
        """
        Étape 1: Filtrer les transactions valides.
        
        Critères:
        - amount_|_wrbtr IS NOT NULL (montant obligatoire)
        - deletion_indicator_|_loekz IS NULL (non supprimé)
        
        Args:
            df (pd.DataFrame): Données brutes
            
        Returns:
            pd.DataFrame: Données filtrées
        """
        self.log("ÉTAPE 1: Filtrage transactions valides...")
        
        initial_rows = len(df)
        
        # Filtre 1: Montant obligatoire
        df_filtered = df[df['amount_|_wrbtr'].notna()].copy()
        null_amount_count = initial_rows - len(df_filtered)
        self.log(f"Lignes avec amount NULL: {null_amount_count}")
        
        # Filtre 2: Non supprimé
        deletion_before = len(df_filtered)
        df_filtered = df_filtered[df_filtered['deletion_indicator_|_loekz'].isna()].copy()
        deleted_count = deletion_before - len(df_filtered)
        self.log(f"Lignes supprimées (loekz): {deleted_count}")
        
        self.rules_applied['filter_valid_transactions'] = {
            'initial': initial_rows,
            'final': len(df_filtered),
            'removed': initial_rows - len(df_filtered),
            'removal_pct': round((initial_rows - len(df_filtered)) / initial_rows * 100, 2)
        }
        
        return df_filtered
    
    
    # ============================================
    # RÈGLE 2: AGRÉGATION PAR PO + ITEM
    # ============================================
    
    def aggregate_by_po_item(self, df):
        """
        Étape 2: Agréger par clé métier = (PO, Item).
        
        Raison: Un même PO+Item peut avoir:
        - Plusieurs GR (livraisons partielles) - po_history_category_|_bewtp = 'E'
        - Plusieurs IR (facturations partielles) - po_history_category_|_bewtp = 'Q'
        - Retours (mouvements inverses)
        
        Args:
            df (pd.DataFrame): Données filtrées
            
        Returns:
            pd.DataFrame: Données agrégées
        """
        self.log("ÉTAPE 2: Agrégation par (PO, Item)...")
        
        agg_dict = {
            'amount_|_wrbtr': 'sum',              # Total GR amount
            'invoice_value_|_reewr': 'sum',       # Total IR amount
            'quantity_|_menge': 'sum',             # Total quantity
            'net_order_price_|_netpr': 'first',   # Unit price
            'supplier_|_lifnr': 'first',          # Supplier (ID)
            'supplier_name': 'first',             # Supplier (name) if present
            'plant_|_werks': 'first',              # Plant
            'material_|_matnr': 'first',           # Material
            'posting_date_|_budat': ['min', 'max'], # Date range
            'delivery_completed_|_elikz_ekpo': 'max', # Delivery completed flag
            'po_history_category_|_bewtp': lambda x: ''.join(x.unique()), # Track which categories present
        }
        
        df_agg = df.groupby(['purchasing_document_|_ebeln', 'item_|_ebelp']).agg(agg_dict).reset_index()
        
        # Flatten multiindex columns
        df_agg.columns = ['_'.join(col).strip('_') if col[1] else col[0] 
                          for col in df_agg.columns.values]
        
        self.log(f"Lignes avant agrégation: {len(df)}")
        self.log(f"Lignes après agrégation: {len(df_agg)}")
        self.log(f"Ratio réduction: {round(len(df) / len(df_agg), 1)}x")
        
        return df_agg
    
    
    # ============================================
    # RÈGLE 3: DÉTECTION GR & IR
    # ============================================
    
    def detect_gr_ir(self, df):
        """
        Étape 3: Détecter présence GR et IR.
        
        Logique SAP P2P:
        - GR (Goods Receipt): po_history_category_|_bewtp = 'E' (E = Eingang/Receipt)
        - IR (Invoice Receipt): po_history_category_|_bewtp = 'Q' (Q = Quittung/Invoice)
        
        Args:
            df (pd.DataFrame): Données agrégées
            
        Returns:
            pd.DataFrame: Données avec flags GR/IR
        """
        self.log("ÉTAPE 3: Détection GR & IR...")
        
        df = df.copy()
        
        # Flag GR: 'E' dans po_history_category_|_bewtp
        if 'po_history_category_|_bewtp' in df.columns:
            df['has_gr'] = df['po_history_category_|_bewtp'].astype(str).str.contains('E', na=False).astype(int)
        else:
            # Fallback si colonne n'existe pas
            df['has_gr'] = (df.get('amount_|_wrbtr_sum', df.get('amount_|_wrbtr', 0)) > 0).astype(int)
        
        # Flag IR: 'Q' dans po_history_category_|_bewtp
        if 'po_history_category_|_bewtp' in df.columns:
            df['has_ir'] = df['po_history_category_|_bewtp'].astype(str).str.contains('Q', na=False).astype(int)
        else:
            # Fallback si colonne n'existe pas
            df['has_ir'] = (df.get('invoice_value_|_reewr_sum', df.get('invoice_value_|_reewr', 0)) > 0).astype(int)
        
        # Statistiques
        gr_count = df['has_gr'].sum()
        ir_count = df['has_ir'].sum()
        both_count = ((df['has_gr'] == 1) & (df['has_ir'] == 1)).sum()
        
        self.log(f"Transactions avec GR (E): {gr_count} ({round(gr_count/len(df)*100, 1)}%)")
        self.log(f"Transactions avec IR (Q): {ir_count} ({round(ir_count/len(df)*100, 1)}%)")
        self.log(f"Transactions avec GR+IR: {both_count} ({round(both_count/len(df)*100, 1)}%)")
        
        return df
    
    
    # ============================================
    # RÈGLE 4: CLASSIFICATION ANOMALIES
    # ============================================
    
    def classify_anomalies(self, df):
        """
        Étape 4: Classifier les anomalies.
        
        Matrice de règles:
        has_gr=1, has_ir=1 → OK (normal)
        has_gr=1, has_ir=0 → DELIVERED_NOT_INVOICED (risque: facture manquante)
        has_gr=0, has_ir=1 → INVOICED_NOT_DELIVERED (risque: paiement sans réception)
        has_gr=0, has_ir=0 → INCOMPLETE (données incomplètes)
        
        Args:
            df (pd.DataFrame): Données avec flags GR/IR
            
        Returns:
            pd.DataFrame: Données avec labels anomalies
        """
        self.log("ÉTAPE 4: Classification anomalies...")
        
        df = df.copy()
        
        # Création labels
        def classify_row(row):
            has_gr = row['has_gr']
            has_ir = row['has_ir']
            
            if has_gr == 1 and has_ir == 1:
                return 'OK'
            elif has_gr == 1 and has_ir == 0:
                return 'DELIVERED_NOT_INVOICED'
            elif has_gr == 0 and has_ir == 1:
                return 'INVOICED_NOT_DELIVERED'
            else:
                return 'INCOMPLETE'
        
        df['anomaly_label'] = df.apply(classify_row, axis=1)
        
        # Statistiques
        label_stats = df['anomaly_label'].value_counts()
        self.log("Distribution des labels:")
        for label, count in label_stats.items():
            pct = round(count / len(df) * 100, 2)
            self.log(f"  {label}: {count} ({pct}%)")
        
        self.anomaly_stats = label_stats.to_dict()
        
        return df
    
    
    # ============================================
    # RÈGLE 5: FLAGS ANOMALIES DÉTAILLÉES
    # ============================================
    
    def add_anomaly_details(self, df):
        """
        Étape 5: Ajouter flags d'anomalies détaillées.
        
        Flags:
        - is_anomaly: Oui/Non
        - anomaly_type: Type spécifique
        - anomaly_severity: Critique/Haute/Moyenne/Basse
        - anomaly_reason: Description pour audit
        
        Args:
            df (pd.DataFrame): Données classifiées
            
        Returns:
            pd.DataFrame: Données enrichies
        """
        self.log("ÉTAPE 5: Flags anomalies détaillées...")
        
        df = df.copy()
        
        # Flag principal
        df['is_anomaly'] = (df['anomaly_label'] != 'OK').astype(int)
        
        # Type d'anomalie
        df['anomaly_type'] = df['anomaly_label'].apply(
            lambda x: 'ACCOUNTING' if x == 'DELIVERED_NOT_INVOICED' 
            else ('FRAUD' if x == 'INVOICED_NOT_DELIVERED' 
            else ('DATA' if x == 'INCOMPLETE' else 'NONE'))
        )
        
        # Sévérité
        def severity(row):
            if row['anomaly_label'] == 'OK':
                return 'NONE'
            elif row['anomaly_label'] == 'INVOICED_NOT_DELIVERED':
                return 'CRITICAL'  # Paiement sans réception = risque fraude
            elif row['anomaly_label'] == 'DELIVERED_NOT_INVOICED':
                return 'HIGH'       # Facture manquante = risque comptable
            else:
                return 'MEDIUM'
        
        df['anomaly_severity'] = df.apply(severity, axis=1)
        
        # Raison en texte
        def reason(row):
            if row['anomaly_label'] == 'OK':
                return 'Flux normal: GR et IR présents'
            elif row['anomaly_label'] == 'DELIVERED_NOT_INVOICED':
                return 'Marchandise reçue (GR) mais pas de facture (IR)'
            elif row['anomaly_label'] == 'INVOICED_NOT_DELIVERED':
                return 'Facture reçue (IR) mais pas de marchandise (GR)'
            else:
                return 'Données incomplètes pour cette ligne'
        
        df['anomaly_reason'] = df.apply(reason, axis=1)
        
        # Comptage anomalies
        anomalies_count = df['is_anomaly'].sum()
        self.log(f"Total anomalies détectées: {anomalies_count} ({round(anomalies_count/len(df)*100, 2)}%)")
        
        return df
    
    
    # ============================================
    # RÈGLE 6: ÉCARTS MONTANTS
    # ============================================
    
    def calculate_amount_gaps(self, df):
        """
        Étape 6: Calculer écarts montants GR vs IR.
        
        Écarts:
        - gr_amount: Montant GR
        - ir_amount: Montant IR
        - amount_difference: IR - GR
        - abs_amount_diff: |IR - GR|
        - invoice_ratio: IR / GR (si GR > 0)
        
        Seuils d'alerte:
        - > 10%: écart détecté
        - > 50%: écart significatif
        
        Args:
            df (pd.DataFrame): Données avec anomalies
            
        Returns:
            pd.DataFrame: Données avec écarts
        """
        self.log("ÉTAPE 6: Calcul écarts montants...")
        
        df = df.copy()
        
        # Colonnes montants
        gr_col = 'amount_|_wrbtr_sum' if 'amount_|_wrbtr_sum' in df.columns else 'amount_|_wrbtr'
        ir_col = 'invoice_value_|_reewr_sum' if 'invoice_value_|_reewr_sum' in df.columns else 'invoice_value_|_reewr'
        
        df['gr_amount'] = df[gr_col].fillna(0)
        df['ir_amount'] = df[ir_col].fillna(0)
        
        # Écarts
        df['amount_difference'] = df['ir_amount'] - df['gr_amount']
        df['abs_amount_diff'] = df['amount_difference'].abs()
        
        # Ratio
        df['invoice_ratio'] = np.where(
            df['gr_amount'] > 0,
            df['ir_amount'] / df['gr_amount'],
            np.nan
        )
        
        # Flags d'écarts
        df['has_amount_gap'] = (df['abs_amount_diff'] > (df['gr_amount'] * 0.10)).astype(int)
        df['has_significant_gap'] = (df['abs_amount_diff'] > (df['gr_amount'] * 0.50)).astype(int)
        
        gap_count = df['has_amount_gap'].sum()
        sig_gap_count = df['has_significant_gap'].sum()
        
        self.log(f"Écarts montants (>10%): {gap_count}")
        self.log(f"Écarts significatifs (>50%): {sig_gap_count}")
        
        return df
    
    
    # ============================================
    # PIPELINE COMPLET
    # ============================================
    
    def detect_anomalies(self, df):
        """
        Pipeline complet de détection d'anomalies.
        
        Args:
            df (pd.DataFrame): Données brutes
            
        Returns:
            pd.DataFrame: Données avec labels et anomalies
        """
        self.log("\n" + "="*80)
        self.log("PIPELINE DÉTECTION ANOMALIES SAP P2P")
        self.log("="*80 + "\n")
        
        # Étapes
        df = self.filter_valid_transactions(df)
        df = self.aggregate_by_po_item(df)
        df = self.detect_gr_ir(df)
        df = self.classify_anomalies(df)
        df = self.add_anomaly_details(df)
        df = self.calculate_amount_gaps(df)
        
        self.log("\n" + "="*80)
        self.log("✅ PIPELINE COMPLÉTÉ")
        self.log("="*80 + "\n")
        
        return df
    
    
    def get_statistics(self):
        """Retourner les statistiques d'application des règles"""
        return {
            'rules_applied': self.rules_applied,
            'anomaly_stats': self.anomaly_stats
        }
