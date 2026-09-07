from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def utcnow() -> datetime:
    return datetime.utcnow()


class EvidenceType(str, enum.Enum):
    COURSE_SOURCE = "COURSE_SOURCE"
    EXPECTED_RESULT = "EXPECTED_RESULT"
    SIMULATED_RESULT = "SIMULATED_RESULT"
    ACTUAL_RUN = "ACTUAL_RUN"
    TUTOR_INTERPRETATION = "TUTOR_INTERPRETATION"
    EXTERNAL_RESEARCH = "EXTERNAL_RESEARCH"


class TutorMode(str, enum.Enum):
    COURSE = "COURSE"
    RESEARCH = "RESEARCH"


class ExplanationDepth(str, enum.Enum):
    SCHOOL = "SCHOOL"
    ENGINEER = "ENGINEER"
    RESEARCH = "RESEARCH"


class ProviderName(str, enum.Enum):
    DEMO = "demo"
    OPENAI = "openai"
    NVIDIA_NIM = "nvidia_nim"
    HUGGINGFACE = "huggingface"


class VoiceProviderName(str, enum.Enum):
    NONE = "none"
    ELEVENLABS = "elevenlabs"
    SARVAM = "sarvam"
    OPENAI_REALTIME = "openai_realtime"


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(128), default="Learner")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    onboarded: Mapped[bool] = mapped_column(Boolean, default=False)
    tutor_provider: Mapped[str] = mapped_column(String(32), default=ProviderName.DEMO.value)
    voice_provider: Mapped[str] = mapped_column(String(32), default=VoiceProviderName.NONE.value)
    research_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    explanation_depth: Mapped[str] = mapped_column(
        String(16), default=ExplanationDepth.ENGINEER.value
    )
    tutor_mode: Mapped[str] = mapped_column(String(16), default=TutorMode.COURSE.value)
    last_resume_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)


class Course(Base):
    __tablename__ = "courses"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True)
    title: Mapped[str] = mapped_column(String(256))
    vendor: Mapped[str] = mapped_column(String(128), default="NVIDIA Deep Learning Institute")
    description: Mapped[str] = mapped_column(Text, default="")


class SourceArtifact(Base):
    __tablename__ = "source_artifacts"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id"))
    source_type: Mapped[str] = mapped_column(String(32))
    filename: Mapped[str] = mapped_column(String(512))
    relpath: Mapped[str] = mapped_column(String(1024))
    title: Mapped[str] = mapped_column(String(512), default="")
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    sha256: Mapped[str] = mapped_column(String(64), default="")
    extra: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    spans: Mapped[list[SourceSpan]] = relationship(back_populates="artifact")


class SourceSpan(Base):
    __tablename__ = "source_spans"
    __table_args__ = (Index("ix_span_artifact_cell", "artifact_id", "cell_index"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    artifact_id: Mapped[str] = mapped_column(ForeignKey("source_artifacts.id"))
    source_type: Mapped[str] = mapped_column(String(32))
    file: Mapped[str] = mapped_column(String(512))
    cell_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    slide: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cell_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    heading: Mapped[str | None] = mapped_column(String(512), nullable=True)
    body: Mapped[str] = mapped_column(Text, default="")
    code: Mapped[str | None] = mapped_column(Text, nullable=True)
    stored_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evidence_type: Mapped[str] = mapped_column(
        String(32), default=EvidenceType.COURSE_SOURCE.value
    )
    embedding: Mapped[list[float] | None] = mapped_column(JSON, default=None)
    extra: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    artifact: Mapped[SourceArtifact] = relationship(back_populates="spans")


class Notebook(Base):
    __tablename__ = "notebooks"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    artifact_id: Mapped[str] = mapped_column(ForeignKey("source_artifacts.id"))
    filename: Mapped[str] = mapped_column(String(512))
    title: Mapped[str] = mapped_column(String(512))
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    purpose: Mapped[str] = mapped_column(Text, default="")
    why_it_matters: Mapped[str] = mapped_column(Text, default="")
    expected_outcome: Mapped[str] = mapped_column(Text, default="")
    cells: Mapped[list[NotebookCell]] = relationship(back_populates="notebook")


class NotebookCell(Base):
    __tablename__ = "notebook_cells"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    notebook_id: Mapped[str] = mapped_column(ForeignKey("notebooks.id"))
    span_id: Mapped[str | None] = mapped_column(ForeignKey("source_spans.id"), nullable=True)
    cell_index: Mapped[int] = mapped_column(Integer)
    cell_type: Mapped[str] = mapped_column(String(32))
    source: Mapped[str] = mapped_column(Text, default="")
    stored_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    plain_english: Mapped[str] = mapped_column(Text, default="")
    line_by_line: Mapped[str] = mapped_column(Text, default="")
    why_exists: Mapped[str] = mapped_column(Text, default="")
    what_should_happen: Mapped[str] = mapped_column(Text, default="")
    how_to_verify: Mapped[str] = mapped_column(Text, default="")
    common_failure: Mapped[str] = mapped_column(Text, default="")
    try_modifying: Mapped[str] = mapped_column(Text, default="")
    business_impact: Mapped[str] = mapped_column(Text, default="")
    blocked_execution: Mapped[bool] = mapped_column(Boolean, default=True)
    safety_flags: Mapped[list[str] | None] = mapped_column(JSON, default=None)
    notebook: Mapped[Notebook] = relationship(back_populates="cells")


class Concept(Base):
    __tablename__ = "concepts"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(256))
    cluster: Mapped[str] = mapped_column(String(64), default="fundamentals")
    definition: Mapped[str] = mapped_column(Text, default="")
    school: Mapped[str] = mapped_column(Text, default="")
    engineer: Mapped[str] = mapped_column(Text, default="")
    research: Mapped[str] = mapped_column(Text, default="")
    analogy: Mapped[str] = mapped_column(Text, default="")
    common_misconceptions: Mapped[list[str] | None] = mapped_column(JSON, default=None)
    notebook_file: Mapped[str | None] = mapped_column(String(256), nullable=True)
    cell_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    twin_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_span_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class ConceptEdge(Base):
    __tablename__ = "concept_edges"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    src_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"))
    dst_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"))
    relation: Mapped[str] = mapped_column(String(32))
    note: Mapped[str] = mapped_column(Text, default="")


class LearningObjective(Base):
    __tablename__ = "learning_objectives"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id"))
    notebook_file: Mapped[str] = mapped_column(String(256))
    text: Mapped[str] = mapped_column(Text)
    concept_ids: Mapped[list[str] | None] = mapped_column(JSON, default=None)


class Lesson(Base):
    __tablename__ = "lessons"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"))
    title: Mapped[str] = mapped_column(String(256))
    steps: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, default=None)


