from __future__ import annotations

import time
from typing import Any

import httpx

from app.config import settings
from app.domains.providers.base import TutorModelProvider, TutorRequest, TutorResponse


class OpenAIProvider(TutorModelProvider):
    name = "openai"

    def available(self) -> bool:
        return bool(settings.openai_api_key)

    def generate(self, req: TutorRequest) -> TutorResponse:
        if not self.available():
            raise RuntimeError("OpenAI is not configured")
        t0 = time.perf_counter()
        payload: dict[str, Any] = {
            "model": settings.openai_model,
            "input": [{"role": "system", "content": req.system}]
            + [{"role": m["role"], "content": m["content"]} for m in req.messages],
        }
        headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
        with httpx.Client(timeout=60.0) as client:
            r = client.post("https://api.openai.com/v1/responses", json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
        text = _extract_openai_text(data)
        usage = data.get("usage") or {}
        ms = (time.perf_counter() - t0) * 1000
        return TutorResponse(
            text=text,
            model=settings.openai_model,
            provider=self.name,
            input_tokens=int(usage.get("input_tokens") or 0),
            output_tokens=int(usage.get("output_tokens") or 0),
            latency_ms=ms,
            extra={"raw_id": data.get("id")},
        )


def _extract_openai_text(data: dict[str, Any]) -> str:
    if "output_text" in data and data["output_text"]:
        return str(data["output_text"])
    chunks: list[str] = []
    for item in data.get("output") or []:
        for c in item.get("content") or []:
            if c.get("type") in ("output_text", "text") and c.get("text"):
                chunks.append(c["text"])
    return "\n".join(chunks) or str(data)[:2000]
