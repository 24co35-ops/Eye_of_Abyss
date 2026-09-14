"""VoiceGuard __init__ — expose public API."""
from .model import load_models, infer_window, aggregate_windows, AudioResult, WindowResult
from .artifacts import generate_artifacts

__all__ = [
    "load_models",
    "infer_window",
    "aggregate_windows",
    "generate_artifacts",
    "AudioResult",
    "WindowResult",
]
