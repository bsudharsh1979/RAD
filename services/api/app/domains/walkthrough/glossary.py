"""First-mention glossary for SIMPLE walkthroughs. Lowercase prose matches only."""

from __future__ import annotations

import re

# term -> plain gloss. Applied once per walkthrough, not inside proper nouns or parentheses.
GLOSSARY: list[tuple[str, str]] = [
    ("pipeline", "the ready-made wrapper that turns text in and text out"),
    ("tokenizer", "the translator from words into ID numbers"),
    ("token", "a language brick the model can look up"),
    ("embedding", "a list of numbers that stands for a token's meaning"),
    ("attention", "the model's way of deciding which other tokens matter right now"),
    ("encoder", "the half of the model that reads and understands"),
    ("decoder", "the half that writes the next word"),
    ("mask", "a blank the model is asked to fill"),
    ("quantization", "storing weights with fewer bits so they fit in memory"),
    ("replica", "another running copy of the model server"),
    ("agent", "a loop that keeps calling tools until it decides to stop"),
    ("retrieval", "looking up stored text and stuffing it into the prompt"),
    ("toxicity", "how rude or harmful a sentence is scored to be"),
    ("latency", "how long you wait for an answer"),
    ("checkpoint", "a saved set of model weights"),
]


def apply_glossary(steps: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out = []
    for step in steps:
        text = step.get("narration") or ""
        text, seen = gloss_once(text, seen)
        row = dict(step)
        row["narration"] = text
        out.append(row)
    return out


_WORD = re.compile(r"(?<![\w(])({term})(?![\w)])", re.I)


def gloss_once(text: str, seen: set[str]) -> tuple[str, set[str]]:
    for term, gloss in GLOSSARY:
        if term in seen:
            continue
        # only lowercase prose occurrences — skip Title Case / ALL CAPS / existing ()
        pattern = re.compile(rf"(?<![\w(]){re.escape(term)}(?![\w)])")
        m = pattern.search(text)
        if not m:
            continue
        # skip if already inside parentheses nearby
        start = m.start()
        before = text[max(0, start - 1) : start]
        if before == "(":
            continue
        insert = f"{term} ({gloss})"
        text = text[: m.start()] + insert + text[m.end() :]
        seen.add(term)
    return text, seen
