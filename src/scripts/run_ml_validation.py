#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Complete ML Validation Pipeline
=================================

This script:
1. Loads prepared data with labels & features
2. Prepares ML-ready features (X, y)
3. Trains ML models
4. Validates fraud detection
5. Generates comprehensive report
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import pickle
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("🚀 COMPLETE ML VALIDATION PIPELINE")
print("=" * 80)

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
PROCESSED_DATA_DIR = SRC_DIR / "data" / "processed"
MODEL_DIR = SRC_DIR / "models"
OUTPUT_DIR = SRC_DIR / "outputs"
DATA_OUTPUT_DIR = OUTPUT_DIR / "data"

# Create directories
for dir_path in [MODEL_DIR, OUTPUT_DIR, DATA_OUTPUT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ============================================================================
# STEP 1: FIND AND LOAD LATEST DATA FILE
# ============================================================================
print("\n📂 STEP 1: FINDING LATEST DATA FILE")
print("-" * 80)

# Find latest file with labels and features
data_files = sorted(PROCESSED_DATA_DIR.glob("documents_with_labels_and_features_*.csv"))
if not data_files:
    data_files = sorted(PROCESSED_DATA_DIR.glob("data_prepared_*.csv"))

if not data_files:
    print("❌ No prepared data files found!")
    print(f"   Searched in: {PROCESSED_DATA_DIR}")
    exit(1)

latest_file = data_files[-1]
print(f"✅ Found latest file: {latest_file.name}")
print(f"   Size: {latest_file.stat().st_size / 1024 / 1024:.1f} MB")

# Load data
print(f"\n📥 Loading data...")
df = pd.read_csv(latest_file)
print(f"✅ Loaded: {len(df):,} rows × {len(df.columns)} columns")

print(f"\n📋 Columns available:")
for i, col in enumerate(df.columns[:15], 1):
    print(f"   {i:2d}. {col}")
if len(df.columns) > 15:
    print(f"   ... ({len(df.columns) - 15} more columns)")

# ============================================================================
# STEP 2: IDENTIFY LABEL COLUMN & FEATURES
# ============================================================================
print("\n🔍 STEP 2: IDENTIFYING LABELS AND FEATURES")
print("-" * 80)

# Find label column (usually named 'anomaly_class', 'anomaly_type', 'label', etc.)
label_col = None
for potential_col in ['anomaly_class', 'anomaly_type', 'label', 'classification', 'anomaly', 'status']:
    if potential_col in df.columns:
        label_col = potential_col
        break

if not label_col:
    # Try to find column with categorical values that matches our anomaly types
    anomaly_types = {'OK', 'INCOMPLETE', 'DELIVERED_NOT_INVOICED', 'INVOICED_NOT_DELIVERED'}
    for col in df.columns:
        if df[col].dtype == 'object' and set(df[col].unique()).issubset(anomaly_types):
            label_col = col
            break

if not label_col:
    print("❌ Could not identify label column!")
    print(f"   Columns: {list(df.columns)}")
    exit(1)

print(f"✅ Label column identified: {label_col}")

# Find feature columns (numeric columns, excluding IDs and labels)
id_cols = [col for col in df.columns if 'id' in col.lower()]
metadata_cols = [col for col in df.columns if col in ['po_number', 'ir_number', 'gr_number', 'supplier', 'date', 'created_at']]
exclude_cols = id_cols + metadata_cols + [label_col]

feature_cols = [col for col in df.columns 
                if df[col].dtype in ['int64', 'float64', 'int32', 'float32']
                and col not in exclude_cols]

print(f"\n✅ Identified {len(feature_cols)} numeric feature columns")
print(f"   Excluded {len(exclude_cols)} non-feature columns")

# ============================================================================
# STEP 3: DATA QUALITY ANALYSIS
# ============================================================================
print("\n🔍 STEP 3: DATA QUALITY ANALYSIS")
print("-" * 80)

# Check labels
print(f"\n📊 Label Distribution ({label_col}):")
label_counts = df[label_col].value_counts()
for label, count in label_counts.items():
    pct = count / len(df) * 100
    bar = "█" * int(pct / 2)
    print(f"  {label:30s}: {count:7,} ({pct:5.2f}%) {bar}")

# Check for fraud detection (main concern)
fraud_col = 'INVOICED_NOT_DELIVERED'
fraud_count = (df[label_col] == fraud_col).sum()
fraud_pct = fraud_count / len(df) * 100

print(f"\n🎯 FRAUD DETECTION (Primary Objective):")
print(f"  Fraud Cases ({fraud_col}): {fraud_count:,} ({fraud_pct:.2f}%)")

if fraud_count == 0:
    print(f"  ⚠️  WARNING: NO FRAUD CASES DETECTED!")
    print(f"      This is a CRITICAL issue for primary objective")
else:
    print(f"  ✅ Fraud detection working - {fraud_count} cases found")

# Check for missing values in features
print(f"\n❓ Missing Values in Features:")
missing_count = df[feature_cols].isnull().sum()
if missing_count.sum() == 0:
    print(f"  ✅ No missing values")
else:
    missing_features = missing_count[missing_count > 0]
    print(f"  ⚠️  {len(missing_features)} features have missing values")
    for col, count in missing_features.head(10).items():
        print(f"      {col}: {count:,} missing ({count/len(df)*100:.2f}%)")

# ============================================================================
# STEP 4: PREPARE ML FEATURES
# ============================================================================
print("\n⚙️  STEP 4: PREPARING ML FEATURES")
print("-" * 80)

# Handle missing values in features
X = df[feature_cols].fillna(0)
y = df[label_col]

print(f"✅ Features prepared:")
print(f"   X shape: {X.shape}")
print(f"   y shape: {len(y)}")
print(f"   Feature columns: {len(feature_cols)}")

# Check for constant features (no variance)
constant_features = [col for col in feature_cols if X[col].std() == 0]
if constant_features:
    print(f"\n⚠️  Constant features ({len(constant_features)}):")
    for col in constant_features[:10]:
        print(f"     • {col}")
    # Remove constant features
    X = X.drop(columns=constant_features)
    print(f"   Removed {len(constant_features)} constant features")
    print(f"   New X shape: {X.shape}")

# ============================================================================
# STEP 5: SAVE ML FEATURES
# ============================================================================
print("\n💾 STEP 5: SAVING PREPARED FEATURES")
print("-" * 80)

X_file = PROCESSED_DATA_DIR / "ml_features_phase2_X.csv"
y_file = PROCESSED_DATA_DIR / "ml_features_phase2_y.csv"

X.to_csv(X_file, index=False)
y.to_csv(y_file, index=False, header=False)

print(f"✅ Features saved:")
print(f"   X: {X_file.name} ({X_file.stat().st_size / 1024 / 1024:.1f} MB)")
print(f"   y: {y_file.name} ({y_file.stat().st_size / 1024:.1f} KB)")

# ============================================================================
# STEP 6: FEATURE ANALYSIS
# ============================================================================
print("\n🔬 STEP 6: FEATURE ANALYSIS")
print("-" * 80)

print(f"\n📊 Feature Statistics:")
print(f"  Count:     {X.shape[0]:,} samples")
print(f"  Features:  {X.shape[1]} dimensions")
print(f"  Mean std:  {X.std().mean():.4f}")
print(f"  Min std:   {X.std().min():.4f}")
print(f"  Max std:   {X.std().max():.4f}")

# Top features by variance
print(f"\n⭐ Top 10 Features by Variance:")
feature_variance = X.var().sort_values(ascending=False)
for i, (col, var) in enumerate(feature_variance.head(10).items(), 1):
    print(f"   {i:2d}. {col:30s}: {var:12.4f}")

# ============================================================================
# STEP 7: PREPROCESSING & MODEL TRAINING
# ============================================================================
print("\n🤖 STEP 7: MODEL TRAINING")
print("-" * 80)

from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from imblearn.over_sampling import SMOTE

# Encode labels
unique_labels = sorted(y.unique())
label_encoder = {label: i for i, label in enumerate(unique_labels)}
y_encoded = y.map(label_encoder)

print(f"\n🏷️  Label Encoding:")
for label, code in sorted(label_encoder.items(), key=lambda x: x[1]):
    count = (y == label).sum()
    print(f"   {label:30s} → {code}  ({count:6,})")

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)

