"""LLM Twin Academy API on Modal. Pin to one container while SQLite is the store."""

from __future__ import annotations

import os
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parents[2]

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "fastapi==0.115.6",
        "uvicorn[standard]==0.32.1",
        "sqlalchemy==2.0.36",
        "pydantic==2.10.3",
        "nbformat==5.10.4",
        "python-multipart==0.0.19",
        "httpx==0.28.1",
        "numpy==2.2.1",
        "alembic==1.14.0",
    )
    .add_local_dir(str(ROOT / "services" / "api"), remote_path="/root/api")
    .add_local_dir(str(ROOT / "services" / "twin-engine"), remote_path="/root/twin-engine")
    .add_local_dir(str(ROOT / "course-materials"), remote_path="/root/course-materials")
)

app = modal.App("llm-twin-academy-api", image=image)

min_containers = int(os.environ.get("MODAL_MIN_CONTAINERS", "0"))
max_containers = int(os.environ.get("MODAL_MAX_CONTAINERS", "1"))


@app.function(
    secrets=[modal.Secret.from_name("academy-env", required_keys=[])],
    min_containers=min_containers,
    max_containers=max_containers,
    scaledown_window=300,
)
@modal.concurrent(max_inputs=100)
@modal.asgi_app()
def fastapi_app():
    import sys
    from pathlib import Path as P

    sys.path.insert(0, "/root/api")
    sys.path.insert(0, "/root/twin-engine")
    os.environ.setdefault("COURSE_MATERIALS_DIR", "/root/course-materials")
    data = P("/root/data")
    data.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{data / 'academy.db'}")
    os.environ.setdefault(
        "CORS_ORIGIN_REGEX",
        r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$|^https://.*\.modal\.run$|^https://.*\.vercel\.app$",
    )
    from app.main import app as fa

    return fa
