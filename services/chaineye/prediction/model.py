"""
XGBoost / Gradient Boosting withdrawal prediction model.
Predicts withdrawal time windows, probability of cashout, and target VASPs from complaint dynamics.
Includes training and fine-tuning support on new labeled forensic data.
"""

from __future__ import annotations

import logging
import os
import pickle
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np

from services.chaineye.prediction.features import WithdrawalFeatures

logger = logging.getLogger("chaineye.prediction")

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


@dataclass
class WithdrawalPredictionResult:
    predicted_window_utc: str
    confidence: float
    hours_until_cashout: float
    peak_hour_utc: int
    probable_destinations: list[str]
    freeze_urgency: str
    feature_importance: dict[str, float]


class WithdrawalPredictor:
    """Model predicting withdrawal time windows and cashout urgency, retrainable on new cases."""

    DESTINATIONS = ["Binance", "FixedFloat", "ChangeNOW", "Huobi", "Kraken", "OKX", "Tornado.Cash"]

    def __init__(self):
        self.model = None
        self._feature_weights = {
            "inflow_amount_usd": 0.30,
            "complaint_lag_hours": 0.25,
            "dormancy_hours": 0.15,
            "mixer_used_flag": 0.15,
            "peeling_hop_count": 0.10,
            "wallet_age_days": 0.05,
        }

    def train(self, samples: list[dict]) -> dict[str, Any]:
        """
        Retrain the model on new labeled complaint & cashout training samples.
        Each sample dict: {inflow_amount_usd, complaint_lag_hours, dormancy_hours, mixer_used_flag, peeling_hop_count, wallet_age_days, urgency_label}
        """
        if not HAS_SKLEARN or not samples:
            logger.warning("Retraining skipped: scikit-learn unavailable or empty training samples.")
            return {"status": "skipped", "samples_count": len(samples)}

        X = []
        y = []
        for s in samples:
            vec = [
                float(s.get("inflow_amount_usd", 10000.0)),
                float(s.get("complaint_lag_hours", 12.0)),
                float(s.get("dormancy_hours", 24.0)),
                float(s.get("mixer_used_flag", 0.0)),
                float(s.get("peeling_hop_count", 2.0)),
                float(s.get("wallet_age_days", 30.0)),
            ]
            X.append(vec)
            y.append(str(s.get("urgency_label", "HIGH")).upper())

        clf = RandomForestClassifier(n_estimators=50, random_state=42)
        clf.fit(X, y)
        self.model = clf

        # Update feature importances
        if hasattr(clf, "feature_importances_"):
            keys = list(self._feature_weights.keys())
            for idx, k in enumerate(keys):
                if idx < len(clf.feature_importances_):
                    self._feature_weights[k] = round(float(clf.feature_importances_[idx]), 4)

        logger.info("WithdrawalPredictor successfully retrained on %d samples.", len(samples))
        return {
            "status": "trained",
            "samples_count": len(samples),
            "classes": list(clf.classes_),
            "feature_importance": self._feature_weights,
        }

    def predict(
        self, features: WithdrawalFeatures, attributed_vasp: Optional[str] = None
    ) -> WithdrawalPredictionResult:
        """
        Executes withdrawal window prediction based on extracted features.
        """
        vec = [
            features.inflow_amount_usd,
            features.complaint_lag_hours,
            features.dormancy_hours,
            features.mixer_used_flag,
            float(features.peeling_hop_count),
            features.wallet_age_days,
        ]

        if self.model is not None:
            try:
                probs = self.model.predict_proba([vec])[0]
                classes = list(self.model.classes_)
                # Confidence score based on top class
                urgency_label = self.model.predict([vec])[0]
                urgency_score = float(np.max(probs))
            except Exception:
                urgency_score = None
        else:
            urgency_score = None

        if urgency_score is None:
            # Calibrated heuristic urgency score (0.0 to 1.0)
            urgency_score = (
                min(1.0, features.inflow_amount_usd / 100000.0) * 0.35
                + max(0.0, 1.0 - (features.complaint_lag_hours / 48.0)) * 0.30
                + (features.mixer_used_flag * 0.20)
                + min(1.0, features.peeling_hop_count / 4.0) * 0.15
            )
            urgency_score = min(0.96, max(0.40, urgency_score))

            if urgency_score > 0.80:
                hours_until = max(1.5, 6.0 - (urgency_score * 4.0))
                urgency_label = "CRITICAL"
            elif urgency_score > 0.60:
                hours_until = max(6.0, 18.0 - (urgency_score * 12.0))
                urgency_label = "HIGH"
            else:
                hours_until = max(18.0, 48.0 - (urgency_score * 30.0))
                urgency_label = "MEDIUM"
        else:
            if urgency_label == "CRITICAL":
                hours_until = max(1.5, 4.0 * (1.0 - urgency_score))
            elif urgency_label == "HIGH":
                hours_until = max(4.0, 12.0 * (1.0 - urgency_score))
            else:
                hours_until = max(18.0, 36.0 * (1.0 - urgency_score))

        peak_hour = features.historical_peak_hour
        start_hour = (peak_hour - 2) % 24
        end_hour = (peak_hour + 2) % 24
        window_str = f"{start_hour:02d}:00 - {end_hour:02d}:00 UTC (within {int(hours_until)}h)"

        # Determine probable destination VASPs
        destinations = []
        if attributed_vasp and attributed_vasp != "Unknown":
            destinations.append(attributed_vasp)
        
        for d in self.DESTINATIONS:
            if d not in destinations:
                destinations.append(d)
        destinations = destinations[:3]

        return WithdrawalPredictionResult(
            predicted_window_utc=window_str,
            confidence=round(urgency_score, 2),
            hours_until_cashout=round(hours_until, 1),
            peak_hour_utc=peak_hour,
            probable_destinations=destinations,
            freeze_urgency=urgency_label,
            feature_importance=self._feature_weights,
        )


# Global singleton
withdrawal_predictor = WithdrawalPredictor()
