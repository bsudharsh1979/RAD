from __future__ import annotations

import hashlib
import random
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import (
    Bookmark,
    BenchmarkRun,
    Concept,
    ConceptEdge,
    DigitalTwin,
    EvidenceArtifact,
    Experiment,
    IntegrityFlag,
    LearnerNote,
    LearnerPrediction,
    Lesson,
    MasteryState,
    Misconception,
    Notebook,
    NotebookCell,
    ProviderTrace,
    Question,
    QuestionAttempt,
    ReviewItem,
    SourceArtifact,
    SourceSpan,
    TwinRun,
    User,
)
from app.db.session import get_db
from app.domains.experiments.importer import compare_runs, explain_experiment, parse_import
from app.domains.mastery.algorithm import apply_event, heatmap
from app.domains.providers.registry import PROVIDERS, VOICE, PerplexityResearchProvider
from app.domains.retrieval.search import hybrid_search
from app.domains.tutor.service import tutor_turn
from app.domains.twins.engine import TWIN_CATALOG, run as run_twin
from app.ingestion.safety import inspect_code
from app.security.guards import (
    ALLOWED_IMPORT_SUFFIX,
    ensure_upload_size,
    rate_limit_ok,
    sanitize_filename,
)

router = APIRouter()
_hits: dict[str, list[float]] = {}


def learner(db: Session = Depends(get_db)) -> User:
    u = db.get(User, settings.demo_learner_id)
    if not u:
        raise HTTPException(500, "Demo learner missing")
    return u


class OnboardIn(BaseModel):
    display_name: str = "Learner"
    tutor_provider: str = "demo"
    voice_provider: str = "none"
    research_enabled: bool = False
    explanation_depth: str = "ENGINEER"
    tutor_mode: str = "COURSE"


class TutorIn(BaseModel):
    content: str
    session_id: str | None = None
    mode: str | None = None
    depth: str | None = None


class AttemptIn(BaseModel):
    question_id: str
    given: Any
    hints_used: int = 0
    latency_ms: float = 0


class TwinIn(BaseModel):
    scenario: str
    params: dict[str, Any] = Field(default_factory=dict)
    prediction_id: str | None = None


class PredictIn(BaseModel):
    twin_id: str
    prompt: str
    predicted: dict[str, Any]


class TeachbackIn(BaseModel):
    concept_id: str
    transcript: str


class NoteIn(BaseModel):
    target_type: str
    target_id: str
    body: str


class BookmarkIn(BaseModel):
    target_type: str
    target_id: str
    label: str = "Review later"


class SettingsIn(BaseModel):
    tutor_provider: str | None = None
    voice_provider: str | None = None
    research_enabled: bool | None = None
    explanation_depth: str | None = None
    tutor_mode: str | None = None
    display_name: str | None = None


@router.get("/health")
def health():
    return {"ok": True, "app": settings.app_name}


@router.get("/meta")
def meta():
    return {
        "app": settings.app_name,
        "course": settings.course_title,
        "nav": [
            "home",
            "learn",
            "tutor",
            "concepts",
            "notebooks",
            "twins",
            "experiments",
            "practice",
            "review",
            "assessment",
            "progress",
            "sources",
            "settings",
        ],
    }


@router.get("/providers")
def providers():
    px = PerplexityResearchProvider()
    status = {name: ("connected" if p.available() else "not_configured") for name, p in PROVIDERS.items()}
    status.update({f"voice_{n}": ("connected" if v.available() else "not_configured") for n, v in VOICE.items()})
    status["perplexity"] = "connected" if px.available() else "not_configured"
    status["omniverse"] = "connected" if settings.omniverse_bridge_url else "offline"
    status["langfuse"] = "connected" if settings.langfuse_public_key else "not_configured"
    return {
        "status": status,
        "ask": "Which APIs do you want? Demo works offline. OpenAI, NVIDIA NIM, HuggingFace, ElevenLabs, Sarvam, Perplexity are optional.",
        "choices": {
            "tutor": ["demo", "openai", "nvidia_nim", "huggingface"],
            "voice": ["none", "elevenlabs", "sarvam", "openai_realtime"],
            "research": ["off", "perplexity"],
        },
    }


@router.post("/onboard")
def onboard(body: OnboardIn, user: User = Depends(learner), db: Session = Depends(get_db)):
    if body.tutor_provider not in PROVIDERS:
        raise HTTPException(400, "Unknown tutor provider")
    user.display_name = body.display_name
    user.tutor_provider = body.tutor_provider
    user.voice_provider = body.voice_provider
    user.research_enabled = body.research_enabled
    user.explanation_depth = body.explanation_depth
    user.tutor_mode = body.tutor_mode
    user.onboarded = True
    db.commit()
    return {"ok": True, "user": _user(user)}


