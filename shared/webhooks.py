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
from shared.net_guard import UnsafeUrlError, assert_public_http_url
from shared.runtime_config import is_production

logger = setup_logger("eob.webhooks")


class WebhookSubscription(BaseModel):
    id: str = Field(default_factory=lambda: hashlib.sha256(os.urandom(16)).hexdigest()[:12])
    url: str
    secret: str = Field(default_factory=lambda: hashlib.sha256(os.urandom(32)).hexdigest())
    events: list[str] = Field(default_factory=lambda: ["*"])  # e.g. ["case.anchored", "threat.high_alert", "evidence.submitted"]
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# Webhook store: persistent in Redis with in-memory fallback
# ponytail: Redis hash 'eob:webhooks' provides multi-replica persistence without schema migrations
_WEBHOOKS: dict[str, WebhookSubscription] = {}
_REDIS_CLIENT = None


def _get_redis():
    global _REDIS_CLIENT
    if _REDIS_CLIENT is None:
        url = os.getenv("REDIS_URL")
        if url:
            try:
                import redis
                _REDIS_CLIENT = redis.from_url(url, socket_timeout=1.5, socket_connect_timeout=1.5, decode_responses=True)
            except Exception:
                _REDIS_CLIENT = None
    return _REDIS_CLIENT


def register_webhook(url: str, secret: str | None = None, events: list[str] | None = None) -> WebhookSubscription:
    """Register a new webhook subscription. Private and metadata targets are rejected."""
    try:
        url = assert_public_http_url(url, https_only=is_production())
    except UnsafeUrlError as exc:
        raise ValueError(str(exc)) from exc
    sub = WebhookSubscription(
        url=url,
        secret=secret or hashlib.sha256(os.urandom(32)).hexdigest(),
        events=events or ["*"],
    )
    r = _get_redis()
    if r:
        try:
            r.hset("eob:webhooks", sub.id, sub.model_dump_json())
        except Exception:
            _WEBHOOKS[sub.id] = sub
    else:
        _WEBHOOKS[sub.id] = sub
    logger.info(f"Registered webhook {sub.id} -> {url} for events: {sub.events}")
    return sub


def list_webhooks() -> list[WebhookSubscription]:
    """List all active webhook subscriptions."""
    r = _get_redis()
    if r:
        try:
            items = r.hgetall("eob:webhooks")
            if items:
                return [WebhookSubscription.model_validate_json(v) for v in items.values()]
        except Exception:
            pass
    return list(_WEBHOOKS.values())


def remove_webhook(sub_id: str) -> bool:
    """Remove a webhook subscription."""
    r = _get_redis()
    deleted = False
    if r:
        try:
            deleted = bool(r.hdel("eob:webhooks", sub_id))
        except Exception:
            pass
    if sub_id in _WEBHOOKS:
        del _WEBHOOKS[sub_id]
        deleted = True
    if deleted:
        logger.info(f"Removed webhook {sub_id}")
    return deleted


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
        assert_public_http_url(url, https_only=is_production())
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
        sub for sub in list_webhooks()
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
