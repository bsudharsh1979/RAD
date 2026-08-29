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


def _ensure_columns() -> None:
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    tables = set(insp.get_table_names())
    alters: list[tuple[str, str, str]] = [
        ("concepts", "analogy", "ALTER TABLE concepts ADD COLUMN analogy TEXT DEFAULT ''"),
        ("notebook_cells", "business_impact", "ALTER TABLE notebook_cells ADD COLUMN business_impact TEXT DEFAULT ''"),
    ]
    with engine.begin() as conn:
        for table, col, sql in alters:
            if table not in tables:
                continue
            cols = {c["name"] for c in inspect(engine).get_columns(table)}
            if col not in cols:
                conn.execute(text(sql))


def init_db_and_seed() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_columns()
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

    existing_concepts = {c.id for c in db.query(Concept).all()}
    for c in CONCEPTS:
        if c["id"] in existing_concepts:
            row = db.get(Concept, c["id"])
            if row and not (row.analogy or "").strip():
                row.analogy = c.get("analogy") or (
                    c["school"].split(".")[0] + " — like a labeled drawer in a filing cabinet."
                )
            continue
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
                analogy=c.get("analogy")
                or (c["school"].split(".")[0] + " — like a labeled drawer in a filing cabinet."),
                notebook_file=c.get("notebook_file"),
                cell_index=c.get("cell_index"),
                twin_id=c.get("twin_id"),
                common_misconceptions=[],
            )
        )
        db.add(
            Lesson(
                id="les-" + c["id"],
                concept_id=c["id"],
                title=c["name"],
                steps=[{"name": st, "prompt": f"{st} · {c['name']}"} for st in ACTIVE_STEPS],
            )
        )
    db.flush()
    have_edges = {e.id for e in db.query(ConceptEdge).all()}
    for i, (s, d, rel) in enumerate(EDGES):
        eid = f"e-{i}-{s}-{d}"[:64]
        if eid in have_edges:
            continue
        if not db.get(Concept, s) or not db.get(Concept, d):
            continue
        db.add(ConceptEdge(id=eid, src_id=s, dst_id=d, relation=rel))
    db.flush()

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

    if db.query(Question).count() < 500:
        have_q = {q.id for q in db.query(Question).all()}
        for q in all_questions():
            if q["id"] in have_q:
                continue
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

    have_twins = {t.id for t in db.query(DigitalTwin).all()}
    for t in TWIN_CATALOG:
        if t["id"] not in have_twins:
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
        suggestions = t.get("suggested") or [
            {"name": "Default", "params": {c["key"]: c.get("default") for c in t["controls"]}}
        ]
        for i, scn in enumerate(suggestions[:4]):
            sid = f"scn-{t['id']}-{i}"
            if db.get(TwinScenario, sid):
                continue
            db.add(
                TwinScenario(
                    id=sid,
                    twin_id=t["id"],
                    name=scn.get("name") or f"Scenario {i+1}",
                    params=scn.get("params") or {},
                    teaching_point=t["summary"],
                )
            )
