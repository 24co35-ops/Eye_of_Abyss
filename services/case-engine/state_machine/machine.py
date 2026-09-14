"""
Case state machine — exactly as defined in design-doc.md §3.

CREATED -> ACTIVE -> EVIDENCE_SUBMITTED -> CONVERGENCE_COMPUTED
        -> READY_TO_ANCHOR -> ANCHORED -> FILED -> CLOSED

Transitions are a plain dict; no class hierarchy needed.
"""

from typing import Literal

CaseStatus = Literal[
    "CREATED", "ACTIVE", "EVIDENCE_SUBMITTED",
    "CONVERGENCE_COMPUTED", "READY_TO_ANCHOR",
    "ANCHORED", "FILED", "CLOSED",
]

# ponytail: dict covers all valid transitions; anything not listed is rejected
TRANSITIONS: dict[str, list[str]] = {
    "CREATED":              ["ACTIVE"],
    "ACTIVE":               ["EVIDENCE_SUBMITTED"],
    "EVIDENCE_SUBMITTED":   ["CONVERGENCE_COMPUTED", "READY_TO_ANCHOR"],  # manual override path
    "CONVERGENCE_COMPUTED": ["READY_TO_ANCHOR"],
    "READY_TO_ANCHOR":      ["ANCHORED"],
    "ANCHORED":             ["FILED"],
    "FILED":                ["CLOSED"],
    "CLOSED":               [],
}


class InvalidTransition(ValueError):
    pass


def transition(current: str, target: str) -> str:
    """Return target status if transition is valid, else raise."""
    if target not in TRANSITIONS.get(current, []):
        raise InvalidTransition(
            f"Cannot move from {current} to {target}. "
            f"Valid next states: {TRANSITIONS.get(current, [])}"
        )
    return target


def auto_advance(current: str, evidence_modules: list[str], assigned_modules: list[str]) -> str | None:
    """
    Return the next status to auto-advance to based on evidence state,
    or None if no auto-advance applies.

    Rules from design-doc:
    - CREATED -> ACTIVE on first evidence submission
    - ACTIVE -> EVIDENCE_SUBMITTED when all assigned modules have submitted
    - EVIDENCE_SUBMITTED -> CONVERGENCE_COMPUTED when 2+ modules submitted (auto)
    """
    submitted = set(evidence_modules)
    assigned  = set(assigned_modules)

    if current == "CREATED" and submitted:
        return "ACTIVE"
    if current == "ACTIVE" and assigned and submitted >= assigned:
        return "EVIDENCE_SUBMITTED"
    if current == "EVIDENCE_SUBMITTED" and len(submitted) >= 2:
        return "CONVERGENCE_COMPUTED"
    return None
