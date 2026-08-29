from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field


ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseModel):
    app_name: str = "LLM Twin Academy"
    course_title: str = (
        "NVIDIA DLI — Rapid Application Development Using Large Language Models"
    )
    database_url: str = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL", f"sqlite:///{ROOT / 'data' / 'academy.db'}"
        )
    )
    course_materials_dir: Path = Field(
        default_factory=lambda: Path(
            os.getenv("COURSE_MATERIALS_DIR", str(ROOT / "course-materials"))
        )
    )
    openai_api_key: str | None = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    openai_model: str = Field(
        default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    )
    nim_base_url: str | None = Field(default_factory=lambda: os.getenv("NIM_BASE_URL"))
    nvidia_api_key: str | None = Field(default_factory=lambda: os.getenv("NVIDIA_API_KEY"))
    nvidia_nim_model: str = Field(
        default_factory=lambda: os.getenv("NVIDIA_NIM_MODEL", "meta/llama-3.1-8b-instruct")
    )
    huggingface_api_key: str | None = Field(
        default_factory=lambda: os.getenv("HUGGINGFACE_API_KEY")
    )
    huggingface_model: str = Field(
        default_factory=lambda: os.getenv("HUGGINGFACE_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
    )
    elevenlabs_api_key: str | None = Field(
        default_factory=lambda: os.getenv("ELEVENLABS_API_KEY")
    )
    elevenlabs_voice_id: str | None = Field(
        default_factory=lambda: os.getenv("ELEVENLABS_VOICE_ID")
    )
    sarvam_api_key: str | None = Field(default_factory=lambda: os.getenv("SARVAM_API_KEY"))
    perplexity_api_key: str | None = Field(
        default_factory=lambda: os.getenv("PERPLEXITY_API_KEY")
    )
    langfuse_public_key: str | None = Field(
        default_factory=lambda: os.getenv("LANGFUSE_PUBLIC_KEY")
    )
    langfuse_secret_key: str | None = Field(
        default_factory=lambda: os.getenv("LANGFUSE_SECRET_KEY")
    )
    langfuse_host: str | None = Field(default_factory=lambda: os.getenv("LANGFUSE_HOST"))
    omniverse_bridge_url: str | None = Field(
        default_factory=lambda: os.getenv("OMNIVERSE_BRIDGE_URL")
    )
    nvcf_api_key: str | None = Field(default_factory=lambda: os.getenv("NVCF_API_KEY"))
    cors_origins: str = Field(
        default_factory=lambda: os.getenv("CORS_ORIGINS", "http://localhost:3000")
    )
    cors_origin_regex: str = Field(
        default_factory=lambda: os.getenv(
            "CORS_ORIGIN_REGEX",
            r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$|^https://.*\.modal\.run$|^https://.*\.vercel\.app$",
        )
    )
    demo_learner_id: str = "demo-learner"
    embedding_dim: int = 256
    monthly_budget_usd: float = Field(
        default_factory=lambda: float(os.getenv("MONTHLY_BUDGET_USD", "25"))
    )


settings = Settings()
