#!/usr/bin/env python
"""
ML Pipeline Execution & Validation Script
==========================================

This script executes the complete ML pipeline:
1. Load data
2. Preprocess features
3. Train models
4. Evaluate performance
5. Validate anomalies
6. Generate validation report
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import pickle
import json
from datetime import datetime
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    ML_FEATURES_X_FILE, ML_FEATURES_Y_FILE, MODEL_DIR, 
    PROCESSED_DATA_DIR, DATA_OUTPUT_DIR
)
from logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Visualization setup
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 6)

print("=" * 80)
print("🚀 ML PIPELINE EXECUTION & VALIDATION")
print("=" * 80)

# ============================================================================
# STEP 1: LOAD DATA
# ============================================================================
print("\n📊 STEP 1: LOADING DATA")
print("-" * 80)

try:
    X = pd.read_csv(ML_FEATURES_X_FILE)
    y = pd.read_csv(ML_FEATURES_Y_FILE, header=None, squeeze=True)
    
    print(f"✅ Features loaded: {X.shape}")
    print(f"✅ Labels loaded: {len(y):,}")
    print(f"\nFeature columns ({len(X.columns)}):")
    for i, col in enumerate(X.columns[:10], 1):
        print(f"  {i}. {col}")
    if len(X.columns) > 10:
        print(f"  ... ({len(X.columns) - 10} more features)")
    
except Exception as e:
    logger.error(f"❌ Failed to load data: {e}")
    print(f"❌ Failed to load data: {e}")
    sys.exit(1)

# ============================================================================
# STEP 2: DATA QUALITY CHECKS
# ============================================================================
print("\n🔍 STEP 2: DATA QUALITY CHECKS")
print("-" * 80)

# Check for missing values
missing_x = X.isnull().sum().sum()
missing_y = y.isnull().sum()
print(f"Missing values in X: {missing_x}")
print(f"Missing values in y: {missing_y}")

# Check label distribution
print(f"\n📋 Label Distribution:")
label_counts = y.value_counts()
for label, count in label_counts.items():
    pct = count / len(y) * 100
    print(f"  {label:30s}: {count:6,} ({pct:5.2f}%)")

# Check for class imbalance
min_class = label_counts.min()
max_class = label_counts.max()
imbalance_ratio = max_class / min_class
print(f"\n⚠️  Class Imbalance Ratio: {imbalance_ratio:.1f}:1")

# ============================================================================
# STEP 3: FEATURE ANALYSIS
# ============================================================================
print("\n🔬 STEP 3: FEATURE ANALYSIS")
print("-" * 80)

print(f"\n📊 Feature Statistics:")
print(X.describe().to_string())

print(f"\n⚠️  Feature Quality Checks:")
# Check for constant features
constant_features = [col for col in X.columns if X[col].std() == 0]
if constant_features:
    print(f"  ⚠️  Constant features ({len(constant_features)}): {constant_features[:5]}")
else:
    print(f"  ✅ No constant features found")

# Check for highly correlated features
print(f"\n  Checking feature correlations...")
corr_matrix = X.corr().abs()
# Get upper triangle
upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
high_corr_pairs = [(column, row, upper.loc[row, column]) 
                    for column in upper.columns 
                    for row in upper.index 
                    if upper.loc[row, column] > 0.95]
if high_corr_pairs:
    print(f"  ⚠️  Highly correlated features (r > 0.95): {len(high_corr_pairs)} pairs")
    for col1, col2, corr in high_corr_pairs[:5]:
        print(f"      • {col1} ↔ {col2}: {corr:.3f}")
else:
    print(f"  ✅ No highly correlated features found")

# ============================================================================
# STEP 4: TRAIN/TEST SPLIT & PREPROCESSING
# ============================================================================
print("\n🔄 STEP 4: TRAIN/TEST SPLIT & PREPROCESSING")
print("-" * 80)

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE

# Encode labels
unique_labels = y.unique()
label_encoder = {label: i for i, label in enumerate(sorted(unique_labels))}
y_encoded = y.map(label_encoder)

print(f"\n🏷️  Label Encoding:")
for label, code in sorted(label_encoder.items(), key=lambda x: x[1]):
    count = (y == label).sum()
    print(f"  {label:30s} → {code}  ({count:,})")

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)
print(f"\n📊 Train/Test Split:")
print(f"  Training: {len(X_train):,} ({len(X_train)/len(X)*100:.1f}%)")
print(f"  Test:     {len(X_test):,} ({len(X_test)/len(X)*100:.1f}%)")

# Scale
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
print(f"\n✅ Features scaled (StandardScaler)")

# Apply SMOTE
try:
    smote = SMOTE(random_state=42, k_neighbors=5)
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train_scaled, y_train)
    print(f"\n✅ SMOTE Applied:")
    print(f"  Before: {len(X_train_scaled):,} samples")
    print(f"  After:  {len(X_train_balanced):,} samples")
    
    # Show balanced distribution
    print(f"\n  Balanced distribution:")
    for label, code in sorted(label_encoder.items(), key=lambda x: x[1]):
        count = (y_train_balanced == code).sum()
        print(f"    {label:30s}: {count:6,}")
except Exception as e:
    logger.warning(f"SMOTE failed: {e}. Using original data.")
    X_train_balanced = X_train_scaled
    y_train_balanced = y_train

# ============================================================================
# STEP 5: MODEL TRAINING
# ============================================================================
print("\n🤖 STEP 5: MODEL TRAINING")
print("-" * 80)

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except:
    XGBOOST_AVAILABLE = False

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except:
    LIGHTGBM_AVAILABLE = False

models = {}
results = {}

# Create model directory
Path(MODEL_DIR).mkdir(parents=True, exist_ok=True)

# 1. Logistic Regression
print("\n1️⃣  Logistic Regression")
lr = LogisticRegression(max_iter=1000, random_state=42, n_jobs=-1)
lr.fit(X_train_balanced, y_train_balanced)
models['logistic_regression'] = lr

cv_scores_lr = cross_val_score(lr, X_train_balanced, y_train_balanced, cv=5, scoring='f1_macro')
train_score_lr = lr.score(X_train_balanced, y_train_balanced)
test_score_lr = lr.score(X_test_scaled, y_test)

results['logistic_regression'] = {
    'cv_mean': float(cv_scores_lr.mean()),
    'cv_std': float(cv_scores_lr.std()),
    'train_score': float(train_score_lr),
    'test_score': float(test_score_lr),
}

print(f"  CV F1 Score:    {cv_scores_lr.mean():.4f} (+/- {cv_scores_lr.std():.4f})")
print(f"  Train Score:    {train_score_lr:.4f}")
print(f"  Test Score:     {test_score_lr:.4f}")

# 2. Random Forest
print("\n2️⃣  Random Forest")
rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1, max_depth=15)
rf.fit(X_train_balanced, y_train_balanced)
models['random_forest'] = rf

cv_scores_rf = cross_val_score(rf, X_train_balanced, y_train_balanced, cv=5, scoring='f1_macro')
train_score_rf = rf.score(X_train_balanced, y_train_balanced)
test_score_rf = rf.score(X_test_scaled, y_test)

results['random_forest'] = {
    'cv_mean': float(cv_scores_rf.mean()),
    'cv_std': float(cv_scores_rf.std()),
    'train_score': float(train_score_rf),
    'test_score': float(test_score_rf),
}

print(f"  CV F1 Score:    {cv_scores_rf.mean():.4f} (+/- {cv_scores_rf.std():.4f})")
print(f"  Train Score:    {train_score_rf:.4f}")
print(f"  Test Score:     {test_score_rf:.4f}")

# 3. XGBoost
if XGBOOST_AVAILABLE:
    print("\n3️⃣  XGBoost")
    xg = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        n_jobs=-1,
        eval_metric='logloss'
    )
    xg.fit(X_train_balanced, y_train_balanced)
    models['xgboost'] = xg
    
    cv_scores_xg = cross_val_score(xg, X_train_balanced, y_train_balanced, cv=5, scoring='f1_macro')
    train_score_xg = xg.score(X_train_balanced, y_train_balanced)
    test_score_xg = xg.score(X_test_scaled, y_test)
    
    results['xgboost'] = {
        'cv_mean': float(cv_scores_xg.mean()),
        'cv_std': float(cv_scores_xg.std()),
        'train_score': float(train_score_xg),
        'test_score': float(test_score_xg),
    }
    
    print(f"  CV F1 Score:    {cv_scores_xg.mean():.4f} (+/- {cv_scores_xg.std():.4f})")
    print(f"  Train Score:    {train_score_xg:.4f}")
    print(f"  Test Score:     {test_score_xg:.4f}")
else:
    print("\n3️⃣  XGBoost - ⚠️  NOT AVAILABLE")

# 4. LightGBM
if LIGHTGBM_AVAILABLE:
    print("\n4️⃣  LightGBM")
    lgb_model = lgb.LGBMClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        n_jobs=-1
    )
    lgb_model.fit(X_train_balanced, y_train_balanced)
    models['lightgbm'] = lgb_model
    
    cv_scores_lgb = cross_val_score(lgb_model, X_train_balanced, y_train_balanced, cv=5, scoring='f1_macro')
    train_score_lgb = lgb_model.score(X_train_balanced, y_train_balanced)
    test_score_lgb = lgb_model.score(X_test_scaled, y_test)
    
    results['lightgbm'] = {
        'cv_mean': float(cv_scores_lgb.mean()),
        'cv_std': float(cv_scores_lgb.std()),
        'train_score': float(train_score_lgb),
        'test_score': float(test_score_lgb),
    }
    
    print(f"  CV F1 Score:    {cv_scores_lgb.mean():.4f} (+/- {cv_scores_lgb.std():.4f})")
    print(f"  Train Score:    {train_score_lgb:.4f}")
    print(f"  Test Score:     {test_score_lgb:.4f}")
else:
    print("\n4️⃣  LightGBM - ⚠️  NOT AVAILABLE")

# ============================================================================
# STEP 6: FEATURE IMPORTANCE
# ============================================================================
print("\n⭐ STEP 6: FEATURE IMPORTANCE")
print("-" * 80)

if hasattr(models.get('random_forest'), 'feature_importances_'):
    importances = models['random_forest'].feature_importances_
    feature_importance_df = pd.DataFrame({
        'feature': X.columns,
        'importance': importances
    }).sort_values('importance', ascending=False)
    
    print("\n🔝 Top 15 Important Features (Random Forest):")
    for idx, row in feature_importance_df.head(15).iterrows():
        print(f"  {row['feature']:30s}: {row['importance']:.4f}")

# ============================================================================
# STEP 7: SAVE MODELS
# ============================================================================
print("\n💾 STEP 7: SAVING MODELS")
print("-" * 80)

for name, model in models.items():
    model_path = Path(MODEL_DIR) / f"{name}_model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"  ✅ {name}: {model_path}")

# Save scaler
scaler_path = Path(MODEL_DIR) / "scaler.pkl"
with open(scaler_path, 'wb') as f:
    pickle.dump(scaler, f)
print(f"  ✅ scaler: {scaler_path}")

# Save label encoder
encoder_path = Path(MODEL_DIR) / "label_encoder.json"
with open(encoder_path, 'w') as f:
    json.dump(label_encoder, f)
print(f"  ✅ label_encoder: {encoder_path}")

# ============================================================================
# STEP 8: CREATE MODEL REGISTRY
# ============================================================================
print("\n📋 STEP 8: MODEL REGISTRY")
print("-" * 80)

registry = {
    'timestamp': datetime.now().isoformat(),
    'data_shape': {'X': X_train_balanced.shape, 'y': len(y_train_balanced)},
    'test_size': 0.2,
    'smote_applied': True,
    'models': results,
    'label_encoder': label_encoder,
    'feature_names': list(X.columns),
}

registry_path = Path(MODEL_DIR) / "model_registry.json"
with open(registry_path, 'w') as f:
    json.dump(registry, f, indent=2)

print(f"✅ Model Registry saved: {registry_path}")

# ============================================================================
# STEP 9: PREDICTIONS & ANOMALY DETECTION
# ============================================================================
print("\n🎯 STEP 9: PREDICTIONS & ANOMALY ANALYSIS")
print("-" * 80)

# Use Random Forest for predictions (best performer usually)
best_model = models.get('random_forest', models[list(models.keys())[0]])

# Predict on test set
y_pred = best_model.predict(X_test_scaled)
y_pred_proba = best_model.predict_proba(X_test_scaled)

# Get confidence scores
confidence = y_pred_proba.max(axis=1)

# Inverse label encoding for display
reverse_encoder = {v: k for k, v in label_encoder.items()}

print(f"\n📊 Prediction Distribution (Test Set):")
unique, counts = np.unique(y_pred, return_counts=True)
for label_code, count in zip(unique, counts):
    label_name = reverse_encoder.get(label_code, "UNKNOWN")
    pct = count / len(y_pred) * 100
    print(f"  {label_name:30s}: {count:6,} ({pct:5.2f}%)")

print(f"\n📈 Prediction Confidence Statistics:")
print(f"  Mean:   {confidence.mean():.4f}")
print(f"  Std:    {confidence.std():.4f}")
print(f"  Min:    {confidence.min():.4f}")
print(f"  Max:    {confidence.max():.4f}")

# ============================================================================
# STEP 10: SAVE RESULTS
# ============================================================================
print("\n📁 STEP 10: SAVING RESULTS")
print("-" * 80)

# Create predictions dataframe
predictions_df = pd.DataFrame({
    'actual': y_test.values,
    'predicted': y_pred,
    'confidence': confidence,
})

predictions_df['actual_label'] = predictions_df['actual'].map(reverse_encoder)
predictions_df['predicted_label'] = predictions_df['predicted'].map(reverse_encoder)

output_path = Path(DATA_OUTPUT_DIR) / "ml_predictions.csv"
predictions_df.to_csv(output_path, index=False)
print(f"✅ Predictions saved: {output_path}")

# Save summary
summary = {
    'total_samples': len(X),
    'train_samples': len(X_train),
    'test_samples': len(X_test),
    'features': len(X.columns),
    'labels': list(label_encoder.keys()),
    'models_trained': list(models.keys()),
    'best_cv_score': max([r['cv_mean'] for r in results.values()]),
    'timestamp': datetime.now().isoformat(),
}

summary_path = Path(DATA_OUTPUT_DIR) / "ml_pipeline_summary.json"
with open(summary_path, 'w') as f:
    json.dump(summary, f, indent=2)
print(f"✅ Summary saved: {summary_path}")

print("\n" + "=" * 80)
print("✅ ML PIPELINE EXECUTION COMPLETE!")
print("=" * 80)
print(f"\nNext Steps:")
print(f"  1. Review model performance")
print(f"  2. Analyze anomaly detection quality")
print(f"  3. Validate fraud detection (INVOICED_NOT_DELIVERED)")
print(f"  4. Prepare production deployment")
