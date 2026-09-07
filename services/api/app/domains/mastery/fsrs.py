"""Simplified FSRS-4.5-style scheduler (explainable, no hidden neural net)."""

from __future__ import annotations

from datetime import datetime, timedelta
from math import exp

# Map 1-4 ratings: again, hard, good, easy
W = [0.4, 0.6, 2.4, 5.8, 4.93, 0.94, 0.86, 0.01, 1.49, 0.14, 0.94, 2.18, 0.05, 0.34, 1.26, 0.29, 2.61]


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def review(stability: float, difficulty: float, rating: int, reps: int) -> tuple[float, float, datetime]:
    """rating: 1 again, 2 hard, 3 good, 4 easy."""
    rating = int(_clamp(rating, 1, 4))
    d = _clamp(difficulty - W[6] * (rating - 3), 1.0, 10.0)
    if rating == 1:
        s = W[11] * exp(W[12] * (d - 1)) * ((stability + 1) ** -W[13] - 1) + 0.1
        s = max(0.1, s)
    else:
        s = stability * (1 + exp(W[8]) * (11 - d) * stability ** -W[9] * (exp((1 - 0.9) * W[10]) - 1) * (0.7 + 0.15 * (rating - 3)))
        s = max(stability, s) if rating >= 3 else max(0.1, s * 0.8)
    interval_days = max(1.0, s)
    due = datetime.utcnow() + timedelta(days=interval_days)
    return round(s, 4), round(d, 4), due


def rating_from_attempt(correct: bool, hints: int, latency_ms: float, quality: float | None = None) -> int:
    if not correct:
        return 1
    if hints >= 2 or (latency_ms and latency_ms > 120_000):
        return 2
    if quality is not None and quality >= 0.85 and hints == 0:
        return 4
    return 3
