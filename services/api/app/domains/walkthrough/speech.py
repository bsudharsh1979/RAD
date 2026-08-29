"""Speak-normalize lecture text. Never invent course facts here — only pronunciation."""

from __future__ import annotations

import re

NUM_HEADING = re.compile(r"^\s*\d+(?:\.\d+)*\s+")
DOUBLE_PUNCT = re.compile(r"\?\.")
N_OF_N = re.compile(r"\b(\d+)\s*/\s*(\d+)\b")
ARROW = re.compile(r"\s*(→|->|⇒)\s*")
EQUALS = re.compile(r"\s*=\s*")
SLASH_OR = re.compile(r"(?<=[A-Za-z0-9])/(?=[A-Za-z0-9])")


def humanize_title(title: str) -> str:
    t = HTML_STRIP.sub("", title or "")
    t = t.replace("**", "").strip()
    t = NUM_HEADING.sub("", t)
    return re.sub(r"\s+", " ", t).strip()


HTML_STRIP = re.compile(r"<[^>]+>")


def speak_normalize(text: str) -> str:
    t = HTML_STRIP.sub(" ", text or "")
    t = t.replace("**", "")
    t = DOUBLE_PUNCT.sub("?", t)
    t = ARROW.sub(" then ", t)
    t = N_OF_N.sub(r"\1 of \2", t)
    t = EQUALS.sub(" equals ", t)
    t = SLASH_OR.sub(" or ", t)
    t = t.replace("```", " code fence ")
    t = re.sub(r"`([^`]+)`", r"\1", t)
    t = re.sub(r"\s+", " ", t).strip()
    if t.endswith("?.") or t.endswith("??"):
        t = t.rstrip(".?") + "?"
    return t


def clip_text(text: str, *, clip: bool, limit: int = 520) -> str:
    """clip=false must NEVER shorten text (regression: walkthrough audio died at ~520)."""
    if clip:
        return text[:limit]
    return text


JARGON_BLOCKLIST_SIMPLE = {
    "disaggregated serving",
    "kv-aware routing",
    "podclique",
    "podgang",
    "grove",
    "keda",
    "nixl",
    "kvbm",
    "dynamo graph",
}
