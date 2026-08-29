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

_BUILD = r"""
set -euo pipefail
if [ -z "${NEXT_PUBLIC_API_BASE:-}" ]; then
  echo "NEXT_PUBLIC_API_BASE must be set to bake the Next standalone build." >&2
  echo "Deploy the API first, then:" >&2
  echo "  NEXT_PUBLIC_API_BASE=<api URL> MODAL_MIN_CONTAINERS=0 modal deploy deploy/modal/modal_web.py" >&2
  exit 1
fi
cd /web
npm ci
export MODAL_WEB_BUILD=1 NEXT_TELEMETRY_DISABLED=1
npm run build
mkdir -p /web/.next/standalone/.next
cp -a /web/.next/static /web/.next/standalone/.next/static
if [ -d /web/public ]; then cp -a /web/public /web/.next/standalone/public; fi
"""

image = modal.Image.from_registry("node:22-bookworm-slim", add_python="3.12").run_commands(
    "apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*"
)
if ROOT is not None:
    image = (
        image.add_local_dir(str(ROOT / "apps" / "web"), remote_path="/web", copy=True)
        .env(
            {
                "NEXT_PUBLIC_API_BASE": API_BASE,
                "MODAL_WEB_BUILD": "1",
                "NEXT_TELEMETRY_DISABLED": "1",
            }
        )
        .run_commands(_BUILD)
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
@modal.concurrent(max_inputs=100)
@modal.web_server(port=3000)
def web():
    import os as _os
    from pathlib import Path as P

    _os.environ.setdefault("PORT", "3000")
    _os.environ.setdefault("HOSTNAME", "0.0.0.0")
    root = P("/web/.next/standalone")
    candidates = [root / "server.js", root / "apps" / "web" / "server.js"]
    server = next((p for p in candidates if p.exists()), root / "server.js")
    _os.chdir(str(server.parent))
    _os.execvp("node", ["node", str(server)])