@router.get("/me")
def me(user: User = Depends(learner)):
    return _user(user)


@router.patch("/me")
def patch_me(body: SettingsIn, user: User = Depends(learner), db: Session = Depends(get_db)):
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(user, k, v)
    db.commit()
    return _user(user)


def _user(user: User) -> dict:
    return {
        "id": user.id,
        "display_name": user.display_name,
        "onboarded": user.onboarded,
        "tutor_provider": user.tutor_provider,
        "voice_provider": user.voice_provider,
        "research_enabled": user.research_enabled,
        "explanation_depth": user.explanation_depth,
        "tutor_mode": user.tutor_mode,
        "last_resume": user.last_resume_json,
    }


@router.get("/home")
def home(user: User = Depends(learner), db: Session = Depends(get_db)):
    states = db.query(MasteryState).filter(MasteryState.user_id == user.id).all()
    concepts = {c.id: c for c in db.query(Concept).all()}
    due = (
        db.query(ReviewItem)
        .filter(ReviewItem.user_id == user.id, ReviewItem.due_at <= datetime.utcnow())
        .count()
    )
    scored = sorted(states, key=lambda s: s.score)
    weak = [{"id": s.concept_id, "name": concepts.get(s.concept_id).name if concepts.get(s.concept_id) else s.concept_id, "score": s.score} for s in scored[:5]]
    strong = [{"id": s.concept_id, "name": concepts.get(s.concept_id).name if concepts.get(s.concept_id) else s.concept_id, "score": s.score} for s in scored[-5:][::-1]]
    mis = sum(len(s.misconception_tags or []) for s in states)
    avg = sum(s.score for s in states) / len(states) if states else 0.0
    plan = _thirty(db, user, weak)
    resume = user.last_resume_json or {
        "text": "You have not started a lesson yet. Take the diagnostic or open notebook 1.",
        "action": "/learn",
    }
    return {
        "what_i_know": round(avg, 3),
        "forgetting": due,
        "next": plan,
        "blocking_misconceptions": mis,
        "notebook_revisit": weak[0]["name"] if weak else "01_llm_intro.ipynb",
        "twin": (weak[0] and concepts.get(weak[0]["id"]).twin_id) if weak and concepts.get(weak[0]["id"]) else "pipeline-flow",
        "heatmap": heatmap(db, user.id),
        "progress": avg,
        "reviews_due": due,
        "strongest": strong,
        "weakest": weak,
        "misconception_count": mis,
        "assessment_readiness": round(min(1.0, avg * 0.9 + (0.1 if mis == 0 else 0)), 3),
        "resume": resume,
        "thirty_minute_plan": plan,
    }


def _thirty(db, user, weak) -> list[dict]:
    if not user.onboarded:
        return [{"title": "Choose APIs / start demo", "href": "/settings", "minutes": 5}]
    if db.query(QuestionAttempt).filter(QuestionAttempt.user_id == user.id).count() == 0:
        return [{"title": "Take the adaptive diagnostic", "href": "/practice?mode=diagnostic", "minutes": 12}]
    items = [{"title": "Reviews due", "href": "/review", "minutes": 8}]
    if weak:
        items.append({"title": f"Lesson: {weak[0]['name']}", "href": f"/learn?concept={weak[0]['id']}", "minutes": 12})
        c = db.get(Concept, weak[0]["id"])
        if c and c.twin_id:
            items.append({"title": f"Twin: {c.twin_id}", "href": f"/twins/{c.twin_id}", "minutes": 10})
    items.append({"title": "Notebook studio", "href": "/notebooks", "minutes": 10})
    return items[:4]


@router.get("/concepts")
def concepts(db: Session = Depends(get_db)):
    nodes = db.query(Concept).all()
    edges = db.query(ConceptEdge).all()
    return {
        "nodes": [
            {
                "id": n.id,
                "slug": n.slug,
                "name": n.name,
                "cluster": n.cluster,
                "definition": n.definition,
                "school": n.school,
                "engineer": n.engineer,
                "research": n.research,
                "notebook_file": n.notebook_file,
                "cell_index": n.cell_index,
                "twin_id": n.twin_id,
            }
            for n in nodes
        ],
        "edges": [{"id": e.id, "source": e.src_id, "target": e.dst_id, "relation": e.relation} for e in edges],
    }


