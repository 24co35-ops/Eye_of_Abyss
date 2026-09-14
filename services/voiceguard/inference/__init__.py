"""VoiceGuard __init__ — expose public API."""
from .model import (
    load_models,
    infer_window,
    aggregate_windows,
    get_device_info,
    ECAPATDNN,
    ECAPAStub,
    AudioResult,
    WindowResult,
)
from .artifacts import generate_artifacts

__all__ = [
    "load_models",
    "infer_window",
    "aggregate_windows",
    "get_device_info",
    "ECAPATDNN",
    "ECAPAStub",
    "generate_artifacts",
    "AudioResult",
    "WindowResult",
]
