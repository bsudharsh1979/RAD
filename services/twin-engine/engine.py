"""Shared TwinStateEngine (imported by API and Omniverse bridge)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

from app.domains.twins.engine import SCENARIOS, TWIN_CATALOG, run, sanitize  # noqa: E402,F401
