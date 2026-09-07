"""Spec API surface: walkthroughs, risks, setup, SSE tutor, learning aliases."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import Concept, Lesson, Notebook, NotebookCell, SourceSpan, TwinRun, User
from app.db.session import get_db
from app.domains.risks.catalog import RISKS
from app.domains.tutor.service import tutor_turn
from app.domains.twins.engine import TWIN_CATALOG, run as run_twin
from app.domains.voice.service import transcribe_stub, voice_status
from app.domains.topics.catalog import get_topic, list_topics
from app.domains.walkthrough.engine import build_walkthrough
from app.routers.api import learner, review as review_due
from app.domains.providers.registry import PROVIDERS, VOICE, PerplexityResearchProvider

router = APIRouter()


def _nb_or_404(db: Session, nid: str) -> Notebook:
    n = db.get(Notebook, nid)
    if not n:
        n = db.query(Notebook).filter(Notebook.filename == nid).one_or_none()
    if not n:
        raise HTTPException(
            404,
            {
                "error": "unknown notebook",
                "hint": "IDs are sha1(path). If you bookmarked an old uuid or md5 link, look up by file name instead. Cold starts recreate SQLite but ids stay stable for the same files.",
                "tried": nid,
            },
        )
    return n


@router.get("/spans/{sid}")
def span_one(sid: str, db: Session = Depends(get_db)):
    s = db.get(SourceSpan, sid)
    if not s:
        raise HTTPException(404, {"error": "unknown span", "hint": "Spans use sha1(artifact:locator:kind:seq).", "tried": sid})
    return {
        "id": s.id,
        "file": s.file,
        "cell_index": s.cell_index,
        "page": s.page,
        "slide": s.slide,
        "heading": s.heading,
        "excerpt": (s.body or s.code or "")[:900],
        "evidence_type": s.evidence_type,
    }


@router.get("/notebooks/{nid}/walkthrough")
def notebook_walkthrough(nid: str, depth: str = "simple", db: Session = Depends(get_db)):
    n = _nb_or_404(db, nid)
    cells = (
        db.query(NotebookCell).filter(NotebookCell.notebook_id == n.id).order_by(NotebookCell.cell_index).all()
    )
    concepts = db.query(Concept).filter(Concept.notebook_file == n.filename).all()
    payload = build_walkthrough(
        n.filename,
        [{"cell_index": c.cell_index} for c in cells],
        [
            {
                "id": c.id,
                "name": c.name,
                "school": c.school,
                "research": c.research,
                "analogy": c.analogy,
                "definition": c.definition,
                "cell_index": c.cell_index,
            }
            for c in concepts
        ],
        depth=depth,
    )
    payload["notebook_id"] = n.id
    payload["filename"] = n.filename
    return payload


@router.get("/lessons")
def lessons(db: Session = Depends(get_db)):
    rows = db.query(Lesson).all()
    return [{"id": r.id, "concept_id": r.concept_id, "title": r.title, "steps": r.steps} for r in rows]


@router.get("/lessons/{lid}")
def lesson_one(lid: str, db: Session = Depends(get_db)):
    row = db.get(Lesson, lid) or db.query(Lesson).filter(Lesson.concept_id == lid).one_or_none()
    if not row:
        raise HTTPException(404, "unknown lesson")
    return {"id": row.id, "concept_id": row.concept_id, "title": row.title, "steps": row.steps}


@router.get("/topics")
def topics(db: Session = Depends(get_db)):
    rows = []
    for t in list_topics():
        concepts = []
        for cid in t["concept_ids"]:
            c = db.get(Concept, cid)
            if c:
                concepts.append(
                    {
                        "id": c.id,
                        "name": c.name,
                        "definition": c.definition,
                        "analogy": c.analogy,
                        "school": c.school,
                        "engineer": c.engineer,
                    }
                )
        rows.append({**t, "concepts": concepts, "concept_count": len(concepts)})
    return rows


@router.get("/topics/{tid}")
def topic_one(tid: str, db: Session = Depends(get_db)):
    t = get_topic(tid)
    if not t:
        raise HTTPException(404, {"error": "unknown topic", "tried": tid})
    concepts = []
    for cid in t["concept_ids"]:
        c = db.get(Concept, cid)
        if not c:
            continue
        concepts.append(
            {
                "id": c.id,
                "name": c.name,
                "slug": c.slug,
                "definition": c.definition,
                "analogy": c.analogy,
                "school": c.school,
                "engineer": c.engineer,
                "research": c.research,
                "notebook_file": c.notebook_file,
                "cell_index": c.cell_index,
                "twin_id": c.twin_id,
            }
        )
    return {**t, "concepts": concepts}


@router.get("/risks")
def risks():
    return RISKS


@router.get("/learning/reviews/due")
def learning_reviews(user: User = Depends(learner), db: Session = Depends(get_db)):
    return review_due(user, db)


@router.get("/setup")
def setup():
    px = PerplexityResearchProvider()
    status = {name: ("connected" if p.available() else "not_configured") for name, p in PROVIDERS.items()}
    status.update({f"voice_{n}": ("connected" if v.available() else "not_configured") for n, v in VOICE.items()})
    status["perplexity"] = "connected" if px.available() else "not_configured"
    return {
        "app": settings.app_name,
        "zero_key_demo": True,
        "disclaimer": "Not affiliated with or endorsed by NVIDIA. course-materials/ is bring-your-own, personal-use licensed content.",
        "providers": status,
        "go_live": [
            {"item": "Demo tutor", "ok": True, "note": "Works offline"},
            {"item": "OpenAI tutor", "ok": bool(settings.openai_api_key)},
            {"item": "NVIDIA NIM tutor", "ok": bool(settings.nim_base_url and settings.nvidia_api_key)},
            {"item": "ElevenLabs TTS", "ok": bool(settings.elevenlabs_api_key)},
            {"item": "Perplexity research", "ok": bool(settings.perplexity_api_key)},
            {"item": "Postgres", "ok": settings.database_url.startswith("postgres")},
        ],
    }


@router.get("/voice/status")
def voice_stat():
    return voice_status()


class SttIn(BaseModel):
    note: str = ""


@router.post("/voice/stt")
def voice_stt(body: SttIn):
    return transcribe_stub(body.note)


class TwinRunIn(BaseModel):
    params: dict = Field(default_factory=dict)
    prediction_id: str | None = None
    committed: bool | None = None


@router.post("/twins/{tid}/run")
def twin_run_alias(tid: str, body: TwinRunIn, user: User = Depends(learner), db: Session = Depends(get_db)):
    params = dict(body.params)
    if body.committed is not None:
        params["committed"] = body.committed
    if tid not in {t["id"] for t in TWIN_CATALOG} and tid != "keda-autoscaling":
        raise HTTPException(404, f"Unknown twin scenario: {tid}")
    state = run_twin(tid, params)
    rid = str(uuid.uuid4())
    db.add(
        TwinRun(
            id=rid,
            user_id=user.id,
            twin_id=tid,
            params=params,
            state=state,
            evidence_type=state.get("evidence_type", "SIMULATED_RESULT"),
        )
    )
    db.commit()
    return {"run_id": rid, "state": state, "twin_id": tid}


class SessionIn(BaseModel):
    mode: str | None = None
    depth: str | None = None


@router.post("/tutor/sessions")
def tutor_session(body: SessionIn, user: User = Depends(learner), db: Session = Depends(get_db)):
    from app.db.models import TutorSession

    sid = str(uuid.uuid4())
    db.add(TutorSession(id=sid, user_id=user.id, mode=(body.mode or user.tutor_mode), depth=(body.depth or user.explanation_depth)))
    db.commit()
    return {"session_id": sid}


class MsgIn(BaseModel):
    content: str
    mode: str | None = None
    depth: str | None = None
    provider: str | None = None


@router.post("/tutor/sessions/{sid}/messages")
async def tutor_message(sid: str, body: MsgIn, user: User = Depends(learner), db: Session = Depends(get_db)):
    if body.provider and body.provider != "auto":
        user.tutor_provider = body.provider if body.provider != "nim" else "nvidia_nim"
    result = tutor_turn(db, user, sid, body.content, mode=body.mode, depth=body.depth)

    def events():
        yield f"event: meta\ndata: {json.dumps({k: result[k] for k in ('session_id', 'evidence_type', 'provider', 'mode')})}\n\n"
        yield f"event: text\ndata: {json.dumps({'text': result['text']})}\n\n"
        yield f"event: sources\ndata: {json.dumps(result.get('sources') or [])}\n\n"
        yield f"event: telemetry\ndata: {json.dumps(result.get('how_served') or {})}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
