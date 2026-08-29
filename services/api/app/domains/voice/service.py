"""TTS/STT adapters. clip=false must never shorten text."""

from __future__ import annotations

import base64

import httpx

from app.config import settings
from app.domains.walkthrough.speech import clip_text

DEFAULT_ELEVEN_VOICE = "21m00Tcm4TlvDq8ikWAM"


def voice_status() -> dict:
    return {
        "elevenlabs": "connected" if settings.elevenlabs_api_key else "not_configured",
        "sarvam": "connected" if settings.sarvam_api_key else "not_configured",
        "browser_fallback": "available",
        "note": "ElevenLabs is used when configured. clip=false never shortens text. Browser speechSynthesis is the zero-key path.",
    }


def synthesize(text: str, *, provider: str = "auto", language: str = "en", clip: bool = False) -> dict:
    spoken = clip_text(text, clip=clip)
    chosen = provider
    if provider == "auto":
        if settings.elevenlabs_api_key:
            chosen = "elevenlabs"
        elif settings.sarvam_api_key:
            chosen = "sarvam"
        else:
            chosen = "browser"
    if chosen == "elevenlabs" and not settings.elevenlabs_api_key:
        chosen = "browser"
        reason = "ElevenLabs not configured — browser fallback"
    elif chosen == "sarvam" and not settings.sarvam_api_key:
        chosen = "browser"
        reason = "Sarvam not configured — browser fallback"
    else:
        reason = None
    audio_b64 = None
    if chosen == "elevenlabs" and settings.elevenlabs_api_key:
        audio_b64, reason = _elevenlabs(spoken, language=language)
        if not audio_b64:
            chosen = "browser"
    return {
        "ok": True,
        "provider": chosen,
        "language": language,
        "clip": clip,
        "char_count": len(spoken),
        "input_char_count": len(text),
        "truncated": len(spoken) < len(text),
        "text": spoken,
        "audio_b64": audio_b64,
        "mime": "audio/mpeg" if audio_b64 else None,
        "reason": reason
        or (
            "ElevenLabs narration"
            if chosen == "elevenlabs"
            else "Use browser speechSynthesis."
        ),
        "elevenlabs_tune": {"stability": 0.55, "speed": 0.93} if chosen == "elevenlabs" else None,
    }


def _elevenlabs(text: str, *, language: str) -> tuple[str | None, str | None]:
    voice = settings.elevenlabs_voice_id or DEFAULT_ELEVEN_VOICE
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
    headers = {
        "xi-api-key": settings.elevenlabs_api_key or "",
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2" if language and language != "en" else "eleven_turbo_v2_5",
        "voice_settings": {"stability": 0.55, "similarity_boost": 0.7, "speed": 0.93},
    }
    try:
        with httpx.Client(timeout=90.0) as client:
            r = client.post(url, json=payload, headers=headers)
            if r.status_code >= 400:
                return None, f"ElevenLabs HTTP {r.status_code} — browser fallback"
            return base64.b64encode(r.content).decode("ascii"), None
    except Exception as exc:  # noqa: BLE001
        return None, f"ElevenLabs error ({type(exc).__name__}) — browser fallback"


def transcribe_stub(note: str = "") -> dict:
    return {
        "ok": False,
        "text": "",
        "reason": "Server STT is optional. Use the Web Speech API in the browser.",
        "note": note,
    }