class Misconception(Base):
    __tablename__ = "misconceptions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True)
    title: Mapped[str] = mapped_column(String(256))
    left: Mapped[str] = mapped_column(String(128))
    right: Mapped[str] = mapped_column(String(128))
    confusion: Mapped[str] = mapped_column(Text)
    distinction: Mapped[str] = mapped_column(Text)
    source_file: Mapped[str] = mapped_column(String(256), default="")
    source_cell: Mapped[int | None] = mapped_column(Integer, nullable=True)
    remediation: Mapped[str] = mapped_column(Text, default="")


class MasteryState(Base):
    __tablename__ = "mastery_states"
    __table_args__ = (UniqueConstraint("user_id", "concept_id"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"))
    score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.2)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    correct_attempts: Mapped[int] = mapped_column(Integer, default=0)
    viewed: Mapped[int] = mapped_column(Integer, default=0)
    explain_quality: Mapped[float] = mapped_column(Float, default=0.0)
    teachback_quality: Mapped[float] = mapped_column(Float, default=0.0)
    hints_used: Mapped[int] = mapped_column(Integer, default=0)
    last_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    last_reviewed: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_review: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    misconception_tags: Mapped[list[str] | None] = mapped_column(JSON, default=None)
    stability: Mapped[float] = mapped_column(Float, default=0.4)
    difficulty: Mapped[float] = mapped_column(Float, default=5.0)
    reps: Mapped[int] = mapped_column(Integer, default=0)
    lapses: Mapped[int] = mapped_column(Integer, default=0)
    evidence_log: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, default=None)


class Question(Base):
    __tablename__ = "questions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    qtype: Mapped[str] = mapped_column(String(32))
    bloom: Mapped[str] = mapped_column(String(32))
    difficulty: Mapped[int] = mapped_column(Integer, default=2)
    stem: Mapped[str] = mapped_column(Text)
    options: Mapped[list[str] | None] = mapped_column(JSON, default=None)
    answer: Mapped[Any] = mapped_column(JSON)
    explanation: Mapped[str] = mapped_column(Text, default="")
    concept_id: Mapped[str | None] = mapped_column(ForeignKey("concepts.id"), nullable=True)
    misconception_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_file: Mapped[str] = mapped_column(String(256))
    source_cell: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evidence_type: Mapped[str] = mapped_column(
        String(32), default=EvidenceType.COURSE_SOURCE.value
    )
    validated: Mapped[bool] = mapped_column(Boolean, default=True)
    integrity_flags: Mapped[list[str] | None] = mapped_column(JSON, default=None)


