#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Complete ML Validation Pipeline
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import pickle
import json
from datetime import datetime
import warnings
import sys

warnings.filterwarnings('ignore')

# Simple print without emojis
print("="*80)
print("COMPLETE ML VALIDATION PIPELINE")
print("="*80)

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
PROCESSED_DATA_DIR = SRC_DIR / "data" / "processed"
MODEL_DIR = SRC_DIR / "models"
OUTPUT_DIR = SRC_DIR / "outputs"
DATA_OUTPUT_DIR = OUTPUT_DIR / "data"

for dir_path in [MODEL_DIR, OUTPUT_DIR, DATA_OUTPUT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# STEP 1: FIND LATEST DATA FILE
print("\nSTEP 1: FINDING LATEST DATA FILE")
print("-"*80)

data_files = sorted(PROCESSED_DATA_DIR.glob("documents_with_labels_and_features_*.csv"))
if not data_files:
    data_files = sorted(PROCESSED_DATA_DIR.glob("data_prepared_*.csv"))

if not data_files:
    print("ERROR: No prepared data files found!")
    print(f"Searched in: {PROCESSED_DATA_DIR}")
    sys.exit(1)

latest_file = data_files[-1]
print(f"[OK] Found latest file: {latest_file.name}")
print(f"Size: {latest_file.stat().st_size / 1024 / 1024:.1f} MB")

# Load data
print(f"\nLoading data...")
df = pd.read_csv(latest_file)
print(f"[OK] Loaded: {len(df):,} rows x {len(df.columns)} columns")

# STEP 2: IDENTIFY LABEL COLUMN & FEATURES
print("\nSTEP 2: IDENTIFYING LABELS AND FEATURES")
print("-"*80)

label_col = None
for potential_col in ['anomaly_class', 'anomaly_type', 'label', 'classification', 'anomaly', 'status']:
    if potential_col in df.columns:
        label_col = potential_col
        break

if not label_col:
    anomaly_types = {'OK', 'INCOMPLETE', 'DELIVERED_NOT_INVOICED', 'INVOICED_NOT_DELIVERED'}
    for col in df.columns:
        if df[col].dtype == 'object' and set(df[col].unique()).issubset(anomaly_types):
            label_col = col
            break

if not label_col:
    print("ERROR: Could not identify label column!")
    sys.exit(1)

print(f"[OK] Label column identified: {label_col}")

# Find feature columns
id_cols = [col for col in df.columns if 'id' in col.lower()]
metadata_cols = [col for col in df.columns if col in ['po_number', 'ir_number', 'gr_number', 'supplier', 'date', 'created_at']]
exclude_cols = id_cols + metadata_cols + [label_col]

feature_cols = [col for col in df.columns 
                if df[col].dtype in ['int64', 'float64', 'int32', 'float32']
                and col not in exclude_cols]

print(f"[OK] Identified {len(feature_cols)} numeric features")

# STEP 3: DATA QUALITY ANALYSIS
print("\nSTEP 3: DATA QUALITY ANALYSIS")
print("-"*80)

print(f"\nLabel Distribution ({label_col}):")
label_counts = df[label_col].value_counts()
for label, count in label_counts.items():
    pct = count / len(df) * 100
    print(f"  {label:30s}: {count:7,} ({pct:5.2f}%)")

# Check fraud detection (CRITICAL)
fraud_col = 'INVOICED_NOT_DELIVERED'
fraud_count = (df[label_col] == fraud_col).sum()
fraud_pct = fraud_count / len(df) * 100

print(f"\nFRAUD DETECTION (Primary Objective):")
print(f"  Fraud Cases ({fraud_col}): {fraud_count:,} ({fraud_pct:.2f}%)")

if fraud_count == 0:
    print(f"  [WARNING] NO FRAUD CASES DETECTED!")
    print(f"  This is CRITICAL - Primary objective at risk!")
else:
    print(f"  [OK] Fraud detection working - {fraud_count} cases found")

# Check missing values
print(f"\nMissing Values in Features:")
missing_count = df[feature_cols].isnull().sum()
if missing_count.sum() == 0:
    print(f"  [OK] No missing values")
else:
    missing_features = missing_count[missing_count > 0]
    print(f"  [WARNING] {len(missing_features)} features have missing values")
    for col, count in missing_features.head(5).items():
        print(f"      {col}: {count:,} missing ({count/len(df)*100:.2f}%)")

# STEP 4: PREPARE ML FEATURES
print("\nSTEP 4: PREPARING ML FEATURES")
print("-"*80)

X = df[feature_cols].fillna(0)
y = df[label_col]

print(f"[OK] Features prepared:")
print(f"  X shape: {X.shape}")
print(f"  y shape: {len(y)}")

# Remove constant features
constant_features = [col for col in feature_cols if X[col].std() == 0]
if constant_features:
    print(f"\n[WARNING] Found {len(constant_features)} constant features, removing...")
    X = X.drop(columns=constant_features)
    print(f"  New X shape: {X.shape}")

# STEP 5: SAVE ML FEATURES
print("\nSTEP 5: SAVING PREPARED FEATURES")
print("-"*80)

X_file = PROCESSED_DATA_DIR / "ml_features_phase2_X.csv"
y_file = PROCESSED_DATA_DIR / "ml_features_phase2_y.csv"

X.to_csv(X_file, index=False)
y.to_csv(y_file, index=False, header=False)

print(f"[OK] Features saved:")
print(f"  X: {X_file.name} ({X_file.stat().st_size / 1024 / 1024:.1f} MB)")
print(f"  y: {y_file.name} ({y_file.stat().st_size / 1024:.1f} KB)")

# STEP 6: FEATURE ANALYSIS
print("\nSTEP 6: FEATURE ANALYSIS")
print("-"*80)

print(f"\nFeature Statistics:")
print(f"  Samples: {X.shape[0]:,}")
print(f"  Features: {X.shape[1]}")
print(f"  Mean std: {X.std().mean():.4f}")
print(f"  Min std: {X.std().min():.4f}")
print(f"  Max std: {X.std().max():.4f}")

print(f"\nTop 10 Features by Variance:")
feature_variance = X.var().sort_values(ascending=False)
for i, (col, var) in enumerate(feature_variance.head(10).items(), 1):
    print(f"  {i:2d}. {col:30s}: {var:12.4f}")

# STEP 7: MODEL TRAINING
print("\nSTEP 7: MODEL TRAINING")
print("-"*80)

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from imblearn.over_sampling import SMOTE

# Encode labels
unique_labels = sorted(y.unique())
label_encoder = {label: i for i, label in enumerate(unique_labels)}
y_encoded = y.map(label_encoder)

print(f"\nLabel Encoding:")
for label, code in sorted(label_encoder.items(), key=lambda x: x[1]):
    count = (y == label).sum()
    print(f"  {label:30s} -> {code}  ({count:6,})")

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)

