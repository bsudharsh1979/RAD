from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TutorRequest:
    messages: list[dict[str, str]]
    mode: str
    depth: str
    system: str
    max_tokens: int = 700


@dataclass
class TutorResponse:
    text: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0
    ttft_ms: float | None = None
    tpot_ms: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class TutorModelProvider(ABC):
    name: str

    @abstractmethod
    def available(self) -> bool: ...

    @abstractmethod
    def generate(self, req: TutorRequest) -> TutorResponse: ...


class VoiceProvider(ABC):
    name: str

    @abstractmethod
    def available(self) -> bool: ...

    def tts(self, text: str, language: str = "en") -> bytes:
        raise NotImplementedError

    def transcribe(self, audio: bytes) -> str:
        raise NotImplementedError
