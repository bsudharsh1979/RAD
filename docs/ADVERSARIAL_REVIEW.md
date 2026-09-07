# Adversarial review (this iteration)

Independent pass against the master spec, adapted to **NVIDIA DLI RAD-LLM** (not inference-at-scale).

## Critical / High — fixed

| Finding | Fix |
| --- | --- |
| Diagnostic / practice finished on “Loading…” after the last item | Completion screen with heatmap + 30-minute plan; `POST /api/diagnostic/complete` |
| Twin visuals were a generic three-box SVG for every scenario | Scenario-specific TwinViz for all 11 course twins |
| Assessment page listed questions and leaked no design loop | 8-step arena + `POST /api/assessment/defend` grades reasoning |
| Review due list was not answerable | In-page FSRS attempt flow |
| Experiments lacked run IDs / explainer / confounder UI | List includes `latest_run_id`; compare + explain |
| Light mode left dark panels | CSS variables for panel/background |
| Notebook source links dropped cell index | `notebookHref` + `?cell=` |
| Notes/bookmarks API unused | NotesBar on lessons, twins, notebooks, concept map |
| Voice toggle did nothing | Browser speech + barge-in; paid TTS still opt-in |

## Remaining limitations (not faked)

- No Omniverse Kit/USD in this repository — bridge + protocol only
- No PDF/PPT in source tree — ingestors exist
- Hash embeddings, not a learned encoder
- Demo tutor is retrieval + templates unless a key is configured
- Playwright browsers are not installed in every environment
- Docker Compose unverified where Docker is absent
