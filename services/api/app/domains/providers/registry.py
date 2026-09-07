from __future__ import annotations

from app.config import settings
from app.domains.providers.base import VoiceProvider
from app.domains.providers.demo import DemoProvider
from app.domains.providers.huggingface import HuggingFaceProvider
from app.domains.providers.nim import NvidiaNIMProvider
from app.domains.providers.openai_provider import OpenAIProvider

PROVIDERS = {
    DemoProvider.name: DemoProvider(),
    OpenAIProvider.name: OpenAIProvider(),
    NvidiaNIMProvider.name: NvidiaNIMProvider(),
    HuggingFaceProvider.name: HuggingFaceProvider(),
}


def get_provider(name: str | None):
    key = (name or DemoProvider.name).lower()
    p = PROVIDERS.get(key) or PROVIDERS[DemoProvider.name]
    if not p.available():
        return PROVIDERS[DemoProvider.name], True
    return p, False


class ElevenLabsVoiceProvider(VoiceProvider):
    name = "elevenlabs"

    def available(self) -> bool:
        return bool(settings.elevenlabs_api_key)


class SarvamVoiceProvider(VoiceProvider):
    name = "sarvam"

    def available(self) -> bool:
        return bool(settings.sarvam_api_key)


class OpenAIRealtimeVoiceProvider(VoiceProvider):
    name = "openai_realtime"

    def available(self) -> bool:
        return bool(settings.openai_api_key)


VOICE = {
    ElevenLabsVoiceProvider.name: ElevenLabsVoiceProvider(),
    SarvamVoiceProvider.name: SarvamVoiceProvider(),
    OpenAIRealtimeVoiceProvider.name: OpenAIRealtimeVoiceProvider(),
}


class PerplexityResearchProvider:
    name = "perplexity"

    def available(self) -> bool:
        return bool(settings.perplexity_api_key)

    def search(self, query: str) -> dict:
        if not self.available():
            return {"error": "Perplexity not configured", "citations": []}
        import httpx

        headers = {
            "Authorization": f"Bearer {settings.perplexity_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "sonar",
            "messages": [{"role": "user", "content": query}],
        }
        with httpx.Client(timeout=45.0) as client:
            r = client.post("https://api.perplexity.ai/chat/completions", json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
        text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
        return {"text": text, "citations": data.get("citations") or [], "raw": {"id": data.get("id")}}
