# Omniverse repository analysis

## Finding

This GitHub repository (`bsudharsh1979/RAD`) contains **only** NVIDIA DLI Jupyter notebooks for Rapid Application Development using LLMs. There is:

- no Kit application
- no `exts/` tree
- no OpenUSD stages
- no Omniverse streaming client
- no existing digital-twin simulation engine

The master specification assumed an existing twin under `/integrations/omniverse-twin`. That path did not exist. We created a **bridge contract and Kit stub**, not a fake 3D product.

## Integration strategy (do not rebuild a Kit app)

```text
Web Application
      │
      │ WebSocket / REST
      ▼
TwinStateEngine  (canonical JSON; evidence_type always set)
      │
      ├──── Web 2D / 3D-lite twins (this product’s daily experience)
      │
      └──── Omniverse Bridge  (optional)
                    │
                    ▼
             Omniverse Kit / OpenUSD  (future / external repo)
```

The web twins **must** remain usable when Omniverse is offline. Core learning never requires Kit, NVCF, or a GPU.

## Visual language (when a Kit scene is later attached)

Every object must teach a RAD-LLM concept:

| Visual | Teaches |
| --- | --- |
| Request packet | HuggingFace pipeline input string |
| Tokenizer station | string → `input_ids` |
| Embedding slabs | word + position + type **addition** |
| Attention lattice | Q/K/V and residual token identity |
| Encoder vs decoder volumes | bidirectional vs causal, encoder-decoder vs decoder-only |
| Cross-attention ribbon | T5 / Whisper / captioning context injection |
| KV tape on decoder | `past_key_values` growth (notebook 4) |
| Memory buffer tank | LangChain conversation buffer vs summary |
| Tool sockets | agent tools; Python REPL marked unsafe |
| Quantization compression | FP16 vs GPTQ memory, not “always better quality” |

## Files in this repo

| Path | Role |
| --- | --- |
| `integrations/omniverse-twin/` | Protocol, sample USD comments, Kit extension stub |
| `services/omniverse-bridge/` | FastAPI/WebSocket relay of `TwinState` |
| `deploy/nvidia/` | NVCF / streaming notes — separate from web deploy |

## Changes required if an external Kit repo is later vendored

1. Map `TwinState.scenario` to a USD prim path.
2. Drive utilization / queue attributes from the same JSON the web twin uses.
3. Do not fork simulation formulas into Kit Python.
4. Stream via Omniverse Streaming / NVCF only in `deploy/nvidia`.
