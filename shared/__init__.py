"""Eye of Abyss shared schemas."""
import numpy as np

# Compatibility with NetworkX and NumPy 2.0+
if not hasattr(np, "float_"):
    np.float_ = np.float64  # type: ignore
if not hasattr(np, "int_"):
    np.int_ = np.int64  # type: ignore
if not hasattr(np, "complex_"):
    np.complex_ = np.complex128  # type: ignore

from .schemas import (
    Artifact,
    CrossModuleSignals,
    EvidenceObject,
    CriminalActorProfile,
    CaseFile,
    ModuleEvidence,
    CreateCaseRequest,
    CaseResponse,
)

__all__ = [
    "Artifact",
    "CrossModuleSignals",
    "EvidenceObject",
    "CriminalActorProfile",
    "CaseFile",
    "ModuleEvidence",
    "CreateCaseRequest",
    "CaseResponse",
]
