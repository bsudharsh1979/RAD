from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import (
    Concept,
    ConceptEdge,
    DigitalTwin,
    Lesson,
    Misconception,
    Question,
    TwinScenario,
    User,
)
from app.db.session import Base, engine
from app.domains.twins.engine import TWIN_CATALOG
from app.ingestion.engine import ingest_course_materials
from app.seed.concepts import CONCEPTS, EDGES
from app.seed.misconceptions import MISCONCEPTIONS
from app.seed.questions import all_questions


ACTIVE_STEPS = [
    "EXPLAIN",
    "VISUALIZE",
    "PREDICT",
    "EXPERIMENT",
    "OBSERVE",
    "EXPLAIN_BACK",
    "DIAGNOSE",
    "PRACTICE",
    "MASTERY_UPDATE",
]


def init_db_and_seed() -> None:
    Base.metadata.create_all(bind=engine)
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        _seed(db)
        db.commit()
    finally:
        db.close()


def _seed(db: Session) -> None:
    if not db.get(User, settings.demo_learner_id):
        db.add(
            User(
                id=settings.demo_learner_id,
                display_name="Demo learner",
                onboarded=False,
                tutor_provider="demo",
                voice_provider="none",
                research_enabled=False,
            )
        )
        db.flush()

    ingest_course_materials(db)

    if db.query(Concept).count() == 0:
        for c in CONCEPTS:
            db.add(
                Concept(
                    id=c["id"],
                    slug=c["slug"],
                    name=c["name"],
                    cluster=c["cluster"],
                    definition=c["definition"],
                    school=c["school"],
                    engineer=c["engineer"],
                    research=c["research"],
                    notebook_file=c.get("notebook_file"),
                    cell_index=c.get("cell_index"),
                    twin_id=c.get("twin_id"),
                    common_misconceptions=[],
                )
            )
        db.flush()
        for i, (s, d, rel) in enumerate(EDGES):
            db.add(
                ConceptEdge(
                    id=f"e-{i}-{s}-{d}"[:64],
                    src_id=s,
                    dst_id=d,
                    relation=rel,
                )
            )
        db.flush()
        for c in CONCEPTS:
            db.add(
                Lesson(
                    id="les-" + c["id"],
                    concept_id=c["id"],
                    title=c["name"],
                    steps=[{"name": st, "prompt": f"{st} · {c['name']}"} for st in ACTIVE_STEPS],
                )
            )

    if db.query(Misconception).count() == 0:
        for m in MISCONCEPTIONS:
            db.add(
                Misconception(
                    id=m["id"],
                    slug=m["slug"],
                    title=m["title"],
                    left=m["left"],
                    right=m["right"],
                    confusion=m["confusion"],
                    distinction=m["distinction"],
                    source_file=m["source_file"],
                    source_cell=m.get("source_cell"),
                    remediation=m["remediation"],
                )
            )

    if db.query(Question).count() == 0:
        for q in all_questions():
            db.add(
                Question(
                    id=q["id"],
                    qtype=q.get("qtype", "mcq"),
                    bloom=q.get("bloom", "recall"),
                    difficulty=q.get("difficulty", 2),
                    stem=q["stem"],
                    options=q.get("options"),
                    answer=q.get("answer"),
                    explanation=q.get("explanation", ""),
                    concept_id=q.get("concept_id"),
                    misconception_id=q.get("misconception_id"),
                    source_file=q.get("source_file") or "unknown",
                    source_cell=q.get("source_cell"),
                    evidence_type=q.get("evidence_type", "COURSE_SOURCE"),
                    validated=q.get("validated", True),
                    integrity_flags=q.get("integrity_flags") or [],
                )
            )

    if db.query(DigitalTwin).count() == 0:
        for t in TWIN_CATALOG:
            db.add(
                DigitalTwin(
                    id=t["id"],
                    slug=t["id"],
                    name=t["name"],
                    summary=t["summary"],
                    notebook_file=t["notebook_file"],
                    controls=t["controls"],
                )
            )
            db.flush()
            db.add(
                TwinScenario(
                    id="scn-" + t["id"],
                    twin_id=t["id"],
                    name="Default",
                    params={c["key"]: c.get("default") for c in t["controls"]},
                    teaching_point=t["summary"],
                )
            )
