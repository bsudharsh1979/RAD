"""NVIDIA NIM HTTP payload must match integrate.api.nvidia.com, not the OpenAI SDK."""

from __future__ import annotations

from app.config import settings
from app.domains.providers.base import TutorRequest
from app.domains.providers.nim import NvidiaNIMProvider


class _Resp:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "choices": [{"message": {"content": "What's happening — the pipeline fills [MASK]."}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 8},
        }


class _Client:
    last = None

    def __init__(self, *a, **k):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def post(self, url, json=None, headers=None):
        _Client.last = {"url": url, "json": json, "headers": headers}
        return _Resp()


def test_nim_payload_uses_top_level_chat_template_kwargs(monkeypatch):
    monkeypatch.setattr(settings, "nim_base_url", "https://integrate.api.nvidia.com/v1")
    monkeypatch.setattr(settings, "nvidia_api_key", "nvapi-test")
    monkeypatch.setattr(settings, "nvidia_nim_model", "nvidia/nemotron-3.5-lightning-30b-a3b")
    import app.domains.providers.nim as nim

    monkeypatch.setattr(nim.httpx, "Client", _Client)
    out = NvidiaNIMProvider().generate(
        TutorRequest(
            messages=[{"role": "user", "content": "What happens at [MASK]?"}],
            mode="COURSE",
            depth="ENGINEER",
            system="Teach the mechanism.",
        )
    )
    assert out.text.startswith("What's happening")
    payload = _Client.last["json"]
    assert "extra_body" not in payload
    assert payload["chat_template_kwargs"] == {"enable_thinking": False}
    assert payload["model"] == "nvidia/nemotron-3.5-lightning-30b-a3b"
    assert _Client.last["url"].endswith("/chat/completions")
    assert _Client.last["headers"]["Authorization"] == "Bearer nvapi-test"
