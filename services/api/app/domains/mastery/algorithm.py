"""Explainable mastery: viewing is not mastery."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import MasteryState, ReviewItem
from app.domains.mastery.fsrs import rating_from_attempt, review

WEIGHTS = {
    "viewed": 0.04,
    "recognition": 0.08,
    "recall": 0.16,
    "explain": 0.22,
    "predict": 0.28,
    "diagnose": 0.30,
    "apply": 0.34,
    "design": 0.38,
    "teachback": 0.36,
}


def get_or_create(db: Session, user_id: str, concept_id: str) -> MasteryState:
    row = (
        db.query(MasteryState)
        .filter(MasteryState.user_id == user_id, MasteryState.concept_id == concept_id)
        .one_or_none()
    )
    if row:
        return row
    row = MasteryState(
        id=str(uuid.uuid4()),
        user_id=user_id,
        concept_id=concept_id,
        evidence_log=[],
        misconception_tags=[],
    )
    db.add(row)
    db.flush()
    return row


def apply_event(
    db: Session,
    user_id: str,
    concept_id: str,
    kind: str,
    success: bool,
    *,
    hints: int = 0,
    latency_ms: float = 0,
    quality: float | None = None,
    misconception: str | None = None,
    note: str = "",
) -> MasteryState:
    m = get_or_create(db, user_id, concept_id)
    w = WEIGHTS.get(kind, 0.1)
    delta = w if success else -0.5 * w
    if hints:
        delta -= 0.03 * hints
    m.score = max(0.0, min(1.0, m.score + delta))
    m.attempts += 1
    if success:
        m.correct_attempts += 1
    if kind == "viewed":
        m.viewed += 1
    if kind == "explain" and quality is not None:
        m.explain_quality = 0.7 * m.explain_quality + 0.3 * quality
    if kind == "teachback" and quality is not None:
        m.teachback_quality = 0.6 * m.teachback_quality + 0.4 * quality
    m.hints_used += hints
    m.last_latency_ms = latency_ms
    m.last_reviewed = datetime.utcnow()
    m.confidence = min(1.0, 0.2 + 0.08 * m.attempts + 0.15 * m.score)
    tags = list(m.misconception_tags or [])
    if misconception and misconception not in tags:
        tags.append(misconception)
    if success and misconception and misconception in tags:
        tags = [t for t in tags if t != misconception]
    m.misconception_tags = tags
    rating = rating_from_attempt(success, hints, latency_ms, quality)
    s, d, due = review(m.stability, m.difficulty, rating, m.reps)
    m.stability, m.difficulty, m.next_review = s, d, due
    m.reps += 1
    if rating == 1:
        m.lapses += 1
    log = list(m.evidence_log or [])
    log.append(
        {
            "kind": kind,
            "success": success,
            "delta": round(delta, 4),
            "weight": w,
            "note": note,
            "at": datetime.utcnow().isoformat(),
        }
    )
    m.evidence_log = log[-40:]
    db.add(
        ReviewItem(
            id=str(uuid.uuid4()),
            user_id=user_id,
            concept_id=concept_id,
            due_at=due,
            origin=kind if success else "incorrect",
        )
    )
    db.flush()
    return m


def heatmap(db: Session, user_id: str) -> list[dict[str, Any]]:
    from app.db.models import Concept

    rows = db.query(MasteryState).filter(MasteryState.user_id == user_id).all()
    names = {c.id: c.name for c in db.query(Concept).all()}
    return [
        {
            "concept_id": r.concept_id,
            "name": names.get(r.concept_id, r.concept_id),
            "score": r.score,
            "confidence": r.confidence,
            "next_review": r.next_review.isoformat() if r.next_review else None,
            "misconceptions": r.misconception_tags or [],
        }
        for r in rows
    ]
