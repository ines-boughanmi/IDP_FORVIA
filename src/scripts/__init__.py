"""
SAP P2P Anomaly Detection Pipeline - Main Package

Modules:
- config: Configuration centralisée
- logger: Logging standardisé
- utils: Utilitaires généraux
- data: Data loading & preparation
- features: Feature engineering
- anomaly: Anomaly detection & labeling
- models: ML models & training
- deployment: Model deployment & inference
"""

__version__ = "1.0.0"
__author__ = "Data Science Team"

# Import main utilities
from .config import (
    PROJECT_ROOT, SRC_DIR, DATA_DIR, MODELS_DIR,
    RAW_DATA_FILE, ML_FEATURES_X_FILE, ML_FEATURES_Y_FILE,
    FORVIA_COLORS, RANDOM_SEED
)

from .logger import setup_logger, get_logger, logger

__all__ = [
    'PROJECT_ROOT', 'SRC_DIR', 'DATA_DIR', 'MODELS_DIR',
    'RAW_DATA_FILE', 'ML_FEATURES_X_FILE', 'ML_FEATURES_Y_FILE',
    'FORVIA_COLORS', 'RANDOM_SEED',
    'setup_logger', 'get_logger', 'logger',
]
