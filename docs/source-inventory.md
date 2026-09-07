# Source Inventory — NVIDIA DLI RAD (LLMs)

This repository is **not** the NVIDIA “Deploying and Optimizing AI Inference at Scale” course.
It is the NVIDIA Deep Learning Institute workshop:

**Rapid Application Development Using Large Language Models (LLMs)**

Official outline: [NVIDIA instructor-led workshop](https://www.nvidia.com/en-gb/training/instructor-led-workshops/rapid-application-development-using-large-language-models/).

Technologies named by NVIDIA: Python, PyTorch, HuggingFace, transformers, LangChain, LlamaIndex.

## Discovery method

Ingestion is filename-agnostic. On startup the platform recursively scans `course-materials/` for:

| Kind | Extensions |
| --- | --- |
| Jupyter | `.ipynb` |
| PDF | `.pdf` |
| PowerPoint | `.ppt`, `.pptx` |
| Markdown / text | `.md`, `.txt` |

No PDF or PPT was present in the original repository. Eight notebooks were present at the repository root and were moved to `course-materials/notebooks/`.

**Stored notebook outputs:** none. Every code cell is educational content. Pipeline results shown in the academy are labeled `EXPECTED_RESULT` unless a learner imports an `ACTUAL_RUN`.

**Automatic execution:** never. Notebooks contain `nvidia-smi`, kernel shutdown, `exec()`, and HuggingFace model loads. Those are treated as data.

## Notebook inventory

| Order | File | Title | MD | Code | Stored outputs | Models / pipelines named in source |
| --- | --- | --- | ---: | ---: | --- | --- |
| 1 | `01_llm_intro.ipynb` | Getting Started With Large Language Models | 21 | 4 | no | `bert-base-uncased`, `fill-mask` |
| 2 | `02_llm_intake.ipynb` | LLM Architecture Intuitions | 23 | 13 | no | `bert-base-uncased` |
| 3 | `03_encoder_task.ipynb` | LLM Encoder Tasks | 20 | 6 | no | `bert-base-uncased`, `deepset/roberta-base-squad2`, `SamLowe/roberta-base-go_emotions`, `facebook/bart-large-mnli` (task) |
| 4 | `04_seq2seq.ipynb` | Encoder-Decoders for Seq2Seq | 25 | 16 | no | `t5-base`, `t5-large`, `google/flan-t5-large` |
| 5 | `05_multimodal.ipynb` | Transformers for Multimodal Reasoning | 30 | 13 | no | Whisper base/large-v2, ViT-GPT2, BLIP, CLIP |
| 6 | `06_textgen.ipynb` | Large General Decoder Models | 28 | 17 | no | GPT-2, CodeGen, `TheBloke/Llama-2-13B-chat-GPTQ` |
| 7 | `07_stateful_models.ipynb` | Introduction To Stateful LLMs | 36 | 20 | no | Llama-2 GPTQ 13B/70B, LangChain |
| 8 | `08_assessment.ipynb` | Course Assessment | 26 | 8 | no | BLIP, go_emotions, BART-MNLI, ToxicityModel |

Referenced but **not in this repository** (course environment extras):

- `extras_and_licenses/99_licenses.ipynb`
- `extras_and_licenses/forward_listener.py`
- `extras_and_licenses/99_llama_index.ipynb`
- `extras_and_licenses/99_agent_explore.ipynb`
- `imgs/*` (slide diagrams referenced by markdown)
- `audio-files/*`, `img-files/*`
- `solutions/` directory mentioned in notebook 7

The academy records these as **missing source assets** rather than inventing their contents.

## Course progression (source-aligned)

1. HuggingFace pipelines, tokenizer + model, compute environment.
2. Tokens, embeddings (word / position / type), self-attention, BERT encoder.
3. Token heads, span QA, sequence classification, zero-shot via multi-query.
4. T5 encoder–decoder, cross-attention, Flan-T5, prompt engineering.
5. Modalities, Whisper ASR, ViT captioning, BLIP, CLIP retrieval.
6. Decoder-only GPT, CodeGen pitfalls, Llama-2, quantization, chat templates.
7. LangChain chains, memory, RAG vs agents, ReAct, tool danger (Python REPL).
8. Custom agent: memory + image + code + toxicity + emotion (pass 3 of 5).

## Omniverse

No Omniverse / OpenUSD / Kit application was present in this repository. See `docs/omniverse-repo-analysis.md`.

## Evidence implications

- Course prose → `COURSE_SOURCE`
- “This pipeline would return …” without stored output → `EXPECTED_RESULT`
- Twin numbers → `SIMULATED_RESULT`
- Imported AIPerf/JSON/logs → `ACTUAL_RUN`
- Tutor synthesis → `TUTOR_INTERPRETATION`
- Research mode / Perplexity → `EXTERNAL_RESEARCH`