class QuestionAttempt(Base):
    __tablename__ = "question_attempts"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"))
    given: Mapped[Any] = mapped_column(JSON)
    correct: Mapped[bool] = mapped_column(Boolean, default=False)
    hints_used: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[float] = mapped_column(Float, default=0)
    feedback: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ReviewItem(Base):
    __tablename__ = "review_items"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    concept_id: Mapped[str | None] = mapped_column(ForeignKey("concepts.id"), nullable=True)
    question_id: Mapped[str | None] = mapped_column(ForeignKey("questions.id"), nullable=True)
    due_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    origin: Mapped[str] = mapped_column(String(64), default="weak_concept")
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)


class TutorSession(Base):
    __tablename__ = "tutor_sessions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    mode: Mapped[str] = mapped_column(String(16), default=TutorMode.COURSE.value)
    depth: Mapped[str] = mapped_column(String(16), default=ExplanationDepth.ENGINEER.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class TutorMessage(Base):
    __tablename__ = "tutor_messages"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("tutor_sessions.id"))
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    intent: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sources: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, default=None)
    evidence_type: Mapped[str] = mapped_column(
        String(32), default=EvidenceType.TUTOR_INTERPRETATION.value
    )
    provider_trace: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class LearnerPrediction(Base):
    __tablename__ = "learner_predictions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    twin_id: Mapped[str] = mapped_column(String(64))
    prompt: Mapped[str] = mapped_column(Text)
    predicted: Mapped[dict[str, Any]] = mapped_column(JSON)
    observed: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    revealed: Mapped[bool] = mapped_column(Boolean, default=False)
    why: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class DigitalTwin(Base):
    __tablename__ = "digital_twins"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True)
    name: Mapped[str] = mapped_column(String(256))
    summary: Mapped[str] = mapped_column(Text, default="")
    notebook_file: Mapped[str] = mapped_column(String(256), default="")
    controls: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, default=None)


class TwinScenario(Base):
    __tablename__ = "twin_scenarios"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    twin_id: Mapped[str] = mapped_column(ForeignKey("digital_twins.id"))
    name: Mapped[str] = mapped_column(String(256))
    params: Mapped[dict[str, Any]] = mapped_column(JSON)
    teaching_point: Mapped[str] = mapped_column(Text, default="")


class TwinRun(Base):
    __tablename__ = "twin_runs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    twin_id: Mapped[str] = mapped_column(String(64))
    params: Mapped[dict[str, Any]] = mapped_column(JSON)
    state: Mapped[dict[str, Any]] = mapped_column(JSON)
    evidence_type: Mapped[str] = mapped_column(
        String(32), default=EvidenceType.SIMULATED_RESULT.value
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Experiment(Base):
    __tablename__ = "experiments"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(256))
    kind: Mapped[str] = mapped_column(String(64))
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class BenchmarkRun(Base):
    __tablename__ = "benchmark_runs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    experiment_id: Mapped[str] = mapped_column(ForeignKey("experiments.id"))
    source_format: Mapped[str] = mapped_column(String(64))
    raw: Mapped[dict[str, Any] | str] = mapped_column(JSON)
    normalized: Mapped[dict[str, Any]] = mapped_column(JSON)
    evidence_type: Mapped[str] = mapped_column(
        String(32), default=EvidenceType.ACTUAL_RUN.value
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class EvidenceArtifact(Base):
    __tablename__ = "evidence_artifacts"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    evidence_type: Mapped[str] = mapped_column(String(32))
    pointer: Mapped[dict[str, Any]] = mapped_column(JSON)
    summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ProviderTrace(Base):
    __tablename__ = "provider_traces"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    provider: Mapped[str] = mapped_column(String(32))
    model: Mapped[str] = mapped_column(String(128), default="")
    feature: Mapped[str] = mapped_column(String(64), default="tutor")
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[float] = mapped_column(Float, default=0)
    ttft_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    tpot_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost_usd: Mapped[float] = mapped_column(Float, default=0)
    trace_id: Mapped[str] = mapped_column(String(64), default="")
    extra: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class LearnerNote(Base):
    __tablename__ = "learner_notes"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    target_type: Mapped[str] = mapped_column(String(32))
    target_id: Mapped[str] = mapped_column(String(64))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Bookmark(Base):
    __tablename__ = "bookmarks"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    target_type: Mapped[str] = mapped_column(String(32))
    target_id: Mapped[str] = mapped_column(String(64))
    label: Mapped[str] = mapped_column(String(256), default="Review later")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class IntegrityFlag(Base):
    __tablename__ = "integrity_flags"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    kind: Mapped[str] = mapped_column(String(32))
    item_type: Mapped[str] = mapped_column(String(32))
    item_id: Mapped[str] = mapped_column(String(64))
    detail: Mapped[str] = mapped_column(Text)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