print(f"\nTrain/Test Split:")
print(f"  Training: {len(X_train):,} ({len(X_train)/len(X)*100:.1f}%)")
print(f"  Test: {len(X_test):,} ({len(X_test)/len(X)*100:.1f}%)")

# Scale
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# SMOTE
try:
    smote = SMOTE(random_state=42, k_neighbors=min(5, len(X_train)-1))
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train_scaled, y_train)
    print(f"\n[OK] SMOTE Applied:")
    print(f"  Before: {len(X_train_scaled):,}")
    print(f"  After: {len(X_train_balanced):,}")
except Exception as e:
    print(f"[WARNING] SMOTE failed: {e}")
    X_train_balanced = X_train_scaled
    y_train_balanced = y_train

# Train models
models = {}
results = {}

print(f"\nTraining Models:")

# Logistic Regression
print(f"  1. Logistic Regression")
lr = LogisticRegression(max_iter=1000, random_state=42, n_jobs=-1)
lr.fit(X_train_balanced, y_train_balanced)
models['logistic_regression'] = lr

cv_lr = cross_val_score(lr, X_train_balanced, y_train_balanced, cv=5, scoring='f1_macro')
train_lr = lr.score(X_train_balanced, y_train_balanced)
test_lr = lr.score(X_test_scaled, y_test)

