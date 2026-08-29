from __future__ import annotations

import time

import httpx

from app.config import settings
from app.domains.providers.base import TutorModelProvider, TutorRequest, TutorResponse


class NvidiaNIMProvider(TutorModelProvider):
    name = "nvidia_nim"

    def available(self) -> bool:
        return bool(settings.nim_base_url and settings.nvidia_api_key)

    def generate(self, req: TutorRequest) -> TutorResponse:
        if not self.available():
            raise RuntimeError("NVIDIA NIM is not configured")
        t0 = time.perf_counter()
        url = settings.nim_base_url.rstrip("/") + "/chat/completions"
        messages = [{"role": "system", "content": req.system}] + req.messages
        headers = {
            "Authorization": f"Bearer {settings.nvidia_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.nvidia_nim_model,
            "messages": messages,
            "max_tokens": req.max_tokens,
            "temperature": 0.2,
            "extra_body": {"chat_template_kwargs": {"enable_thinking": False}},
        }
        with httpx.Client(timeout=180.0) as client:
            r = client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        # Never show chain-of-thought / reasoning_content to the learner.
        text = (msg.get("content") or "").strip()
        usage = data.get("usage") or {}
        ms = (time.perf_counter() - t0) * 1000
        return TutorResponse(
            text=text,
            model=settings.nvidia_nim_model,
            provider=self.name,
            input_tokens=int(usage.get("prompt_tokens") or 0),
            output_tokens=int(usage.get("completion_tokens") or 0),
            latency_ms=ms,
        )
