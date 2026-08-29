"""TTS/STT adapters. clip=false must never shorten text."""

from __future__ import annotations

from app.config import settings
from app.domains.walkthrough.speech import clip_text


def voice_status() -> dict:
    return {
        "elevenlabs": "connected" if settings.elevenlabs_api_key else "not_configured",
        "sarvam": "connected" if settings.sarvam_api_key else "not_configured",
        "browser_fallback": "available",
        "note": "Paid TTS is not fetched unless explicitly requested. Browser speechSynthesis is the zero-key path.",
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
    return {
        "ok": True,
        "provider": chosen,
        "language": language,
        "clip": clip,
        "char_count": len(spoken),
        "input_char_count": len(text),
        "truncated": len(spoken) < len(text),
        "text": spoken,
        "audio_b64": None,
        "reason": reason
        or (
            "Keys present but TTS bytes are not fetched in demo to avoid surprise cost."
            if chosen in ("elevenlabs", "sarvam")
            else "Use browser speechSynthesis."
        ),
        "elevenlabs_tune": {"stability": 0.55, "speed": 0.93} if chosen == "elevenlabs" else None,
    }


def transcribe_stub(note: str = "") -> dict:
    return {
        "ok": False,
        "text": "",
        "reason": "Server STT is optional. Use the Web Speech API in the browser.",
        "note": note,
    }
