from __future__ import annotations

import re
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import EvidenceType, ProviderTrace, Question, TutorMessage, TutorMode, TutorSession, User
from app.domains.providers.base import TutorRequest
from app.domains.providers.registry import PerplexityResearchProvider, get_provider
from app.domains.retrieval.search import hybrid_search, match_concepts

INTENTS = [
    ("simpler", r"\b(simpler|eli5|school mode|analogy)\b"),
    ("deeper", r"\b(deeper|engineer|research mode|math)\b"),
    ("show_source", r"\b(show source|view source|citation|notebook cell)\b"),
    ("show_architecture", r"\b(architecture|diagram|show architecture)\b"),
    ("quiz", r"\b(quiz me|test me|challenge me)\b"),
    ("hint", r"\b(hint|don't reveal|do not reveal)\b"),
    ("compare", r"\bcompare\b"),
    ("twin", r"\b(digital twin|run scenario|what happens if)\b"),
    ("debug", r"\b(why did this happen|debug)\b"),
    ("next", r"\b(what should i learn next|10 minutes)\b"),
    ("assessment", r"\b(assessment mode|interview me)\b"),
    ("teachback", r"\b(let me teach|teach it back|let me explain)\b"),
    ("telemetry", r"\b(inference telemetry|how this answer was served|ttft|tpot)\b"),
    ("line_by_line", r"\b(line-by-line|line by line|explain code)\b"),
]


def detect_intent(text: str) -> str:
    t = text.lower()
    for name, pat in INTENTS:
        if re.search(pat, t):
            return name
    return "explain"


COURSE_SYS = """You are the LLM Twin Academy tutor for NVIDIA DLI Rapid Application Development using LLMs.
COURSE MODE: use only notebook excerpts, learner notes, and imported ACTUAL_RUN evidence.
If unsupported, say: "This is not established by the supplied course material."
Never invent NIM Operator, KEDA, Dynamo, or Grove as course facts.
Label synthesis TUTOR_INTERPRETATION. Notebooks here have no stored outputs.
Do not execute notebook shell/Python.
"""


def tutor_turn(
    db: Session,
    user: User,
    session_id: str | None,
    content: str,
    *,
    mode: str | None = None,
    depth: str | None = None,
) -> dict[str, Any]:
    mode = (mode or user.tutor_mode or TutorMode.COURSE.value).upper()
    depth = (depth or user.explanation_depth or "ENGINEER").upper()
    if mode == "RESEARCH" and not user.research_enabled:
        mode = "COURSE"

    if not session_id:
        session_id = str(uuid.uuid4())
        db.add(TutorSession(id=session_id, user_id=user.id, mode=mode, depth=depth))
        db.flush()

    intent = detect_intent(content)
    hits = hybrid_search(db, content, limit=6)
    concepts = match_concepts(db, content, limit=4)
    db.add(
        TutorMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=content,
            intent=intent,
            evidence_type=EvidenceType.COURSE_SOURCE.value,
        )
    )

    research_meta = None
    if mode == "RESEARCH" and user.research_enabled and (not hits or _needs_research(content)):
        px = PerplexityResearchProvider()
        research_meta = px.search(content) if px.available() else {"error": "not configured", "citations": []}

    if mode == "COURSE" and not hits:
        text = (
            "This is not established by the supplied course material. "
            "I searched ingested NVIDIA notebooks and found no supporting span."
        )
        evidence = EvidenceType.COURSE_SOURCE.value
        provider_name = "demo"
        trace = _trace_demo(db, user.id, text)
        sources: list = []
    else:
        provider, fell_back = get_provider(user.tutor_provider)
        provider_name = provider.name
        if provider.name == "demo" or fell_back:
            text = _demo_compose(content, intent, hits, concepts, mode, depth, research_meta)
            if fell_back and user.tutor_provider != "demo":
                text = f"[Provider {user.tutor_provider} offline — Demo used with disclosure]\n\n" + text
                provider_name = "demo"
            trace = _trace_demo(db, user.id, text)
        else:
            sys = COURSE_SYS + (f"\nDEPTH={depth}" if depth else "")
            if mode == "RESEARCH":
                sys += "\nRESEARCH MODE: mark EXTERNAL_RESEARCH; never overwrite course spans."
            ctx = "\n\n".join(
                f"[{h['evidence_type']}] {h['file']} cell={h['cell_index']}\n{h['excerpt']}" for h in hits
            )
            if research_meta:
                ctx += "\n\n[EXTERNAL_RESEARCH]\n" + str(research_meta)[:1500]
            try:
                resp = provider.generate(
                    TutorRequest(
                        messages=[{"role": "user", "content": f"{content}\n\nSPANS:\n{ctx}"}],
                        mode=mode,
                        depth=depth,
                        system=sys,
                    )
                )
                text = resp.text
                trace = _trace_real(db, user.id, resp)
            except Exception as exc:  # noqa: BLE001
                text = f"Provider `{provider.name}` failed: {exc}. Not silently switching."
                provider_name = provider.name
                trace = _trace_demo(db, user.id, text)
        sources = hits
        evidence = (
            EvidenceType.EXTERNAL_RESEARCH.value
            if research_meta and research_meta.get("text")
            else EvidenceType.TUTOR_INTERPRETATION.value
        )

    msg_id = str(uuid.uuid4())
    quiz = None
    if intent == "quiz":
        qrow = db.query(Question).filter(Question.qtype == "mcq").first()
        if qrow:
            quiz = {
                "id": qrow.id,
                "stem": qrow.stem,
                "options": qrow.options,
                "concept_id": qrow.concept_id,
                "source": {"file": qrow.source_file, "cell_index": qrow.source_cell},
            }
            text = text + "\n\nQuiz (do not reveal yet): " + qrow.stem
    db.add(
        TutorMessage(
            id=msg_id,
            session_id=session_id,
            role="assistant",
            content=text,
            intent=intent,
            sources=sources,
            evidence_type=evidence,
            provider_trace=trace,
        )
    )
    db.commit()
    return {
        "session_id": session_id,
        "message_id": msg_id,
        "intent": intent,
        "mode": mode,
        "depth": depth,
        "text": text,
        "sources": hits,
        "concepts": [{"id": c.id, "name": c.name, "slug": c.slug} for c in concepts],
        "evidence_type": evidence,
        "provider": provider_name,
        "how_served": trace,
        "quiz": quiz,
    }


