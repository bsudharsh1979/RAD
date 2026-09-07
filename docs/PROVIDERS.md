# Providers

`TutorModelProvider`: demo, openai, nvidia_nim, huggingface.

Failures are disclosed. No silent failover without a banner.

Embeddings: deterministic hash vectors offline; swap-in OpenAI/NIM later via the same cache keys (`sha256` of source).
