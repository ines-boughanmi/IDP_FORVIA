"""
ML Prediction Service.

Charge les modèles entraînés (LightGBM, Isolation Forest, K-Means)
et pré-calcule les prédictions sur toutes les transactions au démarrage.
"""

import logging
import json
import pickle
from pathlib import Path
from typing import Optional, Dict, Any, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

MODEL_DIR   = Path("src/models")
FEATURE_CSV = Path("src/data/processed/ml_features_phase2_X.csv")
IDS_CSV     = Path("src/data/processed/ml_features_phase2_ids.csv")


class MLService:
    """Service de prédictions ML branché sur les modèles entraînés."""

    def __init__(self):
        self.is_ready = False
        self._lgbm       = None
        self._iso        = None
        self._kmeans     = None
        self._scaler     = None
        self._label_enc  = {}   # int → label str
        self._predictions: Optional[pd.DataFrame] = None

    # ------------------------------------------------------------------
    def load(self, transactions_df: pd.DataFrame) -> bool:
        """
        Charge les modèles et pré-calcule les prédictions pour toutes
        les transactions. Appelé une fois au démarrage de l'API.
        """
        try:
            self._load_models()
            self._compute_predictions(transactions_df)
            self.is_ready = True
            logger.info("MLService ready — %d predictions computed", len(self._predictions))
            return True
        except Exception:
            logger.exception("MLService.load() failed")
            return False

    def _load_models(self):
        with open(MODEL_DIR / "lightgbm_model.pkl", "rb") as f:
            self._lgbm = pickle.load(f)
        with open(MODEL_DIR / "isolation_forest_model.pkl", "rb") as f:
            self._iso = pickle.load(f)
        with open(MODEL_DIR / "kmeans_model.pkl", "rb") as f:
            self._kmeans = pickle.load(f)
        with open(MODEL_DIR / "scaler.pkl", "rb") as f:
            self._scaler = pickle.load(f)
        with open(MODEL_DIR / "label_encoder.json", "r") as f:
            enc = json.load(f)
            self._label_enc = {v: k for k, v in enc.items()}  # int → str
        logger.info("ML models loaded: LightGBM, IsolationForest, KMeans")

    def _compute_predictions(self, transactions_df: pd.DataFrame):
        """Charge la matrice de features et calcule toutes les prédictions."""
        if not FEATURE_CSV.exists():
            raise FileNotFoundError(f"Feature matrix not found: {FEATURE_CSV}")

        X_df     = pd.read_csv(FEATURE_CSV).fillna(0)
        X_scaled = self._scaler.transform(X_df)

        # Supervised: anomaly type + confidence
        lgbm_codes  = self._lgbm.predict(X_scaled)
        lgbm_proba  = self._lgbm.predict_proba(X_scaled)
        lgbm_conf   = lgbm_proba.max(axis=1)
        lgbm_labels = [self._label_enc[c] for c in lgbm_codes]

        # Unsupervised: isolation score + cluster
        iso_scores  = self._iso.score_samples(X_scaled)
        iso_flags   = (self._iso.predict(X_scaled) == -1).astype(int)
        km_clusters = self._kmeans.predict(X_scaled)

        # Join key: SAP document IDs saved alongside feature matrix
        if IDS_CSV.exists():
            transaction_ids = pd.read_csv(IDS_CSV)["transaction_id"].values
        else:
            # Fallback: align by position with transactions_df
            logger.warning("IDs file missing — aligning by row position (may be inaccurate)")
            n = min(len(X_df), len(transactions_df))
            transaction_ids = transactions_df["transaction_id"].iloc[:n].values

        n = len(transaction_ids)
        self._predictions = pd.DataFrame({
            "transaction_id"    : transaction_ids[:n],
            "ml_anomaly_type"   : lgbm_labels[:n],
            "ml_confidence"     : lgbm_conf[:n].round(4),
            "ml_isolation_score": iso_scores[:n].round(4),
            "ml_is_anomaly"     : iso_flags[:n],
            "ml_cluster"        : km_clusters[:n],
        }).drop_duplicates("transaction_id").set_index("transaction_id")

    # ------------------------------------------------------------------
    def get_prediction(self, transaction_id: int) -> Optional[Dict[str, Any]]:
        if not self.is_ready or self._predictions is None:
            return None
        if transaction_id not in self._predictions.index:
            return None
        row = self._predictions.loc[transaction_id]
        return {
            "transaction_id"    : int(transaction_id),
            "ml_anomaly_type"   : str(row["ml_anomaly_type"]),
            "ml_confidence"     : float(row["ml_confidence"]),
            "ml_isolation_score": float(row["ml_isolation_score"]),
            "ml_is_anomaly"     : int(row["ml_is_anomaly"]),
            "ml_cluster"        : int(row["ml_cluster"]),
        }

    def get_top_anomalies(self, limit: int = 50) -> List[Dict[str, Any]]:
        if not self.is_ready or self._predictions is None:
            return []
        top = (
            self._predictions
            .sort_values("ml_isolation_score")  # score le plus négatif = plus anormal
            .head(limit)
            .reset_index()
        )
        return top.to_dict(orient="records")

    def get_status(self) -> Dict[str, Any]:
        n_anomalies = int(self._predictions["ml_is_anomaly"].sum()) if self.is_ready else 0
        clusters    = (
            self._predictions["ml_cluster"].value_counts().to_dict()
            if self.is_ready else {}
        )
        return {
            "ready"              : self.is_ready,
            "total_transactions" : len(self._predictions) if self.is_ready else 0,
            "models"             : ["lightgbm", "isolation_forest", "kmeans"],
            "anomalies_detected" : n_anomalies,
            "anomaly_rate_pct"   : round(n_anomalies / len(self._predictions) * 100, 2) if self.is_ready else 0,
            "cluster_distribution": {f"cluster_{k}": v for k, v in clusters.items()},
            "label_classes"      : list(self._label_enc.values()),
        }
