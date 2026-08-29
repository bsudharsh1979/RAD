"""API re-export of the installable twin-engine package."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_PKG = _ROOT / "twin-engine"
if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))

from twin_engine.engine import (  # noqa: E402,F401
    DISCLAIMER,
    EVIDENCE,
    SCENARIOS,
    SUGGESTED,
    TWIN_CATALOG,
    run,
    sanitize,
)