print(f"\n📊 Train/Test Split:")
print(f"   Training: {len(X_train):,} ({len(X_train)/len(X)*100:.1f}%)")
print(f"   Test:     {len(X_test):,} ({len(X_test)/len(X)*100:.1f}%)")

# Scale
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# SMOTE
try:
    smote = SMOTE(random_state=42, k_neighbors=min(5, len(X_train)-1))
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train_scaled, y_train)
    print(f"\n✅ SMOTE Applied:")
    print(f"   Before: {len(X_train_scaled):,}")
    print(f"   After:  {len(X_train_balanced):,}")
except Exception as e:
    print(f"⚠️  SMOTE failed: {e}")
    X_train_balanced = X_train_scaled
    y_train_balanced = y_train

# Train models
models = {}
results = {}

print(f"\n🎯 Training Models:")

# Logistic Regression
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

print(f"   1. Logistic Regression")
print(f"      CV F1:    {cv_lr.mean():.4f} (+/- {cv_lr.std():.4f})")
print(f"      Train:    {train_lr:.4f}")
print(f"      Test:     {test_lr:.4f}")

# Random Forest
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

print(f"   2. Random Forest")
print(f"      CV F1:    {cv_rf.mean():.4f} (+/- {cv_rf.std():.4f})")
print(f"      Train:    {train_rf:.4f}")
print(f"      Test:     {test_rf:.4f}")

