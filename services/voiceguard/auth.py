"""Thin auth shim for VoiceGuard / ShadowTrace / ChainEye.

Each service imports this instead of duplicating auth logic.
JWT_SECRET must match the value in case-engine (shared via env var).
"""

import os
import sys

# Ensure shared/ is importable
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
for p in (_root, os.path.join(_root, "shared")):
    if p not in sys.path:
        sys.path.insert(0, p)

from shared.auth import Role, TokenPayload, get_current_user, require_role  # noqa: F401