results['logistic_regression'] = {
    'cv_mean': float(cv_lr.mean()),
    'cv_std': float(cv_lr.std()),
    'train_score': float(train_lr),
    'test_score': float(test_lr),
}

print(f"     CV F1: {cv_lr.mean():.4f} (+/- {cv_lr.std():.4f})")
print(f"     Train: {train_lr:.4f}")
print(f"     Test: {test_lr:.4f}")

# Random Forest
print(f"  2. Random Forest")
rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1, max_depth=15)
rf.fit(X_train_balanced, y_train_balanced)
models['random_forest'] = rf

cv_rf = cross_val_score(rf, X_train_balanced, y_train_balanced, cv=5, scoring='f1_macro')
train_rf = rf.score(X_train_balanced, y_train_balanced)
test_rf = rf.score(X_test_scaled, y_test)

results['random_forest'] = {
    'cv_mean': float(cv_rf.mean()),
    'cv_std': float(cv_rf.std()),
    'train_score': float(train_rf),
    'test_score': float(test_rf),
}

print(f"     CV F1: {cv_rf.mean():.4f} (+/- {cv_rf.std():.4f})")
print(f"     Train: {train_rf:.4f}")
print(f"     Test: {test_rf:.4f}")

# XGBoost
try:
    import xgboost as xgb
    print(f"  3. XGBoost")
    xg = xgb.XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, n_jobs=-1, eval_metric='logloss')
    xg.fit(X_train_balanced, y_train_balanced)
    models['xgboost'] = xg
    
    cv_xg = cross_val_score(xg, X_train_balanced, y_train_balanced, cv=5, scoring='f1_macro')
    train_xg = xg.score(X_train_balanced, y_train_balanced)
    test_xg = xg.score(X_test_scaled, y_test)
    
    results['xgboost'] = {
        'cv_mean': float(cv_xg.mean()),
        'cv_std': float(cv_xg.std()),
        'train_score': float(train_xg),
        'test_score': float(test_xg),
    }
    
    print(f"     CV F1: {cv_xg.mean():.4f} (+/- {cv_xg.std():.4f})")
    print(f"     Train: {train_xg:.4f}")
    print(f"     Test: {test_xg:.4f}")
except Exception as e:
    print(f"  3. XGBoost - NOT AVAILABLE ({str(e)[:50]})")

# LightGBM
try:
    import lightgbm as lgb
    print(f"  4. LightGBM")
    lgb_model = lgb.LGBMClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, n_jobs=-1)
    lgb_model.fit(X_train_balanced, y_train_balanced)
    models['lightgbm'] = lgb_model
    
    cv_lgb = cross_val_score(lgb_model, X_train_balanced, y_train_balanced, cv=5, scoring='f1_macro')
    train_lgb = lgb_model.score(X_train_balanced, y_train_balanced)
    test_lgb = lgb_model.score(X_test_scaled, y_test)
    
    results['lightgbm'] = {
        'cv_mean': float(cv_lgb.mean()),
        'cv_std': float(cv_lgb.std()),
        'train_score': float(train_lgb),
        'test_score': float(test_lgb),
    }
    
    print(f"     CV F1: {cv_lgb.mean():.4f} (+/- {cv_lgb.std():.4f})")
    print(f"     Train: {train_lgb:.4f}")
    print(f"     Test: {test_lgb:.4f}")
except Exception as e:
    print(f"  4. LightGBM - NOT AVAILABLE ({str(e)[:50]})")

# STEP 8: SAVE MODELS
print("\nSTEP 8: SAVING MODELS")
print("-"*80)

for name, model in models.items():
    path = MODEL_DIR / f"{name}_model.pkl"
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    print(f"  [OK] {name}")

with open(MODEL_DIR / "scaler.pkl", 'wb') as f:
    pickle.dump(scaler, f)
