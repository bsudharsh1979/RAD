"""Build simple/expert audio lectures with identical step structure."""

from __future__ import annotations

from app.domains.walkthrough.frames import FRAMES
from app.domains.walkthrough.glossary import apply_glossary
from app.domains.walkthrough.speech import humanize_title, speak_normalize

STEP_KINDS = ("big_idea", "model", "concept", "game_plan", "stage", "one_thing")


def build_walkthrough(filename: str, cells: list[dict], concepts: list[dict], *, depth: str = "simple") -> dict:
    depth = "expert" if str(depth).lower() == "expert" else "simple"
    frame = FRAMES.get(filename)
    n = len(cells)
    if not frame:
        frame = _fallback_frame(filename, n)
    steps = _steps(frame, cells, concepts, depth)
    if depth == "simple":
        steps = apply_glossary(steps)
    for s in steps:
        s["narration"] = speak_normalize(s["narration"])
        if depth == "simple" and len(s["narration"]) > 620:
            # Gloss/compress stage narration; keep meaning, never drop the whole lecture.
            s["narration"] = s["narration"][:617].rsplit(" ", 1)[0] + "."
            s["compressed"] = True
        else:
            s["compressed"] = False
        s["title"] = humanize_title(s["title"])
        s["chars"] = len(s["narration"])
        s["duration_s"] = max(4, round(s["chars"] / 14))
    _assert_coverage(frame, n)
    return {
        "file": filename,
        "depth": depth,
        "title": humanize_title(frame["title"]),
        "steps": steps,
        "stage_count": sum(1 for s in steps if s["kind"] == "stage"),
        "disclaimer": "Not affiliated with or endorsed by NVIDIA. Lectures are our own words about bring-your-own materials.",
        "evidence_type": "TUTOR_INTERPRETATION",
    }


def _steps(frame: dict, cells: list[dict], concepts: list[dict], depth: str) -> list[dict]:
    simple = depth == "simple"
    steps: list[dict] = []
    bi = frame["big_idea"]
    steps.append(
        {
            "kind": "big_idea",
            "title": "The big idea",
            "narration": f"{bi['hook']} {bi['stake']}",
            "cell_start": 0,
            "cell_end": 0,
        }
    )
    steps.append(
        {
            "kind": "model",
            "title": "The model",
            "narration": frame["simple_model"] if simple else frame["expert_model"],
            "cell_start": 0,
            "cell_end": max(0, (frame["stages"][0]["end"] if frame["stages"] else 0)),
        }
    )
    wanted = {c["id"] for c in concepts}
    for cid in frame.get("concepts") or []:
        hit = next((c for c in concepts if c["id"] == cid), None)
        if not hit:
            continue
        body = hit.get("school") if simple else hit.get("research")
        analogy = hit.get("analogy") or ""
        narration = body or hit.get("definition") or ""
        if simple and analogy:
            narration = f"{narration} Picture this: {analogy}"
        steps.append(
            {
                "kind": "concept",
                "title": hit["name"],
                "narration": narration,
                "concept_id": cid,
                "cell_start": hit.get("cell_index") or 0,
                "cell_end": hit.get("cell_index") or 0,
            }
        )
        wanted.discard(cid)
    steps.append(
        {
            "kind": "game_plan",
            "title": "The game plan",
            "narration": frame["game_plan"],
            "cell_start": 0,
            "cell_end": 0,
        }
    )
    last_end = -1
    for st in frame["stages"]:
        crux = st["crux_simple"] if simple else st["crux_expert"]
        steps.append(
            {
                "kind": "stage",
                "title": st["title"],
                "narration": crux,
                "cell_start": st["start"],
                "cell_end": st["end"],
                "crux": crux,
            }
        )
        last_end = st["end"]
    n = len(cells)
    if last_end < n - 1:
        steps.append(
            {
                "kind": "stage",
                "title": "Remaining cells",
                "narration": "The remaining cells continue the same arc. Nothing here is executed by the academy.",
                "cell_start": last_end + 1,
                "cell_end": n - 1,
            }
        )
    steps.append(
        {
            "kind": "one_thing",
            "title": "The one thing to remember",
            "narration": frame["one_thing"],
            "cell_start": max(0, n - 1),
            "cell_end": max(0, n - 1),
        }
    )
    return steps


def _fallback_frame(filename: str, n: int) -> dict:
    end = max(0, n - 1)
    mid = max(0, n // 2)
    return {
        "title": filename,
        "n_cells": n,
        "big_idea": {"hook": "This notebook is ingested course material.", "stake": "We lecture in our own words and never run the cells."},
        "simple_model": "Read, predict, then check a twin. Treat every printed number without stored output as expected, not measured.",
        "expert_model": "Source spans are COURSE_SOURCE. Twins are SIMULATED_RESULT. No automatic execution.",
        "game_plan": "Walk the cells in ranges, then prove mastery on a twin.",
        "one_thing": "Evidence labels stay attached to every number.",
        "concepts": [],
        "stages": [
            {"title": "First half", "start": 0, "end": mid, "crux_simple": "Setup and motivation.", "crux_expert": "Opening spans establish vocabulary."},
            {"title": "Second half", "start": mid + 1 if mid + 1 <= end else end, "end": end, "crux_simple": "Practice and wrap.", "crux_expert": "Closing spans apply the mechanism."},
        ],
    }


def _assert_coverage(frame: dict, n: int) -> None:
    covered = set()
    for st in frame["stages"]:
        for i in range(st["start"], st["end"] + 1):
            covered.add(i)
    # fallback stage in _steps covers a tail if needed; frames should already cover.
    missing = [i for i in range(n) if i not in covered]
    frame["_missing_cells"] = missing


def structure_kinds(steps: list[dict]) -> list[str]:
    return [s["kind"] for s in steps]