def _needs_research(content: str) -> bool:
    return bool(re.search(r"\b(current|2024|2025|2026|latest|today)\b", content.lower()))


def _demo_compose(content, intent, hits, concepts, mode, depth, research_meta) -> str:
    if not hits and mode == "COURSE":
        return "This is not established by the supplied course material."
    lines = [f"Depth: {depth}. Intent: {intent}. Mode: {mode}.", "", "🔵 COURSE_SOURCE:"]
    for h in hits[:4]:
        lines.append(f"- {h['file']} · cell {h['cell_index']} · {h['heading']}")
        lines.append(f"  {h['excerpt'][:400]}")
    lines.append("\n🟣 TUTOR_INTERPRETATION (not a measurement):")
    if concepts:
        lines.append("Likely concepts: " + ", ".join(c.name for c in concepts) + ".")
    lines.append("This repo stores no notebook outputs. Twin numbers are SIMULATED_RESULT.")
    if intent == "hint":
        lines.append("Hint: name tokenizer vs model vs head before asking for the full answer.")
    if research_meta:
        lines.append("\n🟠 EXTERNAL_RESEARCH (must not override course):")
        lines.append(str(research_meta.get("text") or research_meta.get("error"))[:800])
    lines.append("\nQuestion: " + content[:400])
    return "\n".join(lines)


def _trace_real(db, user_id, resp) -> dict:
    tid = str(uuid.uuid4())
    db.add(
        ProviderTrace(
            id=tid,
            user_id=user_id,
            provider=resp.provider,
            model=resp.model,
            feature="tutor",
            input_tokens=resp.input_tokens,
            output_tokens=resp.output_tokens,
            latency_ms=resp.latency_ms,
            ttft_ms=resp.ttft_ms,
            tpot_ms=resp.tpot_ms,
            trace_id=tid,
        )
    )
    tps = None
    if resp.latency_ms and resp.output_tokens:
        tps = round(resp.output_tokens / (resp.latency_ms / 1000.0), 3)
    return {
        "provider": resp.provider,
        "model": resp.model,
        "input_tokens": resp.input_tokens,
        "output_tokens": resp.output_tokens,
        "latency_ms": round(resp.latency_ms, 1),
        "ttft_ms": resp.ttft_ms,
        "tpot_ms": resp.tpot_ms,
        "tokens_per_sec": tps,
        "trace_id": tid,
        "evidence_type": "ACTUAL_RUN",
    }


def _trace_demo(db, user_id, text) -> dict:
    tid = str(uuid.uuid4())
    db.add(
        ProviderTrace(
            id=tid,
            user_id=user_id,
            provider="demo",
            model="demo-grounded",
            feature="tutor",
            output_tokens=len(text.split()),
            latency_ms=1,
            trace_id=tid,
        )
    )
    return {
        "provider": "demo",
        "model": "demo-grounded",
        "latency_ms": 1,
        "trace_id": tid,
        "evidence_type": "TUTOR_INTERPRETATION",
        "note": "Demo path — not GPU inference.",
    }
