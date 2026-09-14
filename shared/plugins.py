"""Plugin-style module registration system for Eye of Abyss.

Enables registering new investigation modules dynamically with capabilities,
endpoints, schemas, and health checks without modifying Case Engine core.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Literal
from urllib.request import Request, urlopen
from pydantic import BaseModel, Field

from shared.logging_config import setup_logger

logger = setup_logger("eob.plugins")


class ModuleManifest(BaseModel):
    module_id: str = Field(..., description="Unique slug for module, e.g. voiceguard, imageguard")
    name: str = Field(..., description="Human-readable module name")
    description: str = Field(default="")
    version: str = Field(default="1.0.0")
    endpoint_url: str = Field(..., description="Base URL of the module microservice")
    health_endpoint: str = Field(default="/health")
    icon: str = Field(default="Shield", description="Lucide icon name or emoji")
    capabilities: list[str] = Field(default_factory=list)
    accepted_input_types: list[str] = Field(default_factory=list)  # e.g. ["audio/wav", "crypto/tx", "text/plain"]
    registered_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_active: bool = True


# Built-in default modules
_DEFAULT_MODULES: dict[str, ModuleManifest] = {
    "voiceguard": ModuleManifest(
        module_id="voiceguard",
        name="VoiceGuard",
        description="Audio deepfake detection & speaker verification ensemble",
        version="1.0.0",
        endpoint_url=os.getenv("VOICEGUARD_URL", "http://localhost:8001"),
        icon="Mic",
        capabilities=["deepfake_detection", "speaker_verification", "realtime_streaming"],
        accepted_input_types=["audio/wav", "audio/mp3", "audio/m4a", "audio/flac"],
    ),
    "chaineye": ModuleManifest(
        module_id="chaineye",
        name="ChainEye",
        description="Multi-chain crypto forensics, clustering, and withdrawal prediction",
        version="1.0.0",
        endpoint_url=os.getenv("CHAINEYE_URL", "http://localhost:8002"),
        icon="Network",
        capabilities=["utxo_clustering", "vasp_attribution", "withdrawal_prediction"],
        accepted_input_types=["crypto/address", "crypto/tx_hash"],
    ),
    "shadowtrace": ModuleManifest(
        module_id="shadowtrace",
        name="ShadowTrace",
        description="Dark web linguistic profiling and actor persona attribution",
        version="1.0.0",
        endpoint_url=os.getenv("SHADOWTRACE_URL", "http://localhost:8003"),
        icon="Fingerprint",
        capabilities=["stylometry", "temporal_correlation", "actor_graph"],
        accepted_input_types=["text/plain", "actor/handle"],
    ),
}

_REGISTRY: dict[str, ModuleManifest] = dict(_DEFAULT_MODULES)


def register_module(manifest: ModuleManifest) -> ModuleManifest:
    """Register or update a module in the registry."""
    _REGISTRY[manifest.module_id] = manifest
    logger.info(f"Registered plugin module '{manifest.module_id}' ({manifest.name}) at {manifest.endpoint_url}")
    return manifest


def get_module(module_id: str) -> ModuleManifest | None:
    """Get manifest for a specific module."""
    return _REGISTRY.get(module_id)


def list_modules() -> list[ModuleManifest]:
    """List all registered modules."""
    return list(_REGISTRY.values())


def check_module_health(module_id: str) -> dict[str, Any]:
    """Check live status of a registered module."""
    manifest = get_module(module_id)
    if not manifest:
        return {"status": "not_found", "module_id": module_id}
    
    url = f"{manifest.endpoint_url.rstrip('/')}/{manifest.health_endpoint.lstrip('/')}"
    try:
        req = Request(url, headers={"User-Agent": "EyeOfAbyss-PluginManager/1.0"})
        with urlopen(req, timeout=3.0) as resp:
            return {"status": "healthy" if resp.status == 200 else "degraded", "code": resp.status, "module_id": module_id}
    except Exception as exc:
        return {"status": "unreachable", "error": str(exc), "module_id": module_id}
