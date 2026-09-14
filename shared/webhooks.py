"""Webhook event notification system for Eye of Abyss."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.request import Request, urlopen
from urllib.error import URLError

from pydantic import BaseModel, Field, HttpUrl
from shared.logging_config import setup_logger

logger = setup_logger("eob.webhooks")


class WebhookSubscription(BaseModel):
    id: str = Field(default_factory=lambda: hashlib.sha256(os.urandom(16)).hexdigest()[:12])
    url: str
    secret: str = Field(default_factory=lambda: hashlib.sha256(os.urandom(32)).hexdigest())
    events: list[str] = Field(default_factory=lambda: ["*"])  # e.g. ["case.anchored", "threat.high_alert", "evidence.submitted"]
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# In-memory webhook store
_WEBHOOKS: dict[str, WebhookSubscription] = {}


def register_webhook(url: str, secret: str | None = None, events: list[str] | None = None) -> WebhookSubscription:
    """Register a new webhook subscription."""
    sub = WebhookSubscription(
        url=url,
        secret=secret or hashlib.sha256(os.urandom(32)).hexdigest(),
        events=events or ["*"],
    )
    _WEBHOOKS[sub.id] = sub
    logger.info(f"Registered webhook {sub.id} -> {url} for events: {sub.events}")
    return sub


def list_webhooks() -> list[WebhookSubscription]:
    """List all active webhook subscriptions."""
    return list(_WEBHOOKS.values())


def remove_webhook(sub_id: str) -> bool:
    """Remove a webhook subscription."""
    if sub_id in _WEBHOOKS:
        del _WEBHOOKS[sub_id]
        logger.info(f"Removed webhook {sub_id}")
        return True
    return False


def _send_webhook_sync(url: str, secret: str, payload_bytes: bytes, event_type: str) -> bool:
    """Send HTTP POST with HMAC-SHA256 signature."""
    timestamp = str(int(time.time()))
    signature = hmac.new(
        secret.encode("utf-8"),
        f"{timestamp}.".encode("utf-8") + payload_bytes,
        hashlib.sha256,
    ).hexdigest()

    req = Request(
        url,
        data=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "EyeOfAbyss-Webhook/1.0",
            "X-EOB-Event": event_type,
            "X-EOB-Timestamp": timestamp,
            "X-EOB-Signature": f"sha256={signature}",
        },
        method="POST",
    )

    try:
        with urlopen(req, timeout=5.0) as resp:
            return 200 <= resp.status < 300
    except Exception as exc:
        logger.warning(f"Webhook delivery failed for {url} ({event_type}): {exc}")
        return False


async def dispatch_webhook_event(event_type: str, data: dict[str, Any]) -> int:
    """Dispatch an event to all matching webhook subscriptions asynchronously."""
    payload = {
        "event": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }
    payload_bytes = json.dumps(payload, default=str).encode("utf-8")

    matching = [
        sub for sub in _WEBHOOKS.values()
        if sub.is_active and ("*" in sub.events or event_type in sub.events)
    ]

    if not matching:
        return 0

    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(None, _send_webhook_sync, sub.url, sub.secret, payload_bytes, event_type)
        for sub in matching
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    delivered = sum(1 for r in results if r is True)
    logger.info(f"Dispatched {event_type} to {len(matching)} endpoints ({delivered} succeeded)")
    return delivered
