"""
Configuration centralisée pour le projet SAP P2P
Contient tous les paramètres, chemins, et constantes métier
"""

import os
from pathlib import Path
from datetime import datetime

# ============================================
# PATHS & DIRECTORIES
# ============================================

PROJECT_ROOT = Path(__file__).parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
SCRIPTS_DIR = SRC_DIR / "scripts"
NOTEBOOKS_DIR = SRC_DIR / "notebooks"
DATA_DIR = SRC_DIR / "data"
MODELS_DIR = SRC_DIR / "models"
DOCS_DIR = SRC_DIR / "docs"

# Data paths
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
RULE_BASED_LABELS_DIR = DATA_DIR / "rule_based_labels"
RISK_SCORES_DIR = DATA_DIR / "risk_scores"

# Output paths
OUTPUTS_DIR = SRC_DIR / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
REPORTS_DIR = OUTPUTS_DIR / "reports"
PREDICTIONS_DIR = OUTPUTS_DIR / "predictions"

# Ensure directories exist
for dir_path in [PROCESSED_DATA_DIR, RULE_BASED_LABELS_DIR, RISK_SCORES_DIR, 
                 OUTPUTS_DIR, FIGURES_DIR, REPORTS_DIR, PREDICTIONS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ============================================
# DATA FILES
# ============================================

RAW_DATA_FILE = RAW_DATA_DIR / "Documents1.csv"

# Phase 1 outputs
ML_FEATURES_X_FILE = PROCESSED_DATA_DIR / "ml_features_phase2_X.csv"
ML_FEATURES_Y_FILE = PROCESSED_DATA_DIR / "ml_features_phase2_y.csv"
LABELED_DATA_FILE = PROCESSED_DATA_DIR / "documents_with_labels_and_features_phase1.csv"

# ============================================
# SAP P2P BUSINESS LOGIC
# ============================================

# PO History Categories (po_history_category_|_bewtp)
SAP_CATEGORIES = {
    'E': 'Goods Receipt (Livraison)',
    'Q': 'Invoice Receipt (Facture)',
    'R': 'Return',
}

# Movement Types (movement_type_|_bwart)
SAP_MOVEMENT_TYPES = {
    101: 'Goods Receipt',
    102: 'Goods Return',
    105: 'Invoice Receipt',
    106: 'Credit Memo',
}

# Anomaly Types
ANOMALY_TYPES = {
    'OK': 'Normal - GR + IR present',
    'INCOMPLETE': 'Missing both GR and IR',
    'DELIVERED_NOT_INVOICED': 'GR present but no IR - Accounting risk',
    'INVOICED_NOT_DELIVERED': 'IR present but no GR - Fraud risk',
}

# Anomaly Severity Levels
SEVERITY_LEVELS = {
    'NONE': 0,      # Normal
    'LOW': 1,       # Minor issue
    'MEDIUM': 2,    # Moderate risk
    'HIGH': 3,      # Important anomaly
    'CRITICAL': 4,  # Fraud/major issue
}

# Threshold for anomaly classification
ANOMALY_THRESHOLDS = {
    'amount_gap_pct': 5.0,        # % gap between GR and IR
    'high_risk_supplier': 0.20,   # >20% anomalies = high risk
    'high_volume_supplier': 0.75, # 75th percentile spend
    'days_threshold': 30,         # Days to wait before flagging
}

# ============================================
# FEATURE ENGINEERING CONFIG
# ============================================

# Features to create
FINANCIAL_FEATURES = [
    'total_gr_amount', 'total_ir_amount', 'gr_ir_difference',
    'abs_gr_ir_diff', 'invoice_ratio', 'unit_price', 'total_quantity',
    'amount_per_qty', 'gr_ir_gap_pct', 'blocked_amount'
]

TEMPORAL_FEATURES = [
    'days_in_system', 'posting_month', 'posting_quarter',
    'is_month_end', 'is_quarter_end'
]

SUPPLIER_FEATURES = [
    'supplier_transaction_count', 'supplier_total_spend',
    'supplier_avg_amount', 'supplier_std_amount',
    'supplier_anomaly_rate', 'supplier_avg_aging',
    'supplier_high_risk', 'supplier_high_volume'
]

OPERATIONAL_FEATURES = [
    'delivery_completed', 'document_date_known',
    'has_outline_agreement', 'has_payment_terms'
]

CATEGORICAL_FEATURES = [
    'plant_|_werks_encoded',
    'material_group_|_matkl_encoded',
    'purch_organization_|_ekorg_encoded',
    'supplier_|_lifnr_encoded',
    'purchasing_doc_type_|_bsart_encoded'
]

# ============================================
# ML MODELS CONFIG
# ============================================

# Random seed for reproducibility
RANDOM_SEED = 42

# Train/Test split ratio
TEST_SIZE = 0.2
VALIDATION_SIZE = 0.1

# Cross-validation folds
CV_FOLDS = 5

# SMOTE parameters
SMOTE_CONFIG = {
    'sampling_strategy': 'minority',
    'random_state': RANDOM_SEED,
    'k_neighbors': 5,
}

# Model hyperparameters
MODEL_PARAMS = {
    'logistic_regression': {
        'C': 1.0,
        'max_iter': 1000,
        'random_state': RANDOM_SEED,
    },
    'random_forest': {
        'n_estimators': 100,
        'max_depth': 15,
        'min_samples_split': 10,
        'min_samples_leaf': 5,
        'random_state': RANDOM_SEED,
    },
    'xgboost': {
        'n_estimators': 100,
        'learning_rate': 0.05,
        'max_depth': 7,
        'min_child_weight': 1,
        'random_state': RANDOM_SEED,
    },
    'lightgbm': {
        'n_estimators': 100,
        'learning_rate': 0.05,
        'num_leaves': 31,
        'random_state': RANDOM_SEED,
    },
}

# ============================================
# EVALUATION METRICS
# ============================================

# Classification metrics to compute
CLASSIFICATION_METRICS = [
    'accuracy', 'precision', 'recall', 'f1', 'roc_auc'
]

# Success criteria thresholds
SUCCESS_CRITERIA = {
    'min_accuracy': 0.85,
    'min_precision': 0.80,
    'min_recall': 0.70,
    'min_f1': 0.75,
}

# ============================================
# VISUALIZATION CONFIG
# ============================================

# FORVIA Brand Colors
FORVIA_COLORS = ["#002D72", "#009FE3", "#78BE20", "#FFCB05", "#DA291C"]

# Figure defaults
FIGURE_DPI = 300
FIGURE_SIZE_SMALL = (10, 6)
FIGURE_SIZE_MEDIUM = (14, 8)
FIGURE_SIZE_LARGE = (16, 10)

# ============================================
# LOGGING CONFIG
# ============================================

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = OUTPUTS_DIR / f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# ============================================
# ENVIRONMENT
# ============================================

ENV = os.getenv("ENV", "development")  # development, staging, production
DEBUG = ENV == "development"
