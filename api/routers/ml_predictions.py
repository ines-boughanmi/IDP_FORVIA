"""ML Predictions router."""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import Request
from ..services.ml_service import MLService
from ..auth.dependencies import get_current_user

router = APIRouter(tags=["ML Predictions"])


def get_ml_service(request: Request) -> MLService:
    return request.app.state.ml_service


@router.get("/ml/status")
def ml_status(
    ml: MLService = Depends(get_ml_service),
    current_user: dict = Depends(get_current_user),
):
    """État des modèles ML et statistiques globales."""
    return {"status": "ok", "data": ml.get_status()}


@router.get("/ml/predict/{transaction_id}")
def ml_predict(
    transaction_id: int,
    ml: MLService = Depends(get_ml_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Prédiction ML pour une transaction donnée.

    Retourne :
    - ml_anomaly_type   : classe prédite (ACCOUNTING / DATA / NONE)
    - ml_confidence     : score de confiance LightGBM (0-1)
    - ml_isolation_score: score Isolation Forest (plus négatif = plus suspect)
    - ml_is_anomaly     : 1 si détecté comme anomalie par Isolation Forest
    - ml_cluster        : segment K-Means (0-4)
    """
    if not ml.is_ready:
        raise HTTPException(status_code=503, detail="ML models not loaded yet")
    result = ml.get_prediction(transaction_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")
    return {"status": "ok", "data": result}


@router.get("/ml/anomalies")
def ml_top_anomalies(
    limit: int = Query(default=50, ge=1, le=500),
    ml: MLService = Depends(get_ml_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Top transactions les plus suspectes selon Isolation Forest.
    Triées par score d'isolation croissant (plus anormal en premier).
    """
    if not ml.is_ready:
        raise HTTPException(status_code=503, detail="ML models not loaded yet")
    anomalies = ml.get_top_anomalies(limit=limit)
    return {"status": "ok", "data": anomalies, "count": len(anomalies)}