@router.get("/concepts/{cid}")
def concept_one(cid: str, user: User = Depends(learner), db: Session = Depends(get_db)):
    c = db.get(Concept, cid) or db.query(Concept).filter(Concept.slug == cid).one_or_none()
    if not c:
        raise HTTPException(404)
    apply_event(db, user.id, c.id, "viewed", True, note="opened concept")
    db.commit()
    m = (
        db.query(MasteryState)
        .filter(MasteryState.user_id == user.id, MasteryState.concept_id == c.id)
        .one_or_none()
    )
    lesson = db.query(Lesson).filter(Lesson.concept_id == c.id).one_or_none()
    return {
        "concept": {
            "id": c.id,
            "name": c.name,
            "slug": c.slug,
            "definition": c.definition,
            "school": c.school,
            "engineer": c.engineer,
            "research": c.research,
            "notebook_file": c.notebook_file,
            "cell_index": c.cell_index,
            "twin_id": c.twin_id,
        },
        "mastery": m.score if m else 0,
        "lesson": lesson.steps if lesson else [],
        "prerequisites": [
            e.src_id
            for e in db.query(ConceptEdge).filter(ConceptEdge.dst_id == c.id, ConceptEdge.relation == "PREREQUISITE_OF")
        ],
        "related": [
            {"id": e.dst_id, "relation": e.relation}
            for e in db.query(ConceptEdge).filter(ConceptEdge.src_id == c.id)
        ],
    }


@router.get("/notebooks")
def notebooks(db: Session = Depends(get_db)):
    nbs = db.query(Notebook).order_by(Notebook.order_index).all()
    return [
        {
            "id": n.id,
            "filename": n.filename,
            "title": n.title,
            "order": n.order_index,
            "purpose": n.purpose,
            "why_it_matters": n.why_it_matters,
            "expected_outcome": n.expected_outcome,
            "n_cells": db.query(NotebookCell).filter(NotebookCell.notebook_id == n.id).count(),
        }
        for n in nbs
    ]


@router.get("/notebooks/{nid}")
def notebook_one(nid: str, db: Session = Depends(get_db)):
    n = db.get(Notebook, nid)
    if not n:
        n = db.query(Notebook).filter(Notebook.filename == nid).one_or_none()
    if not n:
        raise HTTPException(404)
    cells = (
        db.query(NotebookCell)
        .filter(NotebookCell.notebook_id == n.id)
        .order_by(NotebookCell.cell_index)
        .all()
    )
    flow = [cl.cell_index for cl in cells if cl.cell_type == "markdown" and cl.source.strip().startswith("#")]
    return {
        "id": n.id,
        "filename": n.filename,
        "title": n.title,
        "purpose": n.purpose,
        "why_it_matters": n.why_it_matters,
        "expected_outcome": n.expected_outcome,
        "flow": flow,
        "cells": [_cell(c) for c in cells],
    }


def _cell(c: NotebookCell) -> dict:
    return {
        "id": c.id,
        "cell_index": c.cell_index,
        "cell_type": c.cell_type,
        "source": c.source,
        "stored_output": c.stored_output,
        "output_class": "stored_actual" if c.stored_output else "none",
        "execution_count": c.execution_count,
        "blocked_execution": c.blocked_execution,
        "safety_flags": c.safety_flags or inspect_code(c.source if c.cell_type == "code" else ""),
        "tabs": {
            "CODE": c.source if c.cell_type == "code" else c.source,
            "PLAIN_ENGLISH": c.plain_english,
            "LINE_BY_LINE": c.line_by_line,
            "WHY_THIS_EXISTS": c.why_exists,
            "WHAT_SHOULD_HAPPEN": c.what_should_happen,
            "HOW_TO_VERIFY": c.how_to_verify,
            "COMMON_FAILURE": c.common_failure,
            "TRY_MODIFYING": c.try_modifying,
        },
        "span_id": c.span_id,
        "evidence_type": "COURSE_SOURCE",
    }


@router.get("/sources")
def sources(db: Session = Depends(get_db)):
    arts = db.query(SourceArtifact).order_by(SourceArtifact.order_index).all()
    return [
        {
            "id": a.id,
            "type": a.source_type,
            "file": a.filename,
            "title": a.title,
            "order": a.order_index,
            "sha256": a.sha256,
        }
        for a in arts
    ]


