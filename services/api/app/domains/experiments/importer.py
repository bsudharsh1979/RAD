"""Import real experiment artifacts as ACTUAL_RUN. Never overwrite raw."""

from __future__ import annotations

import csv
import io
import json
import uuid
from typing import Any

from app.db.models import EvidenceType


def parse_import(filename: str, content: str | bytes, kind_hint: str | None = None) -> dict[str, Any]:
    text = content.decode("utf-8", errors="replace") if isinstance(content, bytes) else content
    name = (filename or "").lower()
    kind = kind_hint or _guess(name, text)
    raw: Any
    normalized: dict[str, Any]
    if kind == "json":
        raw = json.loads(text)
        normalized = _from_json(raw)
    elif kind == "csv":
        raw = text
        normalized = _from_csv(text)
    elif kind == "aiperf":
        raw = json.loads(text)
        normalized = _from_aiperf(raw)
    elif kind == "prometheus":
        raw = text
        normalized = _from_prom(text)
    elif kind in ("kubectl", "k8s-events", "logs"):
        raw = text
        normalized = {"kind": kind, "lines": text.splitlines()[:500], "note": "Parsed as text log/events; not executed."}
    elif kind == "otel":
        try:
            raw = json.loads(text)
        except json.JSONDecodeError:
            raw = text
        normalized = {"kind": "otel", "spans": raw if isinstance(raw, (dict, list)) else {"text": text[:5000]}}
    else:
        raw = text
        normalized = {"kind": "opaque", "preview": text[:4000]}
    return {
        "source_format": kind,
        "raw": raw,
        "normalized": normalized,
        "evidence_type": EvidenceType.ACTUAL_RUN.value,
    }


def _guess(name: str, text: str) -> str:
    if "aiperf" in name:
        return "aiperf"
    if name.endswith(".csv"):
        return "csv"
    if name.endswith(".json"):
        if "resourceSpans" in text or "otel" in name:
            return "otel"
        return "json"
    if "# TYPE" in text or name.endswith(".prom"):
        return "prometheus"
    if "kubectl" in name or "Events:" in text[:200]:
        return "kubectl"
    return "logs"


def _from_json(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        metrics = {k: v for k, v in raw.items() if isinstance(v, (int, float, str))}
        return {"kind": "json", "metrics": metrics, "keys": list(raw)[:50]}
    if isinstance(raw, list):
        return {"kind": "json-list", "n": len(raw), "head": raw[:3]}
    return {"kind": "json", "value": raw}


def _from_csv(text: str) -> dict[str, Any]:
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    return {"kind": "csv", "n": len(rows), "columns": reader.fieldnames, "head": rows[:5]}


def _from_aiperf(raw: Any) -> dict[str, Any]:
    blob = raw if isinstance(raw, dict) else {"value": raw}
    metrics = {}
    for key in ("ttft", "tpot", "throughput", "latency", "tokens_per_sec", "isl", "osl", "concurrency"):
        if key in blob:
            metrics[key] = blob[key]
    # nested
    for nest in ("metrics", "summary", "results"):
        if isinstance(blob.get(nest), dict):
            metrics.update({k: v for k, v in blob[nest].items() if isinstance(v, (int, float))})
    return {"kind": "aiperf", "metrics": metrics, "model": blob.get("model"), "engine": blob.get("engine")}


def _from_prom(text: str) -> dict[str, Any]:
    samples = []
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            try:
                samples.append({"metric": parts[0], "value": float(parts[-1])})
            except ValueError:
                continue
    return {"kind": "prometheus", "n": len(samples), "samples": samples[:200]}


def compare_runs(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    """Detect confounded experiments; never claim causality."""
    meta_keys = ["model", "precision", "gpu_type", "gpu_count", "engine", "isl", "osl", "concurrency", "request_rate", "warmup", "cache_state", "worker_count"]
    confounds = []
    ma, mb = a.get("metadata") or {}, b.get("metadata") or {}
    for k in meta_keys:
        va, vb = ma.get(k), mb.get(k)
        if va is not None and vb is not None and va != vb:
            confounds.append({"field": k, "a": va, "b": vb})
    na, nb = a.get("normalized") or {}, b.get("normalized") or {}
    mets_a = na.get("metrics") or {}
    mets_b = nb.get("metrics") or {}
    deltas = {}
    for k in set(mets_a) & set(mets_b):
        try:
            deltas[k] = {"a": mets_a[k], "b": mets_b[k], "diff": float(mets_b[k]) - float(mets_a[k])}
        except (TypeError, ValueError):
            continue
    gpus_a = ma.get("gpu_count") or 1
    gpus_b = mb.get("gpu_count") or 1
    norm = {}
    for label, mets, g in (("a", mets_a, gpus_a), ("b", mets_b, gpus_b)):
        tps = mets.get("tokens_per_sec") or mets.get("throughput")
        rps = mets.get("requests_per_sec")
        try:
            if tps is not None and g:
                norm[f"{label}_tokens_per_sec_per_gpu"] = float(tps) / float(g)
            if rps is not None and g:
                norm[f"{label}_requests_per_sec_per_gpu"] = float(rps) / float(g)
        except (TypeError, ValueError):
            pass
    return {
        "confounds": confounds,
        "deltas": deltas,
        "normalized_metrics": norm,
        "causality": "Correlation only. Confounders listed. Not proven cause.",
        "evidence_type": EvidenceType.TUTOR_INTERPRETATION.value,
    }


def explain_experiment(normalized: dict[str, Any], course_hits: list[dict]) -> dict[str, Any]:
    return {
        "what_happened": {"facts": normalized, "evidence_type": EvidenceType.ACTUAL_RUN.value},
        "important_changes": "See comparison workbench for quantitative diffs.",
        "likely_explanations": [
            "Workload, precision, or cache state may differ — check metadata.",
        ],
        "alternative_explanations": [
            "Cold vs warm start",
            "Different GPU counts",
            "Different ISL/OSL",
            "Measurement scrape gaps",
        ],
        "what_to_check_next": [
            "Confirm identical prompts and concurrency",
            "Import the matching notebook cell as EXPECTED_RESULT only",
        ],
        "course_connection": course_hits,
        "evidence_type": EvidenceType.TUTOR_INTERPRETATION.value,
    }


def new_id() -> str:
    return str(uuid.uuid4())
