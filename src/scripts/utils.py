# ============================================
# UTILITIES MODULE
# ============================================
"""
Fonctions utilitaires réutilisables pour l'analyse FORVIA.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import json

# ============================================
# FIGURE MANAGEMENT
# ============================================

def save_fig(name, fig_dir="../docs/figures", dpi=150, bbox_inches='tight'):
    """
    Sauvegarde une figure Matplotlib.
    
    Args:
        name (str): Nom du fichier (sans extension)
        fig_dir (str): Répertoire de destination
        dpi (int): Résolution (default: 150)
        bbox_inches (str): Ajustement de la boîte (default: 'tight')
    """
    import re
    os.makedirs(fig_dir, exist_ok=True)
    
    # Nettoyer le nom du fichier
    name = re.sub(r'[^\w\-_\. ]', '_', str(name))
    if not name.endswith('.png'):
        name += '.png'
    
    filepath = os.path.join(fig_dir, name)
    plt.savefig(filepath, dpi=dpi, bbox_inches=bbox_inches)
    print(f"✅ Figure saved: {filepath}")
    return filepath


# ============================================
# DATA MANAGEMENT
# ============================================

def load_data(filepath, low_memory=False):
    """
    Charge un fichier CSV avec gestion d'erreurs.
    
    Args:
        filepath (str): Chemin du fichier
        low_memory (bool): Mode bas mémoire
        
    Returns:
        pd.DataFrame: Données chargées
    """
    try:
        df = pd.read_csv(filepath, low_memory=low_memory)
        print(f"✅ Data loaded: {filepath}")
        print(f"   Shape: {df.shape}")
        return df
    except Exception as e:
        print(f"❌ Error loading {filepath}: {str(e)}")
        return None


def save_data(df, filepath, index=False):
    """
    Sauvegarde un DataFrame en CSV.
    
    Args:
        df (pd.DataFrame): Données à sauvegarder
        filepath (str): Chemin de destination
        index (bool): Inclure l'index
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=index)
    print(f"✅ Data saved: {filepath}")


# ============================================
# DATA INSPECTION
# ============================================

def get_profile(df):
    """
    Crée un profil complet du DataFrame.
    
    Returns:
        pd.DataFrame: Profile avec type, unique, missing %
    """
    profile = pd.DataFrame({
        'Column': df.columns,
        'Type': df.dtypes.values,
        'Unique': df.nunique().values,
        'Missing': df.isnull().sum().values,
        'Missing_%': (df.isnull().sum() / len(df) * 100).round(2).values
    })
    return profile.sort_values('Missing_%', ascending=False)


# ============================================
# LOGGING
# ============================================

def log_step(step_name, message=""):
    """
    Log formaté pour les étapes d'analyse.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*80}")
    print(f"[{timestamp}] 🔄 {step_name}")
    if message:
        print(f"   {message}")
    print(f"{'='*80}")


def export_report(data, filepath, format='json'):
    """
    Exporte un rapport d'analyse.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    if format == 'json':
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    elif format == 'csv' and isinstance(data, pd.DataFrame):
        data.to_csv(filepath, index=False)
    
    print(f"✅ Report exported: {filepath}")


# ============================================
# SAP P2P HELPERS (NEW)
# ============================================

def get_sap_column_mapping():
    """
    Mapping des colonnes SAP vers noms lisibles.
    
    Returns:
        dict: Mapping colonnes SAP
    """
    mapping = {
        'purchasing_document_|_ebeln': 'PO_Number',
        'item_|_ebelp': 'PO_Item',
        'supplier_|_lifnr': 'Supplier_ID',
        'supplier_name': 'Supplier_Name',
        'plant_|_werks': 'Plant',
        'material_|_matnr': 'Material',
        'quantity_|_menge': 'Quantity',
        'amount_|_wrbtr': 'GR_Amount',
        'invoice_value_|_reewr': 'IR_Amount',
        'movement_type_|_bwart': 'Movement_Type',
        'posting_date_|_budat': 'Posting_Date',
        'delivery_completed_|_elikz_ekpo': 'Delivery_Completed',
        'deletion_indicator_|_loekz': 'Deletion_Flag',
    }
    return mapping