@router.get("/sources/{sid}")
def source_one(sid: str, db: Session = Depends(get_db)):
    a = db.get(SourceArtifact, sid)
    if not a:
        a = db.query(SourceArtifact).filter(SourceArtifact.filename == sid).one_or_none()
    if not a:
        raise HTTPException(404)
    spans = db.query(SourceSpan).filter(SourceSpan.artifact_id == a.id).all()
    return {
        "artifact": {"id": a.id, "file": a.filename, "type": a.source_type, "title": a.title},
        "spans": [
            {
                "id": s.id,
                "cell_index": s.cell_index,
                "page": s.page,
                "heading": s.heading,
                "cell_type": s.cell_type,
                "excerpt": (s.body or s.code or "")[:500],
                "evidence_type": s.evidence_type,
            }
            for s in spans
        ],
    }


@router.get("/search")
def search(q: str, db: Session = Depends(get_db)):
    return hybrid_search(db, q, limit=12)


@router.post("/tutor")
async def tutor(body: TutorIn, request: Request, user: User = Depends(learner), db: Session = Depends(get_db)):
    await rate_limit_ok(request, _hits, 40)
    return tutor_turn(db, user, body.session_id, body.content, mode=body.mode, depth=body.depth)


@router.get("/twins")
def twins():
    return TWIN_CATALOG


@router.post("/twins/run")
def twins_run(body: TwinIn, user: User = Depends(learner), db: Session = Depends(get_db)):
    try:
        state = run_twin(body.scenario, body.params)
    except KeyError as e:
        raise HTTPException(404, str(e)) from e
    rid = str(uuid.uuid4())
    db.add(
        TwinRun(
            id=rid,
            user_id=user.id,
            twin_id=body.scenario,
            params=body.params,
            state=state,
            evidence_type=state.get("evidence_type", "SIMULATED_RESULT"),
        )
    )
    if body.prediction_id:
        pred = db.get(LearnerPrediction, body.prediction_id)
        if pred:
            pred.observed = state
            pred.revealed = True
    user.last_resume_json = {
        "text": f"Last time you were running the {body.scenario} twin.",
        "action": f"/twins/{body.scenario}",
        "twin": body.scenario,
    }
    db.commit()
    return {"run_id": rid, "state": state}


@router.post("/twins/predict")
def twins_predict(body: PredictIn, user: User = Depends(learner), db: Session = Depends(get_db)):
    pid = str(uuid.uuid4())
    db.add(
        LearnerPrediction(
            id=pid,
            user_id=user.id,
            twin_id=body.twin_id,
            prompt=body.prompt,
            predicted=body.predicted,
            revealed=False,
        )
    )
    db.commit()
    return {"prediction_id": pid, "locked": True}


@router.get("/lessons/{concept_id}")
def lesson(concept_id: str, db: Session = Depends(get_db)):
    les = db.query(Lesson).filter(Lesson.concept_id == concept_id).one_or_none()
    if not les:
        raise HTTPException(404)
    return {"id": les.id, "title": les.title, "steps": les.steps, "hide_outcome_until_predict": True}


DIAGNOSTIC_CONCEPTS = [
    "c-pipeline",
    "c-token",
    "c-attention",
    "c-mlm",
    "c-qa-span",
    "c-zeroshot",
    "c-t5",
    "c-cross-attn",
    "c-flan",
    "c-whisper",
    "c-clip",
    "c-decoder-only",
    "c-quant",
    "c-llama2",
    "c-memory",
    "c-rag",
    "c-agent",
    "c-assess",
]


@router.get("/diagnostic")
def diagnostic(difficulty: int = 2, db: Session = Depends(get_db)):
    qs = (
        db.query(Question)
        .filter(Question.concept_id.in_(DIAGNOSTIC_CONCEPTS), Question.qtype == "mcq")
        .all()
    )
    by_c: dict[str, list] = {}
    for q in qs:
        by_c.setdefault(q.concept_id, []).append(q)
    picked = []
    for cid in DIAGNOSTIC_CONCEPTS:
        pool = [q for q in by_c.get(cid, []) if abs(q.difficulty - difficulty) <= 2]
        if pool:
            picked.append(random.choice(pool))
    return {"questions": [_public_q(q) for q in picked], "adaptive": True}


def _public_q(q: Question) -> dict:
    return {
        "id": q.id,
        "qtype": q.qtype,
        "bloom": q.bloom,
        "difficulty": q.difficulty,
        "stem": q.stem,
        "options": q.options,
        "concept_id": q.concept_id,
        "source": {"file": q.source_file, "cell_index": q.source_cell},
        "evidence_type": q.evidence_type,
    }