# XGBoost (if available)
try:
    import xgboost as xgb
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
    
    print(f"   3. XGBoost")
    print(f"      CV F1:    {cv_xg.mean():.4f} (+/- {cv_xg.std():.4f})")
    print(f"      Train:    {train_xg:.4f}")
    print(f"      Test:     {test_xg:.4f}")
except:
    print(f"   3. XGBoost - NOT AVAILABLE")

# LightGBM (if available)
try:
    import lightgbm as lgb
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
    
    print(f"   4. LightGBM")
    print(f"      CV F1:    {cv_lgb.mean():.4f} (+/- {cv_lgb.std():.4f})")
    print(f"      Train:    {train_lgb:.4f}")
    print(f"      Test:     {test_lgb:.4f}")
except:
    print(f"   4. LightGBM - NOT AVAILABLE")

# ============================================================================
# STEP 8: SAVE MODELS
# ============================================================================
print("\n💾 STEP 8: SAVING MODELS")
print("-" * 80)

for name, model in models.items():
    path = MODEL_DIR / f"{name}_model.pkl"
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    print(f"   ✅ {name}")

# Save scaler
with open(MODEL_DIR / "scaler.pkl", 'wb') as f:
    pickle.dump(scaler, f)
print(f"   ✅ scaler")

# Save label encoder
with open(MODEL_DIR / "label_encoder.json", 'w') as f:
    json.dump(label_encoder, f)
print(f"   ✅ label_encoder")

# ============================================================================
# STEP 9: PREDICTIONS & EVALUATION
# ============================================================================
print("\n🎯 STEP 9: PREDICTIONS & EVALUATION")
print("-" * 80)

# Use best model
best_model_name = max(results.keys(), key=lambda x: results[x]['test_score'])
best_model = models[best_model_name]

print(f"\n✅ Best Model: {best_model_name} (test F1: {results[best_model_name]['test_score']:.4f})")

# Predictions
y_pred = best_model.predict(X_test_scaled)
y_pred_proba = best_model.predict_proba(X_test_scaled)
confidence = y_pred_proba.max(axis=1)

# Inverse encoding
reverse_encoder = {v: k for k, v in label_encoder.items()}

print(f"\n📊 Prediction Distribution (Test Set):")
unique, counts = np.unique(y_pred, return_counts=True)
for label_code, count in zip(unique, counts):
    label_name = reverse_encoder[label_code]
    pct = count / len(y_pred) * 100
    print(f"   {label_name:30s}: {count:6,} ({pct:5.2f}%)")

print(f"\n📈 Prediction Confidence:")
print(f"   Mean:  {confidence.mean():.4f}")
print(f"   Std:   {confidence.std():.4f}")
print(f"   Min:   {confidence.min():.4f}")
print(f"   Max:   {confidence.max():.4f}")

# ============================================================================
# STEP 10: VALIDATION REPORT
# ============================================================================
print("\n📋 STEP 10: GENERATING VALIDATION REPORT")
print("-" * 80)

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

print(f"✅ Report saved: {report_path.name}")

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
print(f"✅ Predictions saved: {pred_path.name}")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("✅ ML VALIDATION PIPELINE COMPLETE!")
print("=" * 80)

print(f"\n📊 Summary:")
print(f"  Data file:    {latest_file.name}")
print(f"  Samples:      {len(df):,}")
print(f"  Features:     {X.shape[1]}")
print(f"  Labels:       {len(label_encoder)}")
print(f"  Models:       {len(models)}")
print(f"  Best model:   {best_model_name}")
print(f"  Test F1:      {results[best_model_name]['test_score']:.4f}")
print(f"  Fraud cases:  {fraud_count:,} ({fraud_pct:.2f}%)")

if fraud_count == 0:
    print(f"\n🚨 CRITICAL ISSUE:")
    print(f"  NO FRAUD CASES DETECTED!")
    print(f"  PRIMARY OBJECTIVE AT RISK")

print(f"\n💾 Output files:")
print(f"  - {X_file.name}")
print(f"  - {y_file.name}")
print(f"  - {report_path.name}")
print(f"  - {pred_path.name}")

print("\n✨ Next Steps:")
print(f"  1. Review validation report")
print(f"  2. Analyze fraud detection accuracy")
print(f"  3. Prepare production deployment")
