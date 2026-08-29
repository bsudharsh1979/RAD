"""Deterministic content IDs. Modal SQLite is ephemeral — uuid4 breaks every cold start."""

from __future__ import annotations

import hashlib


def sha1_hex(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def artifact_id(path: str) -> str:
    """sha1(path) — stable across containers."""
    return sha1_hex(str(path).replace("\\", "/"))


def span_id(artifact: str, locator: str, kind: str, seq: int) -> str:
    """sha1(artifact:locator:kind:seq)."""
    return sha1_hex(f"{artifact}:{locator}:{kind}:{seq}")


def notebook_id(path: str) -> str:
    return sha1_hex(f"notebook:{str(path).replace('\\', '/')}")


def cell_id(nb: str, index: int) -> str:
    return span_id(nb, f"cell:{index}", "cell", index)
