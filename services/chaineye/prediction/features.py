"""
Feature extraction for XGBoost withdrawal window and urgency prediction.
Extracts behavioral, temporal, and flow features from wallet history and complaint profiles.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional, Sequence

from services.chaineye.graph.explorer import TransactionRecord


@dataclass
class WithdrawalFeatures:
    inflow_amount_usd: float
    wallet_age_days: float
    dormancy_hours: float
    complaint_lag_hours: float
    historical_peak_hour: int
    peeling_hop_count: int
    mixer_used_flag: float
    tx_velocity_per_hour: float

    def to_feature_vector(self) -> list[float]:
        return [
            math.log1p(self.inflow_amount_usd),
            self.wallet_age_days,
            self.dormancy_hours,
            self.complaint_lag_hours,
            float(self.historical_peak_hour),
            float(self.peeling_hop_count),
            self.mixer_used_flag,
            self.tx_velocity_per_hour,
        ]


def extract_withdrawal_features(
    transactions: Sequence[TransactionRecord],
    complaint_timestamp: Optional[datetime] = None,
    actor_profile: Optional[dict[str, Any]] = None,
) -> WithdrawalFeatures:
    """
    Extracts structured feature vector from on-chain transactions and optional complaint context.
    """
    now = datetime.now(timezone.utc)
    if not transactions:
        return WithdrawalFeatures(
            inflow_amount_usd=50000.0,
            wallet_age_days=14.0,
            dormancy_hours=48.0,
            complaint_lag_hours=12.0,
            historical_peak_hour=20,
            peeling_hop_count=3,
            mixer_used_flag=0.0,
            tx_velocity_per_hour=0.5,
        )

    timestamps = sorted([tx.timestamp for tx in transactions])
    first_seen = timestamps[0]
    last_seen = timestamps[-1]

    wallet_age_days = max(1.0, (now - first_seen).total_seconds() / 86400.0)

    # Inflow calculation
    inflow_usd = sum(tx.amount_usd for tx in transactions)

    # Dormancy calculation (gap before recent activity)
    if len(timestamps) > 1:
        gaps = [(t2 - t1).total_seconds() / 3600.0 for t1, t2 in zip(timestamps[:-1], timestamps[1:])]
        dormancy_hours = max(gaps) if gaps else 24.0
    else:
        dormancy_hours = 48.0

    # Complaint lag (difference between last seen tx and complaint submission)
    if complaint_timestamp:
        complaint_lag_hours = max(0.5, (complaint_timestamp - last_seen).total_seconds() / 3600.0)
    else:
        complaint_lag_hours = 8.0

    # Historical peak hour
    hours = [t.hour for t in timestamps]
    if actor_profile and actor_profile.get("active_hours"):
        peak_hour = actor_profile["active_hours"][0]
    elif hours:
        peak_hour = max(set(hours), key=hours.count)
    else:
        peak_hour = 20

    # Mixer flag
    mixer_flag = 1.0 if any("tornado" in tx.to_address.lower() or "mixer" in tx.to_address.lower() for tx in transactions) else 0.0

    velocity = len(transactions) / max(1.0, (last_seen - first_seen).total_seconds() / 3600.0)

    return WithdrawalFeatures(
        inflow_amount_usd=round(inflow_usd, 2),
        wallet_age_days=round(wallet_age_days, 1),
        dormancy_hours=round(dormancy_hours, 1),
        complaint_lag_hours=round(complaint_lag_hours, 1),
        historical_peak_hour=peak_hour,
        peeling_hop_count=min(5, len(transactions) // 2 + 1),
        mixer_used_flag=mixer_flag,
        tx_velocity_per_hour=round(velocity, 3),
    )
