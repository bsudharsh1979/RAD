"""LLM Twin Academy Next.js web on Modal."""

from __future__ import annotations

import os
from pathlib import Path

import modal


def _repo_root() -> Path | None:
    here = Path(__file__).resolve()
    for p in (here.parent, *here.parents):
        if (p / "apps" / "web").is_dir():
            return p
    return None


ROOT = _repo_root()
API_BASE = os.environ.get("NEXT_PUBLIC_API_BASE", "").rstrip("/")

image = modal.Image.from_registry("node:22-bookworm-slim", add_python="3.12").run_commands(
    "apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*"
)
if ROOT is not None:
    image = (
        image.add_local_dir(str(ROOT / "apps" / "web"), remote_path="/web", copy=True)
        .add_local_file(str(ROOT / "deploy" / "modal" / "build_web.sh"), remote_path="/build_web.sh", copy=True)
        .env(
            {
                "NEXT_PUBLIC_API_BASE": API_BASE,
                "MODAL_WEB_BUILD": "1",
                "NEXT_TELEMETRY_DISABLED": "1",
            }
        )
        .run_commands("bash /build_web.sh")
    )

app = modal.App("llm-twin-academy-web", image=image)

min_containers = int(os.environ.get("MODAL_MIN_CONTAINERS", "0"))
max_containers = int(os.environ.get("MODAL_MAX_CONTAINERS", "1"))


@app.function(
    secrets=[modal.Secret.from_name("academy-env", required_keys=[])],
    min_containers=min_containers,
    max_containers=max_containers,
    scaledown_window=300,
)
@modal.web_server(port=3000, startup_timeout=120)
def web():
    import os as _os
    import subprocess
    from pathlib import Path as P

    # Next.js binds to HOSTNAME; Modal containers already set this to a
    # non-routable name, so setdefault() would leave the server unreachable.
    _os.environ["PORT"] = "3000"
    _os.environ["HOSTNAME"] = "0.0.0.0"
    _os.environ.setdefault("NODE_ENV", "production")
    root = P("/web/.next/standalone")
    candidates = [root / "server.js", root / "apps" / "web" / "server.js"]
    server = next((p for p in candidates if p.exists()), root / "server.js")
    if not server.exists():
        raise FileNotFoundError(f"Next standalone server missing at {server}")
    # Keep the Modal worker process alive; execvp drops the HTTP proxy.
    subprocess.Popen(["node", str(server)], cwd=str(server.parent))
