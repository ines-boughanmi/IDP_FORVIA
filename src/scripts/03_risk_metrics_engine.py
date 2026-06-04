"""
Risk Metrics Engine - Phase 2
Generates intelligent purchasing alerts by analyzing contract coverage, 
expiration timelines, and spending gaps.

Output: data/processed/06_intelligent_alerts.csv
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def load_data():
    """Load Ariba and SAP data sources and detect supplier columns."""
    print("Loading data sources...")
    ariba = pd.read_csv('data/raw/Ariba Contract.csv')
    sap = pd.read_csv('data/raw/Documents1.csv')

    # Detect supplier id and name columns robustly
    supplier_id_col = 'supplier_|_lifnr' if 'supplier_|_lifnr' in sap.columns else next((c for c in sap.columns if 'lifnr' in c.lower()), None)
    supplier_name_col = 'supplier_name' if 'supplier_name' in sap.columns else next((c for c in sap.columns if 'supplier' in c.lower() and 'name' in c.lower()), None)

    n_ariba_sups = len(ariba['ariba_erp_vendor_id'].unique()) if 'ariba_erp_vendor_id' in ariba.columns else 0
    n_sap_sups = len(sap[supplier_id_col].unique()) if supplier_id_col in sap.columns else (sap[supplier_name_col].nunique() if supplier_name_col in sap.columns else 0)

    print(f"  ✓ Ariba: {len(ariba)} contracts from {n_ariba_sups} suppliers")
    print(f"  ✓ SAP: {len(sap)} documents from {n_sap_sups} suppliers (id_col={supplier_id_col}, name_col={supplier_name_col})")

    return ariba, sap, supplier_id_col, supplier_name_col

def normalize_supplier_ids(data, col_name):
    """Normalize supplier IDs to 10-digit format."""
    return data[col_name].astype(str).str.zfill(10).unique()

def signal_1_contract_coverage(ariba, sap, supplier_id_col='supplier_|_lifnr', supplier_name_col=None):
    """
    Signal 1: Which suppliers have Ariba contracts?
    Identifies uncontracted spending risk.
    """
    print("\n[SIGNAL 1] Contract Coverage Analysis")
    
    ariba_sups = set(normalize_supplier_ids(ariba, 'ariba_erp_vendor_id'))

    # Aggregate SAP by detected supplier id column
    if supplier_id_col and supplier_id_col in sap.columns:
        group_key = supplier_id_col
    elif supplier_name_col and supplier_name_col in sap.columns:
        # fallback to grouping by name if no id available
        group_key = supplier_name_col
    else:
        raise ValueError('No supplier id or name column found in SAP data')

    sap_agg = sap.groupby(group_key).agg({
        'amount_|_wrbtr': 'sum',
        'purchasing_document_|_ebeln': 'count'
    }).reset_index()

    # Normalize column names
    sap_agg.columns = [group_key, 'total_spend', 'num_docs']
    sap_agg = sap_agg.rename(columns={group_key: 'supplier_id_raw'})

    # If supplier name column exists, try to attach name
    if supplier_name_col and supplier_name_col in sap.columns:
        mapping = sap[[supplier_id_col, supplier_name_col]].drop_duplicates() if supplier_id_col and supplier_id_col in sap.columns else sap[[supplier_name_col]].drop_duplicates()
        if supplier_id_col and supplier_id_col in mapping.columns:
            mapping = mapping.rename(columns={supplier_id_col: 'supplier_id_raw', supplier_name_col: 'supplier_name'})
        else:
            mapping = mapping.rename(columns={supplier_name_col: 'supplier_name'})
        sap_agg = sap_agg.merge(mapping, on='supplier_id_raw', how='left')
    else:
        sap_agg['supplier_name'] = None

    # create normalized supplier id used for contract matching
    sap_agg['supplier_id'] = sap_agg['supplier_id_raw'].astype(str).str.zfill(10)
    sap_agg['has_contract'] = sap_agg['supplier_id'].isin(ariba_sups)
    
    with_contract = sap_agg['has_contract'].sum()
    without_contract = (~sap_agg['has_contract']).sum()
    uncontracted_spend = sap_agg[~sap_agg['has_contract']]['total_spend'].sum()
    total_spend = sap_agg['total_spend'].sum()
    
    print(f"  - Suppliers with contract: {with_contract} ({with_contract/len(sap_agg)*100:.1f}%)")
    print(f"  - Suppliers WITHOUT contract: {without_contract} ({without_contract/len(sap_agg)*100:.1f}%)")
    print(f"  - Uncontracted spending: EUR {uncontracted_spend:,.0f} ({uncontracted_spend/total_spend*100:.1f}%)")
    
    return sap_agg, ariba_sups, uncontracted_spend, total_spend

def signal_2_expiration_timeline(ariba):
    """
    Signal 2: Contract expiration timeline.
    Identifies contracts nearing or past expiration.
    """
    print("\n[SIGNAL 2] Expiration Timeline Analysis")
    
    ariba['expiry_dt'] = pd.to_datetime(
        ariba['contract_expiration_date'].apply(lambda x: x if x > 0 else None),
        unit='ms', errors='coerce'
    )
    today = datetime(2026, 4, 3)  # Current date
    ariba['days_to_expiry'] = (ariba['expiry_dt'] - today).dt.days
    
    expired = (ariba['days_to_expiry'] < 0).sum()
    expiring_j90 = ((ariba['days_to_expiry'] >= 0) & (ariba['days_to_expiry'] <= 90)).sum()
    expiring_j180 = ((ariba['days_to_expiry'] >= 90) & (ariba['days_to_expiry'] <= 180)).sum()
    
    print(f"  - Expired contracts: {expired}")
    print(f"  - Expiring <90 days: {expiring_j90}")
    print(f"  - Expiring <180 days: {expiring_j180}")
    
    return ariba

def signal_3_inactive_contracts(ariba_sups, sap_agg):
    """
    Signal 3: Inactive contracts.
    Identifies contracts with no SAP spending.
    """
    print("\n[SIGNAL 3] Inactive Contract Analysis")
    
    inactive_suppliers = []
    for supplier in ariba_sups:
        if supplier not in sap_agg['supplier_id'].values:
            inactive_suppliers.append(supplier)
    
    print(f"  - Suppliers with contract but zero spend: {len(inactive_suppliers)}")
    
    return inactive_suppliers

def generate_alerts(sap_agg, ariba, ariba_sups, inactive_suppliers, uncontracted_spend, total_spend):
    """Generate 16 intelligent alerts from signals."""
    print("\n[ALERTS] Generating governance alerts...")
    
    alerts = []
    
    # ALERT TYPE 1: Uncontracted Spending (Top 5 spenders without contracts)
    uncontracted = sap_agg[~sap_agg['has_contract']].nlargest(5, 'total_spend')
    for idx, row in uncontracted.iterrows():
        alerts.append({
            'alert_id': f"UNCTR_{row['supplier_id']}",
            'type': 'UNCONTRACTED_SPENDING',
            'severity': 'HIGH',
            'supplier_id': row['supplier_id'],
            'supplier_name': row.get('supplier_name', None),
            'description': f"Supplier {row['supplier_id']} spending EUR {row['total_spend']:,.0f} WITHOUT Ariba contract",
            'amount_eur': row['total_spend'],
            'doc_count': row['num_docs'],
            'recommendation': 'Require contract review before next purchase',
            'contract_id': None,
            'expiration_date': None,
            'days_remaining': None,
            'contract_count': None
        })
    
    # ALERT TYPE 2: Expired Contracts (Still in use)
    expired = ariba[ariba['days_to_expiry'] < 0]
    for idx, row in expired.iterrows():
        alerts.append({
            'alert_id': f"EXP_{row['contract_id']}",
            'type': 'EXPIRED_CONTRACT',
            'severity': 'CRITICAL',
            'supplier_id': row['ariba_erp_vendor_id'],
            'supplier_name': row.get('ariba_erp_vendor_name', None),
            'description': f"Contract {row['contract_id']} EXPIRED {abs(row['days_to_expiry']):.0f} days ago",
            'amount_eur': None,
            'doc_count': None,
            'recommendation': 'Renewal urgently needed',
            'contract_id': row['contract_id'],
            'expiration_date': row['expiry_dt'].strftime('%Y-%m-%d') if pd.notna(row['expiry_dt']) else None,
            'days_remaining': row['days_to_expiry'],
            'contract_count': None
        })
    
    # ALERT TYPE 3: Expiring Soon (Next 90 days)
    expiring_soon = ariba[(ariba['days_to_expiry'] >= 0) & (ariba['days_to_expiry'] <= 90)]
    for idx, row in expiring_soon.iterrows():
        alerts.append({
            'alert_id': f"EXP90_{row['contract_id']}",
            'type': 'EXPIRING_SOON',
            'severity': 'HIGH',
            'supplier_id': row['ariba_erp_vendor_id'],
            'supplier_name': row.get('ariba_erp_vendor_name', None),
            'description': f"Contract {row['contract_id']} expires in {row['days_to_expiry']:.0f} days",
            'amount_eur': None,
            'doc_count': None,
            'recommendation': 'Initiate renewal process immediately',
            'contract_id': row['contract_id'],
            'expiration_date': None,
            'days_remaining': row['days_to_expiry'],
            'contract_count': None
        })
    
    # ALERT TYPE 4: Inactive Contracts (Zero SAP spend)
    ariba_with_contracts = ariba[ariba['ariba_erp_vendor_id'].isin(inactive_suppliers)]
    for supplier in inactive_suppliers[:5]:  # Limit to 5
        contracts = ariba[ariba['ariba_erp_vendor_id'] == supplier]
        if len(contracts) > 0:
            alerts.append({
                'alert_id': f"INACT_{supplier}",
                'type': 'INACTIVE_CONTRACT',
                'severity': 'MEDIUM',
                    'supplier_id': supplier,
                    'supplier_name': None,
                'description': f"Supplier {supplier} has {len(contracts)} active contract(s) but ZERO SAP spend",
                'amount_eur': None,
                'doc_count': None,
                'recommendation': 'Review contract necessity or activate purchasing',
                'contract_id': None,
                'expiration_date': None,
                'days_remaining': None,
                'contract_count': len(contracts)
            })
    
    alerts_df = pd.DataFrame(alerts)
    print(f"  ✓ Generated {len(alerts_df)} alerts across 4 types")
    
    return alerts_df

def export_alerts(alerts_df):
    """Export alerts to CSV."""
    os.makedirs('data/processed', exist_ok=True)
    output_path = 'data/processed/06_intelligent_alerts.csv'
    alerts_df.to_csv(output_path, index=False)
    print(f"\n✓ Alerts exported to {output_path}")
    print(f"\nAlert Summary:")
    for alert_type, count in alerts_df['type'].value_counts().items():
        print(f"  - {alert_type}: {count}")

def main():
    """Main execution."""
    print("="*80)
    print("RISK METRICS ENGINE - Phase 2")
    print("="*80)
    
    # Load data
    ariba, sap, supplier_id_col, supplier_name_col = load_data()

    # Signal 1: Contract Coverage
    sap_agg, ariba_sups, uncontracted_spend, total_spend = signal_1_contract_coverage(ariba, sap, supplier_id_col, supplier_name_col)
    
    # Signal 2: Expiration Timeline
    ariba = signal_2_expiration_timeline(ariba)
    
    # Signal 3: Inactive Contracts
    inactive_suppliers = signal_3_inactive_contracts(ariba_sups, sap_agg)
    
    # Generate Alerts
    alerts_df = generate_alerts(sap_agg, ariba, ariba_sups, inactive_suppliers, uncontracted_spend, total_spend)
    
    # Export
    export_alerts(alerts_df)
    
    print("\n" + "="*80)
    print("EXECUTION COMPLETE")
    print("="*80)

if __name__ == '__main__':
    main()