def describe_anomaly(anomaly_label):
    """
    Retourne description détaillée d'une anomalie.
    
    Args:
        anomaly_label (str): Label anomalie
        
    Returns:
        dict: Description, risques, actions
    """
    descriptions = {
        'OK': {
            'description': 'Flux normal: GR et IR présents',
            'risk': 'NONE',
            'action': 'Suivi normal',
            'priority': 0
        },
        'DELIVERED_NOT_INVOICED': {
            'description': 'Marchandise reçue (GR) mais pas de facture (IR)',
            'risk': 'ACCOUNTING - Facture manquante, retard comptable, GR/IR non soldé',
            'action': 'Relancer fournisseur pour facture',
            'priority': 2
        },
        'INVOICED_NOT_DELIVERED': {
            'description': 'Facture reçue (IR) mais pas de marchandise (GR)',
            'risk': 'FRAUD - Paiement sans réception, erreur comptable possible',
            'action': 'Vérifier réception marchandise, bloquer paiement si nécessaire',
            'priority': 1
        },
        'INCOMPLETE': {
            'description': 'Données incomplètes',
            'risk': 'DATA_QUALITY - GR et IR manquants',
            'action': 'Vérifier intégrité données',
            'priority': 3
        }
    }
    return descriptions.get(anomaly_label, {})


def get_sap_movement_types():
    """
    Retourne mapping des codes de mouvement SAP.
    
    Returns:
        dict: Code mouvement → Description
    """
    movements = {
        '101': 'Goods Receipt',
        '102': 'Goods Return',
        '201': 'Reversal Goods Receipt',
        '202': 'Reversal Goods Return',
        '301': 'Adjustment',
        '401': 'Scrap',
        '501': 'Transfer',
        '601': 'Consumption',
        '701': 'Production',
    }
    return movements


def calculate_anomaly_risk_score(row):
    """
    Calcule score de risque pour une transaction.
    
    Args:
        row (pd.Series): Ligne données
        
    Returns:
        int: Score 0-100
    """
    score = 0
    
    # Anomalie de base
    if row.get('is_anomaly', 0) == 1:
        base_score = 40
        
        # Montant
        if row.get('gr_ir_gap_pct', 0) > 50:
            score += 30
        elif row.get('gr_ir_gap_pct', 0) > 10:
            score += 15
        
        # Ancienneté
        if row.get('days_in_system', 0) > 90:
            score += 20
        elif row.get('days_in_system', 0) > 30:
            score += 10
        
        # Fournisseur risqué
        if row.get('supplier_high_risk', 0) == 1:
            score += 15
        
        return base_score + score
    
    return 0


def get_kpi_definitions():
    """
    Retourne définitions des KPI métier.
    
    Returns:
        dict: KPI et calculs
    """
    kpis = {
        'pct_unvoiced_deliveries': {
            'name': '% Commandes non facturées',
            'description': 'Pourcentage de GR sans IR',
            'calculation': 'COUNT(DELIVERED_NOT_INVOICED) / COUNT(*)',
            'threshold_alert': 5.0
        },
        'pct_undelivered_invoices': {
            'name': '% Factures sans livraison',
            'description': 'Pourcentage de IR sans GR',
            'calculation': 'COUNT(INVOICED_NOT_DELIVERED) / COUNT(*)',
            'threshold_alert': 2.0
        },
        'avg_gr_ir_delay': {
            'name': 'Délai moyen GR→IR',
            'description': 'Jours entre GR et IR',
            'calculation': 'AVG(days_between_gr_ir)',
            'threshold_alert': 30
        },
        'blocked_amount': {
            'name': 'Montant bloqué',
            'description': 'Total des écarts GR/IR',
            'calculation': 'SUM(blocked_amount)',
            'threshold_alert': 1000000
        },
        'supplier_anomaly_rate': {
            'name': 'Taux anomalie fournisseur',
            'description': '% anomalies par fournisseur',
            'calculation': 'COUNT(anomalies) / COUNT(*)',
            'threshold_alert': 0.20
        }
    }
    return kpis
