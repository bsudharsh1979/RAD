# Architecture

LLM Twin Academy is a **course-agnostic digital-twin learning engine** whose first packed course is NVIDIA DLI RAD-LLM.

## Domains

`course`, `retrieval`, `tutor`, `mastery`, `questions`, `review`, `experiments`, `twins`, `providers`, `voice`, `research`, `observability`

## Canonical twin state

`services/api/app/domains/twins/engine.py` is the only simulation implementation. Web and Omniverse consume the same JSON. `evidence_type` is mandatory.

## Multi-course

`Course` / `SourceArtifact` are not hardcoded to NVIDIA forever. Seed data is the RAD-LLM pack. Enterprise SSO/billing are extension points only.