@router.get("/questions")
def questions(
    qtype: str | None = None,
    concept_id: str | None = None,
    bloom: str | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    q = db.query(Question)
    if qtype:
        q = q.filter(Question.qtype == qtype)
    if concept_id:
        q = q.filter(Question.concept_id == concept_id)
    if bloom:
        q = q.filter(Question.bloom == bloom)
    rows = q.limit(min(limit, 80)).all()
    return [_public_q(r) for r in rows]


@router.post("/questions/attempt")
def attempt(body: AttemptIn, user: User = Depends(learner), db: Session = Depends(get_db)):
    q = db.get(Question, body.question_id)
    if not q:
        raise HTTPException(404)
    prior = (
        db.query(QuestionAttempt)
        .filter(QuestionAttempt.user_id == user.id, QuestionAttempt.question_id == q.id)
        .count()
    )
    correct, feedback = grade(q, body.given)
    if not correct and prior >= 1:
        feedback["socratic"] = False
        feedback["try_again"] = False
        feedback["canonical_answer"] = q.answer
        feedback["simple_correction"] = q.explanation
        feedback["missing_distinction"] = q.explanation
    aid = str(uuid.uuid4())
    db.add(
        QuestionAttempt(
            id=aid,
            user_id=user.id,
            question_id=q.id,
            given=body.given,
            correct=correct,
            hints_used=body.hints_used,
            latency_ms=body.latency_ms,
            feedback=feedback,
        )
    )
    kind = {
        "recall": "recall",
        "explain": "explain",
        "predict": "predict",
        "diagnose": "diagnose",
        "apply": "apply",
        "design": "design",
        "defend": "design",
        "code": "apply",
        "compare": "explain",
        "architecture": "design",
    }.get(q.bloom, "recognition")
    if q.concept_id:
        apply_event(
            db,
            user.id,
            q.concept_id,
            kind,
            correct,
            hints=body.hints_used,
            latency_ms=body.latency_ms,
            misconception=q.misconception_id,
        )
    db.commit()
    return {"attempt_id": aid, "correct": correct, "feedback": feedback, "reveal": False if not correct else True}


def grade(q: Question, given: Any) -> tuple[bool, dict]:
    ans = q.answer
    correct = False
    if q.qtype in ("mcq",) or q.options:
        correct = _norm(given) == _norm(ans)
    elif isinstance(ans, str) and isinstance(given, str):
        g, a = _norm(given), _norm(ans)
        correct = a[:40] in g or g in a or _token_overlap(g, a) > 0.45
    else:
        correct = _norm(given) == _norm(ans)
    why = None
    if not correct and q.misconception_id:
        why = q.misconception_id
    feedback = {
        "your_answer": given,
        "what_this_suggests": _suggest(q, given, correct),
        "missing_distinction": q.explanation,
        "source_evidence": {"file": q.source_file, "cell_index": q.source_cell, "evidence_type": q.evidence_type},
        "simple_correction": q.explanation,
        "try_again": not correct,
        "canonical_answer": ans if correct or q.qtype == "mcq" else None,
        "socratic": (not correct),
    }
    if not correct:
        feedback["canonical_answer"] = None  # socratic: don't dump immediately for free response
        if q.qtype == "mcq":
            feedback["hint"] = "Re-read the source cell before a second try."
    else:
        feedback["canonical_answer"] = ans
    return correct, feedback


def _norm(x: Any) -> str:
    return str(x or "").strip().lower()


def _token_overlap(a: str, b: str) -> float:
    sa, sb = set(a.split()), set(b.split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _suggest(q: Question, given: Any, correct: bool) -> str:
    if correct:
        return "Your answer matches the sourced distinction."
    if q.misconception_id:
        return f"This pattern is stored as misconception {q.misconception_id}."
    return "A key course distinction is missing. Check the cited cell."


@router.get("/review")
def review(user: User = Depends(learner), db: Session = Depends(get_db)):
    items = (
        db.query(ReviewItem)
        .filter(ReviewItem.user_id == user.id, ReviewItem.due_at <= datetime.utcnow())
        .limit(20)
        .all()
    )
    qs = []
    for it in items:
        q = None
        if it.question_id:
            q = db.get(Question, it.question_id)
        elif it.concept_id:
            q = (
                db.query(Question)
                .filter(Question.concept_id == it.concept_id, Question.qtype == "mcq")
                .first()
            )
        if q:
            qs.append(_public_q(q))
    return {"due": len(items), "questions": qs}


@router.post("/teachback")
def teachback(body: TeachbackIn, user: User = Depends(learner), db: Session = Depends(get_db)):
    c = db.get(Concept, body.concept_id)
    if not c:
        raise HTTPException(404)
    blob = " ".join([c.definition, c.engineer, c.research]).lower()
    required = [w for w in _keywords(c.engineer + " " + c.definition) if len(w) > 4][:8]
    said = set(_keywords(body.transcript))
    missing = [w for w in required if w not in said]
    confused = []
    for m in db.query(Misconception).all():
        if m.left.lower() in body.transcript.lower() and m.right.lower() in body.transcript.lower():
            if m.distinction.lower().split()[0] not in body.transcript.lower():
                confused.append(m.title)
    quality = max(0.0, 1.0 - 0.12 * len(missing) - 0.08 * len(confused))
    apply_event(db, user.id, c.id, "teachback", quality >= 0.55, quality=quality, note="teachback")
    db.commit()
    return {
        "correctly_explained": [w for w in required if w in said],
        "partially_explained": [],
        "missing": missing,
        "confused_concepts": confused[:5],
        "suggested": c.engineer,
        "quality": round(quality, 3),
        "evidence_type": "TUTOR_INTERPRETATION",
    }


def _keywords(text: str) -> list[str]:
    return [w.strip(".,;:()").lower() for w in text.replace("/", " ").split() if w]


@router.get("/misconceptions")
def misconceptions(db: Session = Depends(get_db)):
    return [
        {
            "id": m.id,
            "title": m.title,
            "left": m.left,
            "right": m.right,
            "confusion": m.confusion,
            "distinction": m.distinction,
            "source_file": m.source_file,
            "source_cell": m.source_cell,
        }
        for m in db.query(Misconception).all()
    ]


@router.post("/experiments/import")
async def exp_import(
    user: User = Depends(learner),
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    kind: str | None = None,
):
    data = await file.read()
    ensure_upload_size(len(data))
    fname = sanitize_filename(file.filename or "upload.json")
    suf = "." + fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
    if suf and suf not in ALLOWED_IMPORT_SUFFIX:
        raise HTTPException(400, f"Unsupported type {suf}")
    parsed = parse_import(fname, data, kind)
    eid = str(uuid.uuid4())
    bid = str(uuid.uuid4())
    db.add(Experiment(id=eid, user_id=user.id, name=fname, kind=parsed["source_format"], metadata_json={"filename": fname}))
    db.flush()
    db.add(
        BenchmarkRun(
            id=bid,
            experiment_id=eid,
            source_format=parsed["source_format"],
            raw=parsed["raw"] if isinstance(parsed["raw"], (dict, list, str)) else {"text": str(parsed["raw"])[:8000]},
            normalized=parsed["normalized"],
            evidence_type="ACTUAL_RUN",
        )
    )
    db.add(
        EvidenceArtifact(
            id=str(uuid.uuid4()),
            evidence_type="ACTUAL_RUN",
            pointer={"experiment_id": eid, "file": fname},
            summary=f"Imported {fname} as ACTUAL_RUN",
        )
    )
    db.commit()
    return {"experiment_id": eid, "run_id": bid, "evidence_type": "ACTUAL_RUN", "normalized": parsed["normalized"]}


@router.get("/experiments")
def experiments(user: User = Depends(learner), db: Session = Depends(get_db)):
    exps = db.query(Experiment).filter(Experiment.user_id == user.id).order_by(Experiment.created_at.desc()).all()
    out = []
    for e in exps:
        runs = db.query(BenchmarkRun).filter(BenchmarkRun.experiment_id == e.id).all()
        latest = runs[-1] if runs else None
        out.append(
            {
                "id": e.id,
                "name": e.name,
                "kind": e.kind,
                "created_at": e.created_at.isoformat(),
                "run_ids": [r.id for r in runs],
                "latest_run_id": latest.id if latest else None,
                "normalized": latest.normalized if latest else {},
                "evidence_type": latest.evidence_type if latest else "ACTUAL_RUN",
            }
        )
    return out


class CompareIn(BaseModel):
    a: str
    b: str


@router.post("/experiments/compare")
def exp_compare(body: CompareIn, db: Session = Depends(get_db)):
    ra = db.get(BenchmarkRun, body.a) or _run_for_exp(db, body.a)
    rb = db.get(BenchmarkRun, body.b) or _run_for_exp(db, body.b)
    if not ra or not rb:
        raise HTTPException(404, "Unknown runs")
    ea = db.get(Experiment, ra.experiment_id)
    eb = db.get(Experiment, rb.experiment_id)
    return compare_runs(
        {"normalized": ra.normalized, "metadata": (ea.metadata_json if ea else {})},
        {"normalized": rb.normalized, "metadata": (eb.metadata_json if eb else {})},
    )


def _run_for_exp(db, eid: str):
    return db.query(BenchmarkRun).filter(BenchmarkRun.experiment_id == eid).first()


@router.get("/experiments/{eid}/explain")
def exp_explain(eid: str, db: Session = Depends(get_db)):
    run = db.get(BenchmarkRun, eid) or _run_for_exp(db, eid)
    if not run:
        raise HTTPException(404)
    hits = hybrid_search(db, "quantization llama memory throughput", limit=4)
    return explain_experiment(run.normalized, hits)


@router.post("/notes")
def notes(body: NoteIn, user: User = Depends(learner), db: Session = Depends(get_db)):
    n = LearnerNote(id=str(uuid.uuid4()), user_id=user.id, target_type=body.target_type, target_id=body.target_id, body=body.body)
    db.add(n)
    db.commit()
    return {"id": n.id}


@router.get("/notes")
def notes_list(user: User = Depends(learner), db: Session = Depends(get_db)):
    return [
        {"id": n.id, "target_type": n.target_type, "target_id": n.target_id, "body": n.body}
        for n in db.query(LearnerNote).filter(LearnerNote.user_id == user.id).all()
    ]


@router.post("/bookmarks")
def bookmarks(body: BookmarkIn, user: User = Depends(learner), db: Session = Depends(get_db)):
    b = Bookmark(id=str(uuid.uuid4()), user_id=user.id, **body.model_dump())
    db.add(b)
    db.commit()
    return {"id": b.id}


@router.get("/bookmarks")
def bookmarks_list(user: User = Depends(learner), db: Session = Depends(get_db)):
    return [
        {"id": b.id, "target_type": b.target_type, "target_id": b.target_id, "label": b.label}
        for b in db.query(Bookmark).filter(Bookmark.user_id == user.id).all()
    ]


@router.get("/integrity")
def integrity(db: Session = Depends(get_db)):
    qs = db.query(Question).all()
    sourced = sum(1 for q in qs if q.source_file and q.validated)
    unsupported = [q.id for q in qs if not q.source_file or q.source_file == "unknown"]
    flags = db.query(IntegrityFlag).filter(IntegrityFlag.resolved.is_(False)).all()
    return {
        "questions_total": len(qs),
        "sourced": sourced,
        "unsupported": unsupported[:50],
        "flags": [{"id": f.id, "kind": f.kind, "detail": f.detail} for f in flags],
        "notebooks_without_outputs": True,
        "note": "Generated items require source_file; twins are SIMULATED_RESULT.",
    }


@router.get("/cost")
def cost(user: User = Depends(learner), db: Session = Depends(get_db)):
    traces = db.query(ProviderTrace).filter(ProviderTrace.user_id == user.id).all()
    calls = len(traces)
    tin = sum(t.input_tokens for t in traces)
    tout = sum(t.output_tokens for t in traces)
    usd = sum(t.cost_usd for t in traces)
    return {
        "calls": calls,
        "input_tokens": tin,
        "output_tokens": tout,
        "cost_usd": usd,
        "budget_usd": settings.monthly_budget_usd,
        "by_provider": _group(traces),
    }


def _group(traces):
    out: dict[str, dict] = {}
    for t in traces:
        d = out.setdefault(t.provider, {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0})
        d["calls"] += 1
        d["input_tokens"] += t.input_tokens
        d["output_tokens"] += t.output_tokens
        d["cost_usd"] += t.cost_usd
    return out


@router.get("/progress")
def progress(user: User = Depends(learner), db: Session = Depends(get_db)):
    return {"heatmap": heatmap(db, user.id), "attempts": db.query(QuestionAttempt).filter(QuestionAttempt.user_id == user.id).count()}


@router.get("/assessment")
def assessment(db: Session = Depends(get_db)):
    qs = db.query(Question).filter(Question.concept_id == "c-assess").limit(12).all()
    return {
        "brief": (
            "Lab 8: custom agent talking to the user as a tool. Implement ≥3/5 features. "
            "Grader assumes TheBloke/Llama-2-13B-chat-GPTQ. Do not reveal a completed solution."
        ),
        "features": ["memory", "image", "code", "toxicity", "emotion"],
        "pass_rule": 3,
        "questions": [_public_q(q) for q in qs],
        "twin": "assessment-agent",
        "steps": [
            "understand",
            "hypothesis",
            "choose_features",
            "run_simulation",
            "inspect",
            "import_optional",
            "recommend",
            "defend",
        ],
        "constraints": {
            "image_syntax": "`path/to/img.png`",
            "code_fence": "```",
            "toxicity_reward": "1 - toxicity",
            "model": "TheBloke/Llama-2-13B-chat-GPTQ",
        },
    }


class DefendIn(BaseModel):
    hypothesis: str = ""
    defense: str = ""
    features: dict[str, bool] = Field(default_factory=dict)
    twin_state: dict | None = None


@router.post("/assessment/defend")
def assessment_defend(body: DefendIn, user: User = Depends(learner), db: Session = Depends(get_db)):
    n = sum(1 for v in body.features.values() if v)
    blob = f"{body.hypothesis} {body.defense}".lower()
    checks = {
        "at_least_three_features": n >= 3,
        "mentions_inverted_toxicity": ("1 -" in blob or "1-" in blob or "inverted" in blob or ("reward" in blob and "toxic" in blob)),
        "mentions_user_as_tool": ("ask-for-input" in blob or "ask for input" in blob or "user as a tool" in blob),
        "mentions_13b_not_70b": ("13b" in blob or "13 b" in blob),
    }
    missing = [k for k, v in checks.items() if not v]
    quality = max(0.0, 1.0 - 0.2 * len(missing))
    apply_event(db, user.id, "c-assess", "design", quality >= 0.55, quality=quality, note="assessment-defend")
    user.last_resume_json = {
        "text": "Last time you were defending an assessment agent design. Weakest area was naming the inverted toxicity reward and the 13B GPTQ grader."
        if "mentions_inverted_toxicity" in missing or "mentions_13b_not_70b" in missing
        else "Last time you defended an assessment agent that meets the ≥3/5 pass rule.",
        "action": "/assessment",
    }
    db.commit()
    return {
        "implemented_count": n,
        "pass_rule": 3,
        "would_pass_feature_count": n >= 3,
        "correctly_explained": [k for k, v in checks.items() if v],
        "missing": missing,
        "quality": round(quality, 3),
        "evidence_type": "TUTOR_INTERPRETATION",
        "note": "Grading reasoning, not a leaked notebook solution.",
        "twin_evidence": (body.twin_state or {}).get("evidence_type"),
    }


class DiagCompleteIn(BaseModel):
    answered: int = 0
    correct: int = 0


@router.post("/diagnostic/complete")
def diagnostic_complete(body: DiagCompleteIn, user: User = Depends(learner), db: Session = Depends(get_db)):
    hm = heatmap(db, user.id)
    weak = sorted(hm, key=lambda x: x["score"])[:3]
    user.last_resume_json = {
        "text": (
            f"You finished the diagnostic ({body.correct}/{body.answered} marked correct). "
            + (
                f"Start with {weak[0]['name']}."
                if weak
                else "Open notebook 1 and the pipeline twin."
            )
        ),
        "action": f"/learn?concept={weak[0]['concept_id']}" if weak else "/learn",
    }
    db.commit()
    states = db.query(MasteryState).filter(MasteryState.user_id == user.id).all()
    scored = sorted(states, key=lambda s: s.score)
    concepts = {c.id: c for c in db.query(Concept).all()}
    weak_ui = [
        {"id": s.concept_id, "name": concepts.get(s.concept_id).name if concepts.get(s.concept_id) else s.concept_id, "score": s.score}
        for s in scored[:5]
    ]
    return {
        "heatmap": hm,
        "correct": body.correct,
        "answered": body.answered,
        "plan": _thirty(db, user, weak_ui),
        "resume": user.last_resume_json,
    }


class VoiceIn(BaseModel):
    text: str
    interrupt: bool = False


@router.post("/voice/tts")
def voice_tts(body: VoiceIn, user: User = Depends(learner)):
    if user.voice_provider in (None, "none"):
        return {"ok": False, "reason": "Voice is optional and currently off."}
    p = VOICE.get(user.voice_provider)
    if not p or not p.available():
        return {"ok": False, "reason": f"{user.voice_provider} not configured", "interrupted": body.interrupt}
    return {
        "ok": False,
        "reason": "Keys present but TTS bytes are not fetched in demo to avoid surprise cost.",
        "interrupted": body.interrupt,
        "transcript_echo": body.text[:200],
    }


@router.get("/omniverse/status")
def omniverse_status():
    return {
        "available": bool(settings.omniverse_bridge_url),
        "bridge": settings.omniverse_bridge_url,
        "note": "No Kit repo was vendored. Web twins remain the daily experience.",
    }
