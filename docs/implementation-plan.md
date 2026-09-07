# Implementation plan — LLM Twin Academy

## Product

**LLM Twin Academy** — a digital-twin technical learning platform whose first course is NVIDIA DLI **Rapid Application Development Using Large Language Models**.

The original “Inference Twin Academy” prompt was rewritten onto **this** curriculum: pipelines, encoders, seq2seq, multimodal, decoder chat models, quantization, LangChain, RAG, agents, assessment.

## What we will not fake

- NVIDIA inference-at-scale (NIM Operator, KEDA, Dynamo, Grove) is **out of scope** for this course’s source graph. Those terms may appear only in Research Mode as `EXTERNAL_RESEARCH`.
- Notebook cells are **not executed**.
- Simulations are never labeled `ACTUAL_RUN`.
- Missing extras (`imgs/`, licenses notebook) are disclosed.

## Architecture

- `apps/web` — Next.js App Router, TypeScript, Tailwind.
- `services/api` — FastAPI domains listed in the spec.
- `services/twin-engine` — imported by the API; same `TwinState` schema.
- `services/omniverse-bridge` — optional WebSocket relay.
- SQLite by default (five-minute local launch). PostgreSQL + pgvector via Docker Compose.
- Demo tutor works **without any paid API**. First-run asks which APIs the learner wants.

## Phases (executed in this PR, not left as TODOs)

1. Ingest notebooks with provenance.
2. Seed concept graph, misconceptions, FSRS, diagnostic, 650+ questions.
3. Tutor Course / Research modes + provider abstraction (Demo, OpenAI, NIM, HuggingFace).
4. Notebook Studio for all eight notebooks.
5. Ten web twins + assessment arena.
6. Experiment importer + comparison workbench.
7. Voice provider interfaces (optional).
8. Omniverse bridge stub.
9. Tests (pytest + Playwright) and docs.

## Defaults

- Tutor engine default: **Demo (offline)**. Learner is asked which APIs to enable.
- Voice default: **off**.
- Research / Perplexity: **off** until Research Mode is explicitly enabled.
