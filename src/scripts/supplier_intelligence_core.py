#!/usr/bin/env python
"""
PHASE 2 — Advanced Supplier Intelligence
==========================================

Task 1: Supplier Behavioral Feature Engineering
Task 2: Advanced Supplier Risk Engine
Task 3-4: Clustering & Validation
Task 5: Explainability
Task 6-7: Datasets & Visualizations

Main module: Supplier behavior extraction and analysis
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

from scipy import stats
from datetime import datetime, timedelta


class SupplierBehavioralFeatures:
    """
    Engineer comprehensive behavioral features for each supplier.
    
    Categories:
    - Temporal features (delays, consistency, trends)
    - Financial features (amounts, volatility, extremes)
    - Behavioral features (frequency, anomalies, stability)
    - Business features (diversity, patterns, process consistency)
    """
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.supplier_features = None
        
    def log(self, msg):
        if self.verbose:
            print(f"  {msg}")
    
    # =========================================================================
    # TEMPORAL FEATURES
    # =========================================================================
    
    def compute_temporal_features(self, df):
        """
        Compute temporal behavior metrics per supplier.
        """
        self.log("Computing temporal features...")
        
        temporal_features = {}
        
        for supplier_id in df['supplier_id'].unique():
            supplier_data = df[df['supplier_id'] == supplier_id]
            
            # Average days in system (aging)
            if 'days_in_system' in df.columns:
                avg_aging = supplier_data['days_in_system'].mean()
                std_aging = supplier_data['days_in_system'].std()
                max_aging = supplier_data['days_in_system'].max()
            else:
                avg_aging = std_aging = max_aging = 0
            
            # Transaction recency (assume indexed by time or transaction order)
            recency_score = 1.0 / (1.0 + np.log1p(len(supplier_data)))
            
            # Temporal consistency (low std = consistent)
            temporal_consistency = 1.0 / (1.0 + (std_aging / (avg_aging + 1)))
            
            temporal_features[supplier_id] = {
                'avg_aging_days': avg_aging,
                'std_aging_days': std_aging,
                'max_aging_days': max_aging,
                'recency_score': recency_score,
                'temporal_consistency': temporal_consistency,
            }
        
        return temporal_features
    
    # =========================================================================
    # FINANCIAL FEATURES
    # =========================================================================
    
    def compute_financial_features(self, df):
        """
        Compute financial behavior metrics per supplier.
        """
        self.log("Computing financial features...")
        
        financial_features = {}
        
        # Determine amount column
        amount_col = 'total_gr_amount' if 'total_gr_amount' in df.columns else 'gr_amount'
        
        for supplier_id in df['supplier_id'].unique():
            supplier_data = df[df['supplier_id'] == supplier_id]
            
            # Amount statistics
            amounts = supplier_data[amount_col].fillna(0)
            avg_amount = amounts.mean()
            std_amount = amounts.std()
            min_amount = amounts.min()
            max_amount = amounts.max()
            
            # Coefficient of variation (volatility)
            if avg_amount > 0:
                cv = std_amount / avg_amount
            else:
                cv = 0
            
            # High-value transaction ratio
            if len(amounts) > 0:
                p75 = np.percentile(amounts, 75)
                high_value_ratio = (amounts > p75).sum() / len(amounts) if p75 > 0 else 0
            else:
                high_value_ratio = 0
            
            # Abnormal amount ratio (>3 std from mean)
            if std_amount > 0:
                abnormal_mask = np.abs(amounts - avg_amount) > (3 * std_amount)
                abnormal_ratio = abnormal_mask.sum() / len(amounts)
            else:
                abnormal_ratio = 0
            
            financial_features[supplier_id] = {
                'avg_transaction_amount': avg_amount,
                'std_transaction_amount': std_amount,
                'min_transaction_amount': min_amount,
                'max_transaction_amount': max_amount,
                'amount_volatility_cv': cv,
                'high_value_transaction_ratio': high_value_ratio,
                'abnormal_amount_ratio': abnormal_ratio,
            }
        
        return financial_features
    
    # =========================================================================
    # BEHAVIORAL FEATURES
    # =========================================================================
    
    def compute_behavioral_features(self, df):
        """
        Compute behavioral metrics per supplier.
        """
        self.log("Computing behavioral features...")
        
        behavioral_features = {}
        
        for supplier_id in df['supplier_id'].unique():
            supplier_data = df[df['supplier_id'] == supplier_id]
            
            # Transaction frequency
            transaction_count = len(supplier_data)
            
            # Anomaly statistics
            if 'anomaly_class' in df.columns:
                anomaly_count = (supplier_data['anomaly_class'] != 'NONE').sum()
                anomaly_ratio = anomaly_count / len(supplier_data) if len(supplier_data) > 0 else 0
            else:
                anomaly_count = 0
                anomaly_ratio = 0
            
            # Accounting issue ratio
            if 'anomaly_class' in df.columns:
                accounting_count = (supplier_data['anomaly_class'] == 'ACCOUNTING').sum()
                accounting_ratio = accounting_count / len(supplier_data) if len(supplier_data) > 0 else 0
            else:
                accounting_ratio = 0
            
            # Data issue ratio
            if 'anomaly_class' in df.columns:
                data_count = (supplier_data['anomaly_class'] == 'DATA').sum()
                data_ratio = data_count / len(supplier_data) if len(supplier_data) > 0 else 0
            else:
                data_ratio = 0
            
            # Frequency irregularity
            if transaction_count > 1:
                # If we had monthly data, we'd compute coefficient of variation in frequency
                # For now, estimate from distribution spread
                frequency_irregularity = 0.5  # Placeholder
            else:
                frequency_irregularity = 1.0
            
            # Risk evolution trend (0=stable, 1=worsening, -1=improving)
            if len(supplier_data) > 10:
                first_half_risk = supplier_data.iloc[:len(supplier_data)//2]['risk_score_transaction'].mean()
                second_half_risk = supplier_data.iloc[len(supplier_data)//2:]['risk_score_transaction'].mean()
                if first_half_risk > 0:
                    risk_trend = (second_half_risk - first_half_risk) / first_half_risk
                else:
                    risk_trend = 0
            else:
                risk_trend = 0
            
            # Supplier stability score
            stability_score = 1.0 / (1.0 + anomaly_ratio) * (1.0 - frequency_irregularity)
            
            behavioral_features[supplier_id] = {
                'transaction_frequency': transaction_count,
                'frequency_irregularity': frequency_irregularity,
                'anomaly_ratio': anomaly_ratio,
                'accounting_issue_ratio': accounting_ratio,
                'data_issue_ratio': data_ratio,
                'risk_evolution_trend': risk_trend,
                'supplier_stability_score': stability_score,
                'anomaly_count': anomaly_count,
                'accounting_count': accounting_count,
                'data_count': data_count,
            }
        
        return behavioral_features
    
    # =========================================================================
    # BUSINESS FEATURES
    # =========================================================================
    
    def compute_business_features(self, df):
        """
        Compute business-level metrics per supplier.
        """
        self.log("Computing business features...")
        
        business_features = {}
        
        for supplier_id in df['supplier_id'].unique():
            supplier_data = df[df['supplier_id'] == supplier_id]
            
            # Number of unique POs
            po_col = 'purchasing_document_|_ebeln' if 'purchasing_document_|_ebeln' in df.columns else None
            if po_col:
                unique_pos = supplier_data[po_col].nunique()
            else:
                unique_pos = 0
            
            # Process consistency (repeated patterns)
            if len(supplier_data) > 5:
                # If same PO appears multiple times, indicates repeat orders
                po_value_counts = supplier_data[po_col].value_counts() if po_col else pd.Series()
                repeat_po_ratio = (po_value_counts > 1).sum() / len(po_value_counts) if len(po_value_counts) > 0 else 0
            else:
                repeat_po_ratio = 0
            
            # Duplicate transaction ratio (same amount, same day)
            if 'total_gr_amount' in df.columns:
                amount_col = 'total_gr_amount'
            else:
                amount_col = 'gr_amount'
            
            supplier_amounts = supplier_data[amount_col].fillna(0)
            value_counts = supplier_amounts.value_counts()
            if len(value_counts) > 0:
                duplicate_ratio = (value_counts > 1).sum() / len(value_counts)
            else:
                duplicate_ratio = 0
            
            # Business diversity (spread across different categories if available)
            business_diversity = min(unique_pos / max(len(supplier_data), 1), 1.0)
            
            business_features[supplier_id] = {
                'unique_pos': unique_pos,
                'repeat_po_ratio': repeat_po_ratio,
                'duplicate_transaction_ratio': duplicate_ratio,
                'business_diversity': business_diversity,
            }
        
        return business_features
    
    # =========================================================================
    # CONSOLIDATE ALL FEATURES
    # =========================================================================
    
    def create_supplier_feature_matrix(self, df):
        """
        Create comprehensive supplier feature matrix.
        """
        print("\n[SUPPLIER FEATURE ENGINEERING]")
        print("-" * 80)
        
        temporal = self.compute_temporal_features(df)
        financial = self.compute_financial_features(df)
        behavioral = self.compute_behavioral_features(df)
        business = self.compute_business_features(df)
        
        # Consolidate into dataframe
        supplier_ids = list(temporal.keys())
        feature_dict = {
            'supplier_id': supplier_ids,
        }
        
        # Add all features
        for feature_name in temporal[supplier_ids[0]].keys():
            feature_dict[f'temporal_{feature_name}'] = [
                temporal[sid].get(feature_name, 0) for sid in supplier_ids
            ]
        
        for feature_name in financial[supplier_ids[0]].keys():
            feature_dict[f'financial_{feature_name}'] = [
                financial[sid].get(feature_name, 0) for sid in supplier_ids
            ]
        
        for feature_name in behavioral[supplier_ids[0]].keys():
            feature_dict[f'behavioral_{feature_name}'] = [
                behavioral[sid].get(feature_name, 0) for sid in supplier_ids
            ]
        
        for feature_name in business[supplier_ids[0]].keys():
            feature_dict[f'business_{feature_name}'] = [
                business[sid].get(feature_name, 0) for sid in supplier_ids
            ]
        
        df_features = pd.DataFrame(feature_dict)
        
        print(f"\n✓ Feature Matrix Created:")
        print(f"  Suppliers: {len(df_features)}")
        print(f"  Features: {len(df_features.columns) - 1}")
        print(f"  Temporal features: {len(temporal[supplier_ids[0]])}")
        print(f"  Financial features: {len(financial[supplier_ids[0]])}")
        print(f"  Behavioral features: {len(behavioral[supplier_ids[0]])}")
        print(f"  Business features: {len(business[supplier_ids[0]])}")
        
        self.supplier_features = df_features
        
        return df_features


class AdvancedSupplierRiskEngine:
    """
    Advanced supplier risk scoring using behavioral features.
    """
    
    def __init__(self, verbose=True):
        self.verbose = verbose
    
    def log(self, msg):
        if self.verbose:
            print(f"  {msg}")
    
    def compute_supplier_risk(self, df_features):
        """
        Compute supplier risk based on behavioral features.
        
        Risk Components:
        - Temporal Risk: Aging + Consistency
        - Financial Risk: Volatility + Abnormal amounts
        - Behavioral Risk: Anomaly ratio + Stability
        - Business Risk: Diversity + Repeat patterns
        """
        self.log("Computing advanced supplier risk...")
        
        df_risk = df_features.copy()
        
        # Temporal Risk (30% weight)
        temporal_risk = (
            (df_risk['temporal_avg_aging_days'] / 365).clip(0, 1) * 0.6 +
            (1.0 - df_risk['temporal_temporal_consistency']) * 0.4
        )
        df_risk['risk_temporal'] = temporal_risk.clip(0, 1) * 100
        
        # Financial Risk (25% weight)
        financial_risk = (
            df_risk['financial_amount_volatility_cv'].clip(0, 2) / 2 * 0.5 +
            df_risk['financial_abnormal_amount_ratio'] * 0.5
        )
        df_risk['risk_financial'] = financial_risk.clip(0, 1) * 100
        
        # Behavioral Risk (30% weight)
        behavioral_risk = (
            df_risk['behavioral_anomaly_ratio'] * 0.6 +
            (1.0 - df_risk['behavioral_supplier_stability_score']) * 0.4
        )
        df_risk['risk_behavioral'] = behavioral_risk.clip(0, 1) * 100
        
        # Business Risk (15% weight)
        business_risk = (
            (1.0 - df_risk['business_business_diversity']) * 0.4 +
            df_risk['business_repeat_po_ratio'] * 0.3 +
            df_risk['business_duplicate_transaction_ratio'] * 0.3
        )
        df_risk['risk_business'] = business_risk.clip(0, 1) * 100
        
        # Composite Supplier Risk
        df_risk['supplier_risk_score'] = (
            df_risk['risk_temporal'] * 0.30 +
            df_risk['risk_financial'] * 0.25 +
            df_risk['risk_behavioral'] * 0.30 +
            df_risk['risk_business'] * 0.15
        ).clip(0, 100)
        
        # Assign risk levels (using percentiles)
        p33 = np.percentile(df_risk['supplier_risk_score'], 33)
        p67 = np.percentile(df_risk['supplier_risk_score'], 67)
        p90 = np.percentile(df_risk['supplier_risk_score'], 90)
        
        df_risk['supplier_risk_level'] = 'LOW'
        df_risk.loc[df_risk['supplier_risk_score'] > p33, 'supplier_risk_level'] = 'MEDIUM'
        df_risk.loc[df_risk['supplier_risk_score'] > p67, 'supplier_risk_level'] = 'HIGH'
        df_risk.loc[df_risk['supplier_risk_score'] > p90, 'supplier_risk_level'] = 'CRITICAL'
        
        self.log(f"✓ Supplier risk computed (mean: {df_risk['supplier_risk_score'].mean():.2f})")
        
        return df_risk


# =============================================================================
# TESTING
# =============================================================================

if __name__ == '__main__':
    print("="*80)
    print("PHASE 2 — ADVANCED SUPPLIER INTELLIGENCE")
    print("="*80)
    
    print("\nModules loaded:")
    print("  ✓ SupplierBehavioralFeatures")
    print("  ✓ AdvancedSupplierRiskEngine")
    print("\nReady for Phase 2 implementation")