print(f"  [OK] scaler")

with open(MODEL_DIR / "label_encoder.json", 'w') as f:
    json.dump(label_encoder, f)
print(f"  [OK] label_encoder")

# STEP 9: PREDICTIONS
print("\nSTEP 9: PREDICTIONS & EVALUATION")
print("-"*80)

best_model_name = max(results.keys(), key=lambda x: results[x]['test_score'])
best_model = models[best_model_name]

print(f"\n[OK] Best Model: {best_model_name} (test F1: {results[best_model_name]['test_score']:.4f})")

y_pred = best_model.predict(X_test_scaled)
y_pred_proba = best_model.predict_proba(X_test_scaled)
confidence = y_pred_proba.max(axis=1)

reverse_encoder = {v: k for k, v in label_encoder.items()}

print(f"\nPrediction Distribution (Test Set):")
unique, counts = np.unique(y_pred, return_counts=True)
for label_code, count in zip(unique, counts):
    label_name = reverse_encoder[label_code]
    pct = count / len(y_pred) * 100
    print(f"  {label_name:30s}: {count:6,} ({pct:5.2f}%)")

print(f"\nPrediction Confidence:")
print(f"  Mean: {confidence.mean():.4f}")
print(f"  Std: {confidence.std():.4f}")
print(f"  Min: {confidence.min():.4f}")
print(f"  Max: {confidence.max():.4f}")

# STEP 10: VALIDATION REPORT
print("\nSTEP 10: GENERATING VALIDATION REPORT")
print("-"*80)

validation_report = {
    'timestamp': datetime.now().isoformat(),
    'data_file': latest_file.name,
    'total_samples': len(df),
    'train_samples': len(X_train),
    'test_samples': len(X_test),
    'features': X.shape[1],
    'label_column': label_col,
    'labels': label_encoder,
    'fraud_detection': {
        'fraud_column': fraud_col,
        'fraud_count': int(fraud_count),
        'fraud_pct': float(fraud_pct),
        'status': 'OK' if fraud_count > 0 else 'CRITICAL - NO FRAUD DETECTED'
    },
    'models_trained': list(models.keys()),
    'model_results': results,
    'best_model': best_model_name,
    'best_test_score': float(results[best_model_name]['test_score']),
}

report_path = DATA_OUTPUT_DIR / "ml_validation_report.json"
with open(report_path, 'w') as f:
    json.dump(validation_report, f, indent=2)

print(f"[OK] Report saved: {report_path.name}")

# Save predictions
predictions_df = pd.DataFrame({
    'actual': y_test.values,
    'predicted': y_pred,
    'confidence': confidence,
    'actual_label': [reverse_encoder[y] for y in y_test.values],
    'predicted_label': [reverse_encoder[p] for p in y_pred],
})

pred_path = DATA_OUTPUT_DIR / "ml_predictions.csv"
predictions_df.to_csv(pred_path, index=False)
print(f"[OK] Predictions saved: {pred_path.name}")

# FINAL SUMMARY
print("\n" + "="*80)
print("PIPELINE COMPLETE!")
print("="*80)

print(f"\nSummary:")
print(f"  Data file: {latest_file.name}")
print(f"  Samples: {len(df):,}")
print(f"  Features: {X.shape[1]}")
print(f"  Labels: {len(label_encoder)}")
print(f"  Models: {len(models)}")
print(f"  Best model: {best_model_name}")
print(f"  Test F1: {results[best_model_name]['test_score']:.4f}")
print(f"  Fraud cases: {fraud_count:,} ({fraud_pct:.2f}%)")

if fraud_count == 0:
    print(f"\n[CRITICAL ISSUE]")
    print(f"  NO FRAUD CASES DETECTED!")
    print(f"  PRIMARY OBJECTIVE AT RISK")

print(f"\nOutput files:")
print(f"  - {X_file.name}")
print(f"  - {y_file.name}")
print(f"  - {report_path.name}")
print(f"  - {pred_path.name}")

print("\nDone.")
