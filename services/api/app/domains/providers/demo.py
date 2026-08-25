from __future__ import annotations

import time

from app.domains.providers.base import TutorModelProvider, TutorRequest, TutorResponse


class DemoProvider(TutorModelProvider):
    name = "demo"

    def available(self) -> bool:
        return True

    def generate(self, req: TutorRequest) -> TutorResponse:
        t0 = time.perf_counter()
        user = next((m["content"] for m in reversed(req.messages) if m["role"] == "user"), "")
        text = (
            "COURSE MODE — Demo tutor (no paid API).\n\n"
            "I only restated retrieved NVIDIA notebook spans plus labeled interpretation. "
            "If a fact is missing from those spans I must say so.\n\n"
            f"Your ask: {user[:400]}\n"
        )
        # The real tutor service prepends retrieved evidence; this provider is a last resort.
        ms = (time.perf_counter() - t0) * 1000
        return TutorResponse(
            text=text,
            model="demo-grounded",
            provider=self.name,
            input_tokens=len(req.system.split()),
            output_tokens=len(text.split()),
            latency_ms=ms,
        )
