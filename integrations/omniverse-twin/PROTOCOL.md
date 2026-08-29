# TwinState protocol (shared with web)

Every payload MUST include `evidence_type`. Simulations use `SIMULATED_RESULT`.

Map `scenario` to a USD prim, e.g.:

- `pipeline-flow` → `/World/Pipeline`
- `seq2seq-t5` → `/World/T5`
- `rag-agent` → `/World/AgentLoop`
- `assessment-agent` → `/World/Assessment`

Never reimplement metrics in Kit. Subscribe to `services/omniverse-bridge` WebSocket `/ws`.
