from __future__ import annotations

import time

import httpx

from app.config import settings
from app.domains.providers.base import TutorModelProvider, TutorRequest, TutorResponse


class HuggingFaceProvider(TutorModelProvider):
    """Optional. This course is HuggingFace-centric; not required at startup."""

    name = "huggingface"

    def available(self) -> bool:
        return bool(settings.huggingface_api_key)

    def generate(self, req: TutorRequest) -> TutorResponse:
        if not self.available():
            raise RuntimeError("HuggingFace Inference is not configured")
        t0 = time.perf_counter()
        prompt = req.system + "\n\n" + "\n".join(f"{m['role']}: {m['content']}" for m in req.messages)
        url = f"https://api-inference.huggingface.co/models/{settings.huggingface_model}"
        headers = {"Authorization": f"Bearer {settings.huggingface_api_key}"}
        with httpx.Client(timeout=90.0) as client:
            r = client.post(url, headers=headers, json={"inputs": prompt, "parameters": {"max_new_tokens": req.max_tokens}})
            r.raise_for_status()
            data = r.json()
        if isinstance(data, list) and data:
            text = data[0].get("generated_text", str(data[0]))
        else:
            text = str(data)
        ms = (time.perf_counter() - t0) * 1000
        return TutorResponse(
            text=text[-4000:],
            model=settings.huggingface_model,
            provider=self.name,
            input_tokens=len(prompt.split()),
            output_tokens=len(text.split()),
            latency_ms=ms,
        )
