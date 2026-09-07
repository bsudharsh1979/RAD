# Voice architecture

`VoiceProvider` with ElevenLabs, Sarvam, OpenAI Realtime. Default: none.

Interruption: client sets `interrupt: true` on `/api/voice/tts`; in-flight TTS must cancel. Transcripts persist as tutor messages when wired.

Sarvam is for Indian English / Indic + keep NVIDIA terms in English. Not required at startup.
