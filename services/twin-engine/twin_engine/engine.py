"""Canonical TwinStateEngine — web and Omniverse consume the same JSON."""

from __future__ import annotations

import math
from typing import Any

EVIDENCE = "SIMULATED_RESULT"

DISCLAIMER = (
    "Educational simulation grounded in course qualitative behavior. "
    "Not a measurement. Not a substitute for executing the notebook on GPU."
)


def _clamp(x: float, lo: float, hi: float) -> float:
    if math.isnan(x) or math.isinf(x):
        return lo
    return max(lo, min(hi, x))


def _finite(x: float, fallback: float = 0.0) -> float:
    if x is None or math.isnan(x) or math.isinf(x):
        return fallback
    return x


def sanitize(state: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in state.items():
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            v = float(v)
            if math.isnan(v) or math.isinf(v):
                v = 0.0
            if "util" in k or "rate" in k or "hit" in k:
                v = _clamp(v, 0.0, 1.0)
            if "ms" in k or "latency" in k or "tokens" in k or "memory" in k:
                v = max(0.0, v)
        out[k] = v
    out.setdefault("evidence_type", EVIDENCE)
    if out.get("evidence_type") == "ACTUAL_RUN":
        # Twin engine is unable to emit measured runs.
        out["evidence_type"] = EVIDENCE
        out["evidence_coerced"] = True
    out.setdefault("disclaimer", DISCLAIMER)
    return out


def run(scenario: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    params = dict(params or {})
    fn = SCENARIOS.get(scenario)
    if not fn:
        raise KeyError(f"Unknown twin scenario: {scenario}")
    return sanitize(fn(params))


def pipeline_flow(p: dict[str, Any]) -> dict[str, Any]:
    text = str(p.get("text", "Hello I'm a [MASK] model."))
    tokens = max(1, int(p.get("n_tokens", max(4, len(text.split()) + 2))))
    vocab = 30522
    hidden = 768
    preprocess_ms = 0.4 + 0.05 * tokens
    forward_ms = 4.0 + 0.35 * tokens
    postprocess_ms = 0.8
    return {
        "scenario": "pipeline-flow",
        "stages": ["human_string", "preprocess", "forward", "postprocess", "human_output"],
        "text": text,
        "n_tokens": tokens,
        "includes_mask": "[MASK]" in text or "[mask]" in text,
        "vocab_size": vocab,
        "hidden_size": hidden,
        "preprocess_ms": round(preprocess_ms, 2),
        "forward_ms": round(forward_ms, 2),
        "postprocess_ms": round(postprocess_ms, 2),
        "total_ms": round(preprocess_ms + forward_ms + postprocess_ms, 2),
        "components": ["tokenizer", "model"],
        "teaching": (
            "Notebook 1: FillMaskPipeline is tokenizer preprocess + model forward + "
            "task-specific postprocess. Tensors stay hidden from the typical user."
        ),
        "source": {"file": "01_llm_intro.ipynb", "cell_index": 14},
    }


def tokenizer_embeddings(p: dict[str, Any]) -> dict[str, Any]:
    requested = max(1, int(p.get("seq_len", 12)))
    seq = min(512, requested)
    use_type = bool(p.get("sentence_pair", False))
    dim = 768
    vocab = 30522
    pos_slots = 512
    bytes_f32 = seq * dim * 4
    return {
        "scenario": "tokenizer-embeddings",
        "seq_len": seq,
        "requested_seq_len": requested,
        "over_limit": requested > 512,
        "input_ids": list(range(seq)),
        "token_type_ids": ([0] * (seq // 2) + [1] * (seq - seq // 2)) if use_type else [0] * seq,
        "word_table": [vocab, dim],
        "position_table": [pos_slots, dim],
        "type_table": [2, dim],
        "combine": "addition",
        "formula": "embed = WordEmbed[token] + PosEmbed[pos] + TypeEmbed[type]",
        "embedding_bytes_f32": bytes_f32,
        "cls_sep_note": "Notebook 2 strips CLS/SEP only for word-embedding illustration.",
        "teaching": (
            "BERT positions are learned embeddings over 512 slots, not the original "
            "sinusoidal encodings from Attention Is All You Need."
        ),
        "source": {"file": "02_llm_intake.ipynb", "cell_index": 21},
    }


def attention_encoder(p: dict[str, Any]) -> dict[str, Any]:
    seq = max(1, min(128, int(p.get("seq_len", 10))))
    heads = 12
    layers = 12
    d_model = 768
    d_head = d_model // heads
    attn_elems = seq * seq * heads
    residual = bool(p.get("residual", True))
    masked = bool(p.get("apply_padding_mask", False))
    compute = seq * seq * d_model * layers
    return {
        "scenario": "attention-encoder",
        "seq_len": seq,
        "heads": heads,
        "layers": layers,
        "d_model": d_model,
        "d_head": d_head,
        "attention_matrix_shape": [seq, seq],
        "head_count_total": heads * layers,
        "attn_elems": attn_elems,
        "mlp_path": "768 → 768 → 3072 → 768",
        "residual": residual,
        "padding_mask": masked,
        "approx_qk_v_ops": compute,
        "teaching": (
            "Self-attention: Q, K, V from the same sequence. Softmax(QK^T/√d_k)V. "
            "12 heads of 64-d concatenated back to 768. Residuals keep token identity."
        ),
        "source": {"file": "02_llm_intake.ipynb", "cell_index": 27},
    }


def encoder_heads(p: dict[str, Any]) -> dict[str, Any]:
    mode = str(p.get("mode", "mlm"))
    seq = max(2, min(128, int(p.get("seq_len", 16))))
    n_classes = max(2, int(p.get("n_classes", 4)))
    if mode == "mlm":
        out_shape = [seq, 30522]
        restriction = "Predict a token at each position (often only [MASK] is read)."
        novel = False
    elif mode == "qa":
        out_shape = [seq, 2]
        restriction = "Answer MUST be a substring of the context (start/end logits)."
        novel = False
    elif mode == "sequence":
        out_shape = [1, 28]
        restriction = "Uses a single pooled position (often index 0 / CLS)."
        novel = False
    else:
        out_shape = [n_classes, 1]
        restriction = "One encoder query per candidate class (zero-shot multi-query)."
        novel = False
    return {
        "scenario": "encoder-heads",
        "mode": mode,
        "seq_len": seq,
        "output_shape": out_shape,
        "n_forward_passes": n_classes if mode == "zero_shot" else 1,
        "can_emit_novel_tokens": novel,
        "restriction": restriction,
        "models": {
            "mlm": "bert-base-uncased FillMask",
            "qa": "deepset/roberta-base-squad2",
            "sequence": "SamLowe/roberta-base-go_emotions",
            "zero_shot": "facebook/bart-large-mnli (task notebook)",
        }.get(mode, ""),
        "teaching": (
            "Notebook 3: encoder body is n→n latent sequence. Heads change granularity. "
            "Zero-shot breaks n→1 by querying multiple times."
        ),
        "source": {"file": "03_encoder_task.ipynb", "cell_index": 23},
    }


def seq2seq_t5(p: dict[str, Any]) -> dict[str, Any]:
    isl = max(1, int(p.get("input_tokens", 12)))
    osl = max(1, int(p.get("output_tokens", 8)))
    model = str(p.get("model", "t5-base"))
    params = {"t5-base": 222_903_552, "t5-large": 737_000_000, "flan-t5-large": 783_000_000}.get(
        model, 222_903_552
    )
    encoder_calls = 1
    decoder_calls = osl
    kv_growth = [isl * step for step in range(1, osl + 1)]
    instruction_following = 0.35 if model.startswith("t5") and "flan" not in model else 0.8
    pig_latin_ok = False
    return {
        "scenario": "seq2seq-t5",
        "model": model,
        "parameters": params,
        "input_tokens": isl,
        "output_tokens": osl,
        "encoder_calls": encoder_calls,
        "decoder_calls": decoder_calls,
        "cross_attention_shape": [osl, isl],
        "past_key_values_grows": True,
        "kv_steps": kv_growth[-1],
        "instruction_following_qualitative": round(_clamp(instruction_following, 0, 1), 2),
        "pig_latin_expected_fail": True,
        "pig_latin_ok": pig_latin_ok,
        "start_token_note": "Notebook 4: first decoder step often from <pad>, stop at </s>.",
        "teaching": (
            "Encoder runs once (stable context). Decoder emits one token at a time. "
            "Flan-T5 is trained for instruction following; vanilla T5 is not a general chatbot. "
            "Pig Latin is expected to fail due to tokenization/semantics — course says so."
        ),
        "source": {"file": "04_seq2seq.ipynb", "cell_index": 18},
    }


def multimodal(p: dict[str, Any]) -> dict[str, Any]:
    kind = str(p.get("kind", "whisper"))
    seconds = _clamp(float(p.get("audio_seconds", 8)), 0.1, 120)
    whisper_params = 73_000_000 if p.get("whisper_size", "base") == "base" else 1_550_000_000
    frames = int(seconds * 50)
    caption_quality = 0.35 if p.get("caption_model", "vit-gpt2") == "vit-gpt2" else 0.7
    clip_diag = 0.62
    return {
        "scenario": "multimodal",
        "kind": kind,
        "audio_seconds": seconds,
        "spectrogram_frames": frames,
        "whisper_parameters": whisper_params,
        "whisper_memory_gb_base_note": "~73M params for whisper-base (notebook print cell)",
        "vit_patch_logic": "An Image is Worth 16x16 Words — patches become tokens",
        "caption_model": p.get("caption_model", "vit-gpt2"),
        "caption_quality_qualitative": caption_quality,
        "clip_softmax_diag_qualitative": clip_diag,
        "conditional_prefix": str(p.get("prefix", "")),
        "teaching": (
            "If a modality can be a sequence, cross-attention can condition a text decoder. "
            "CLIP trains dual encoders so related image/text embeddings agree."
        ),
        "source": {"file": "05_multimodal.ipynb", "cell_index": 5},
    }


def decoder_sampling(p: dict[str, Any]) -> dict[str, Any]:
    max_length = max(1, int(p.get("max_length", 30)))
    temperature = _clamp(float(p.get("temperature", 0.6)), 0.01, 2.0)
    do_sample = bool(p.get("do_sample", True))
    seed = int(p.get("seed", 42))
    diversity = 0.15 if not do_sample else _clamp(temperature / 1.2, 0.05, 1.0)
    coherence = _clamp(1.0 - 0.45 * diversity, 0.2, 0.95)
    uses_chat_template = bool(p.get("chat_template", False))
    return {
        "scenario": "decoder-sampling",
        "architecture": "decoder-only",
        "bidirectional": False,
        "max_length": max_length,
        "temperature": temperature,
        "do_sample": do_sample,
        "seed": seed,
        "diversity_qualitative": round(diversity, 2),
        "coherence_qualitative": round(coherence, 2),
        "chat_template": uses_chat_template,
        "codegen_risks": [
            "overgenerate",
            "misinterpret_intent",
            "assume_external_context",
            "go_off_track",
        ],
        "teaching": (
            "GPT-style models drop the encoder when context and generation share a vocabulary. "
            "Unidirectional. Chat-tuned Llama-2 expects <s>[INST]<<SYS>>… format. "
            "CodeGen can overgenerate after a function because training files did."
        ),
        "source": {"file": "06_textgen.ipynb", "cell_index": 3},
    }


def quantization_memory(p: dict[str, Any]) -> dict[str, Any]:
    params_b = float(p.get("params_billion", 13))
    bits = int(p.get("bits", 16))
    bits = bits if bits in (4, 8, 16, 32) else 16
    gb = params_b * (bits / 8)
    # Course numbers: 70B ~135GB; 8-bit ~69GB (and conversion keeps original in RAM).
    course_70b_fp16 = 135.0
    course_70b_int8 = 69.0
    peak_if_self_quantizing = gb * 2 if bits < 16 else gb
    gpu = "consumer-insufficient"
    if params_b >= 70 and bits >= 16:
        gpu = "A100-or-greater (course)"
    elif params_b >= 70 and bits == 8:
        gpu = "A100 to self-quantize 70B-8qt (course)"
    elif params_b <= 13 and bits <= 4:
        gpu = "A10 or T4 fully utilized for 13B-4qt (course)"
    quality_shift = {32: 0.0, 16: 0.02, 8: 0.08, 4: 0.15}[bits]
    return {
        "scenario": "quantization-memory",
        "params_billion": params_b,
        "bits": bits,
        "approx_weight_gb": round(max(0.0, gb), 2),
        "peak_gb_if_self_quantizing": round(max(0.0, peak_if_self_quantizing), 2),
        "course_70b_fp16_gb": course_70b_fp16,
        "course_70b_int8_gb": course_70b_int8,
        "suggested_gpu": gpu,
        "quality_shift_qualitative": quality_shift,
        "gptq_needs_forward": bits == 4 or p.get("method") == "gptq",
        "prequantized_example": "TheBloke/Llama-2-13B-chat-GPTQ",
        "never_claim": "Lower bits do not universally win accuracy.",
        "teaching": (
            "Quantization maps high-precision weights to a smaller set. GPTQ adapts rounding "
            "using representative inputs and needs an unquantized forward pass to produce. "
            "TheBloke GPTQ checkpoints let the course skip self-quantization."
        ),
        "source": {"file": "06_textgen.ipynb", "cell_index": 19},
    }


def langchain_memory(p: dict[str, Any]) -> dict[str, Any]:
    turns = max(0, int(p.get("turns", 4)))
    tokens_per_turn = max(8, int(p.get("tokens_per_turn", 80)))
    limit = int(p.get("context_limit", 1024))
    mode = str(p.get("mode", "buffer"))
    buffer_tokens = turns * tokens_per_turn
    if mode == "summary":
        stored = min(limit, 120 + 25 * math.log1p(turns))
        lossy = True
    elif mode == "summary_buffer":
        stored = min(limit, 0.5 * buffer_tokens + 80)
        lossy = turns > 6
    else:
        stored = buffer_tokens
        lossy = False
    overflow = stored > limit
    return {
        "scenario": "langchain-memory",
        "turns": turns,
        "mode": mode,
        "buffer_tokens": round(buffer_tokens, 1),
        "stored_tokens": round(min(stored, limit * 1.5), 1),
        "context_limit": limit,
        "overflow": overflow,
        "lossy": lossy,
        "partial_variables_gotcha": (
            "Notebook 7 warning: ConversationChain may not see PromptTemplate partials; "
            "history must be in input_variables."
        ),
        "teaching": (
            "LLMChain has no memory. Conversation buffer injects history. "
            "Summary memory trades faithfulness for length. VectorStore memory is RAG-like."
        ),
        "source": {"file": "07_stateful_models.ipynb", "cell_index": 28},
    }


def rag_agent(p: dict[str, Any]) -> dict[str, Any]:
    steps = max(1, min(12, int(p.get("steps", 3))))
    tool = str(p.get("tool", "Ask-For-Input Tool"))
    loop_style = str(p.get("loop", "behind_the_scenes"))
    python_repl = tool.lower().startswith("python")
    retrieved = int(p.get("retrieved_chunks", 3))
    grounded = retrieved > 0 and not python_repl
    return {
        "scenario": "rag-agent",
        "steps": steps,
        "tool": tool,
        "loop": loop_style,
        "python_repl_dangerous": python_repl,
        "retrieved_chunks": retrieved,
        "grounded": grounded,
        "react": True,
        "scratchpad_grows": True,
        "final_action": loop_style != "dialog",
        "assessment_loop": loop_style == "dialog",
        "teaching": (
            "RAG: tools/retrieval always (or often) inject environment text. "
            "Agent: LLM(s) in an event loop until stop. "
            "Notebook 7: dialog-spanning loop is the assessment. Python REPL is a bad idea in practice."
        ),
        "source": {"file": "07_stateful_models.ipynb", "cell_index": 39},
    }


def assessment_agent(p: dict[str, Any]) -> dict[str, Any]:
    features = {
        "memory": bool(p.get("memory", False)),
        "image": bool(p.get("image", False)),
        "code": bool(p.get("code", False)),
        "toxicity": bool(p.get("toxicity", False)),
        "emotion": bool(p.get("emotion", False)),
    }
    n = sum(1 for v in features.values() if v)
    user_toxicity = _clamp(float(p.get("user_toxicity", 0.5)), 0.0, 1.0)
    # Course: nicholasKluge/ToxicityModel returns reward = 1 - toxicity
    reward = _clamp(1.0 - user_toxicity, 0.0, 1.0)
    return {
        "scenario": "assessment-agent",
        "features": features,
        "implemented_count": n,
        "pass_threshold": 3,
        "passed": n >= 3,
        "user_toxicity": user_toxicity,
        "toxicity_reward": round(reward, 3),
        "user_emotion": str(p.get("user_emotion", "Unknown")),
        "image_syntax": "`path/to/img.png`",
        "code_fence_trigger": "```",
        "models": {
            "image": "Salesforce/blip-image-captioning-large",
            "emotion": "SamLowe/roberta-base-go_emotions",
            "zsc": "facebook/bart-large-mnli",
            "toxicity": "nicholasKluge/ToxicityModel",
        },
        "assessment_note": "Assessment uses Llama-2-13B-chat-GPTQ, not 70B.",
        "teaching": (
            "Pass when ≥3 of 5 features work. ToxicityModel reward is inverted. "
            "Agent event loop talks to the user via Ask-For-Input Tool."
        ),
        "source": {"file": "08_assessment.ipynb", "cell_index": 22},
    }


def incident_diagnosis(p: dict[str, Any]) -> dict[str, Any]:
    """Ground truth withheld until the learner commits a cause."""
    committed = bool(p.get("committed", False))
    guess = str(p.get("guess", "unknown"))
    symptom = str(p.get("symptom", "second_turn_amnesia"))
    truth = {
        "second_turn_amnesia": "llmchain-no-memory",
        "exec_blew_up": "python-repl",
        "caption_never_fires": "missing-image-syntax",
        "labels_look_random": "zero-shot-misread",
    }.get(symptom, "unknown")
    revealed = committed
    return {
        "scenario": "incident-diagnosis",
        "symptom": symptom,
        "committed": committed,
        "guess": guess,
        "ground_truth": truth if revealed else None,
        "correct": (guess == truth) if revealed else None,
        "withheld": not revealed,
        "teaching": (
            "Diagnosis revealed after you lock a cause."
            if revealed
            else "Predict the cause. Ground truth stays hidden until you commit."
        ),
        "source": {"file": "07_stateful_models.ipynb", "cell_index": 26},
    }


def risk_radar(p: dict[str, Any]) -> dict[str, Any]:
    prompt_injection = _clamp(float(p.get("untrusted_tool_text", 0.4)), 0, 1)
    repl = bool(p.get("python_repl", False))
    gpu_frac = _clamp(float(p.get("gpu_ram_used", 0.7)), 0, 1)
    tox = _clamp(float(p.get("user_toxicity", 0.2)), 0, 1)
    license_unknown = bool(p.get("license_unknown", True))
    risks = {
        "prompt_injection": round(prompt_injection, 2),
        "code_execution": 0.95 if repl else 0.15,
        "gpu_oom": round(gpu_frac, 2),
        "toxicity_missign": round(abs(tox - (1 - tox)), 2),
        "license_gap": 0.7 if license_unknown else 0.1,
    }
    top = max(risks, key=risks.get)
    return {
        "scenario": "risk-radar",
        "risks": risks,
        "leading": top,
        "teaching": (
            f"Highest simulated risk: {top}. "
            "Python REPL is a course-flagged hazard. License extras notebook is missing from this repo."
        ),
        "source": {"file": "07_stateful_models.ipynb", "cell_index": 43},
    }


def keda_incident(_p: dict[str, Any]) -> dict[str, Any]:
    """Not a course twin. Kept so a mis-routed UI cannot look like an NVIDIA inference lab."""
    return {
        "scenario": "out-of-course",
        "available": False,
        "teaching": (
            "KEDA / Dynamo / Grove are not established by the supplied RAD-LLM notebooks."
        ),
        "evidence_type": "COURSE_SOURCE",
    }


SCENARIOS = {
    "pipeline-flow": pipeline_flow,
    "tokenizer-embeddings": tokenizer_embeddings,
    "attention-encoder": attention_encoder,
    "encoder-heads": encoder_heads,
    "seq2seq-t5": seq2seq_t5,
    "multimodal": multimodal,
    "decoder-sampling": decoder_sampling,
    "quantization-memory": quantization_memory,
    "langchain-memory": langchain_memory,
    "rag-agent": rag_agent,
    "assessment-agent": assessment_agent,
    "incident-diagnosis": incident_diagnosis,
    "risk-radar": risk_radar,
    "keda-autoscaling": keda_incident,
}


TWIN_CATALOG = [
    {
        "id": "pipeline-flow",
        "name": "HuggingFace Pipeline",
        "summary": "preprocess → forward → postprocess with tokenizer + model.",
        "notebook_file": "01_llm_intro.ipynb",
        "controls": [
            {"key": "text", "type": "string", "default": "Hello I'm a [MASK] model."},
            {"key": "n_tokens", "type": "int", "min": 1, "max": 128, "default": 8},
        ],
    },
    {
        "id": "tokenizer-embeddings",
        "name": "Tokens & Embeddings",
        "summary": "input_ids, 30522×768 word table, 512 positions, addition.",
        "notebook_file": "02_llm_intake.ipynb",
        "controls": [
            {"key": "seq_len", "type": "int", "min": 1, "max": 640, "default": 12},
            {"key": "sentence_pair", "type": "bool", "default": False},
        ],
    },
    {
        "id": "attention-encoder",
        "name": "Self-Attention Encoder",
        "summary": "12 layers × 12 heads, residuals, 3072 intermediate.",
        "notebook_file": "02_llm_intake.ipynb",
        "controls": [
            {"key": "seq_len", "type": "int", "min": 1, "max": 128, "default": 10},
            {"key": "residual", "type": "bool", "default": True},
            {"key": "apply_padding_mask", "type": "bool", "default": False},
        ],
    },
    {
        "id": "encoder-heads",
        "name": "Encoder Task Heads",
        "summary": "MLM vs span QA vs sequence class vs zero-shot queries.",
        "notebook_file": "03_encoder_task.ipynb",
        "controls": [
            {
                "key": "mode",
                "type": "enum",
                "options": ["mlm", "qa", "sequence", "zero_shot"],
                "default": "mlm",
            },
            {"key": "seq_len", "type": "int", "min": 2, "max": 128, "default": 16},
            {"key": "n_classes", "type": "int", "min": 2, "max": 12, "default": 4},
        ],
    },
    {
        "id": "seq2seq-t5",
        "name": "T5 Encoder–Decoder",
        "summary": "One encoder call, many decoder steps, Flan vs T5.",
        "notebook_file": "04_seq2seq.ipynb",
        "controls": [
            {
                "key": "model",
                "type": "enum",
                "options": ["t5-base", "t5-large", "flan-t5-large"],
                "default": "t5-base",
            },
            {"key": "input_tokens", "type": "int", "min": 1, "max": 128, "default": 12},
            {"key": "output_tokens", "type": "int", "min": 1, "max": 64, "default": 8},
        ],
    },
    {
        "id": "multimodal",
        "name": "Multimodal Cross-Attention",
        "summary": "Whisper spectrograms, ViT patches, CLIP dual space.",
        "notebook_file": "05_multimodal.ipynb",
        "controls": [
            {
                "key": "kind",
                "type": "enum",
                "options": ["whisper", "caption", "clip"],
                "default": "whisper",
            },
            {"key": "audio_seconds", "type": "float", "min": 0.5, "max": 60, "default": 8},
            {
                "key": "whisper_size",
                "type": "enum",
                "options": ["base", "large-v2"],
                "default": "base",
            },
            {
                "key": "caption_model",
                "type": "enum",
                "options": ["vit-gpt2", "blip"],
                "default": "vit-gpt2",
            },
        ],
    },
    {
        "id": "decoder-sampling",
        "name": "Decoder-Only Generation",
        "summary": "Temperature, seed, chat template, CodeGen failure modes.",
        "notebook_file": "06_textgen.ipynb",
        "controls": [
            {"key": "max_length", "type": "int", "min": 8, "max": 256, "default": 30},
            {"key": "temperature", "type": "float", "min": 0.01, "max": 2, "default": 0.6},
            {"key": "do_sample", "type": "bool", "default": True},
            {"key": "chat_template", "type": "bool", "default": False},
            {"key": "seed", "type": "int", "min": 0, "max": 9999, "default": 42},
        ],
    },
    {
        "id": "quantization-memory",
        "name": "Quantization & GPU RAM",
        "summary": "Course 70B≈135GB; GPTQ vs bitsandbytes; TheBloke checkpoints.",
        "notebook_file": "06_textgen.ipynb",
        "controls": [
            {"key": "params_billion", "type": "float", "min": 0.35, "max": 70, "default": 13},
            {"key": "bits", "type": "enum", "options": [4, 8, 16, 32], "default": 4},
            {
                "key": "method",
                "type": "enum",
                "options": ["naive", "gptq", "bitsandbytes"],
                "default": "gptq",
            },
        ],
    },
    {
        "id": "langchain-memory",
        "name": "LangChain Memory",
        "summary": "Buffer vs summary vs overflow at the context limit.",
        "notebook_file": "07_stateful_models.ipynb",
        "controls": [
            {"key": "turns", "type": "int", "min": 0, "max": 40, "default": 4},
            {"key": "tokens_per_turn", "type": "int", "min": 8, "max": 400, "default": 80},
            {"key": "context_limit", "type": "int", "min": 128, "max": 4096, "default": 1024},
            {
                "key": "mode",
                "type": "enum",
                "options": ["buffer", "summary", "summary_buffer"],
                "default": "buffer",
            },
        ],
    },
    {
        "id": "rag-agent",
        "name": "RAG vs Agent Loop",
        "summary": "ReAct scratchpad, tools, dialog vs behind-the-scenes loops.",
        "notebook_file": "07_stateful_models.ipynb",
        "controls": [
            {"key": "steps", "type": "int", "min": 1, "max": 12, "default": 3},
            {
                "key": "tool",
                "type": "enum",
                "options": ["Ask-For-Input Tool", "Python REPL", "Vector store"],
                "default": "Ask-For-Input Tool",
            },
            {
                "key": "loop",
                "type": "enum",
                "options": ["behind_the_scenes", "dialog"],
                "default": "behind_the_scenes",
            },
            {"key": "retrieved_chunks", "type": "int", "min": 0, "max": 12, "default": 3},
        ],
    },
    {
        "id": "assessment-agent",
        "name": "Assessment Agent Arena",
        "summary": "Design ≥3/5 features; inverted toxicity reward.",
        "notebook_file": "08_assessment.ipynb",
        "controls": [
            {"key": "memory", "type": "bool", "default": True},
            {"key": "image", "type": "bool", "default": True},
            {"key": "code", "type": "bool", "default": False},
            {"key": "toxicity", "type": "bool", "default": True},
            {"key": "emotion", "type": "bool", "default": False},
            {"key": "user_toxicity", "type": "float", "min": 0, "max": 1, "default": 0.2},
        ],
    },
    {
        "id": "incident-diagnosis",
        "name": "Incident diagnosis",
        "summary": "Commit a cause before the twin reveals the ground truth.",
        "notebook_file": "07_stateful_models.ipynb",
        "controls": [
            {
                "key": "symptom",
                "type": "enum",
                "options": ["second_turn_amnesia", "exec_blew_up", "caption_never_fires", "labels_look_random"],
                "default": "second_turn_amnesia",
            },
            {
                "key": "guess",
                "type": "enum",
                "options": ["llmchain-no-memory", "python-repl", "missing-image-syntax", "zero-shot-misread", "unknown"],
                "default": "unknown",
            },
            {"key": "committed", "type": "bool", "default": False},
        ],
    },
    {
        "id": "risk-radar",
        "name": "Operational risk radar",
        "summary": "Simulated technical, security, and business risk scores — not measurements.",
        "notebook_file": "07_stateful_models.ipynb",
        "controls": [
            {"key": "untrusted_tool_text", "type": "float", "min": 0, "max": 1, "default": 0.4},
            {"key": "python_repl", "type": "bool", "default": False},
            {"key": "gpu_ram_used", "type": "float", "min": 0, "max": 1, "default": 0.7},
            {"key": "user_toxicity", "type": "float", "min": 0, "max": 1, "default": 0.2},
            {"key": "license_unknown", "type": "bool", "default": True},
        ],
    },
]


SUGGESTED = {
    "pipeline-flow": [
        {"name": "Has MASK", "params": {"text": "Hello I'm a [MASK] model.", "n_tokens": 8}},
        {"name": "No MASK", "params": {"text": "Hello I am a model.", "n_tokens": 6}},
        {"name": "Longer prompt", "params": {"text": "Hello I'm a [MASK] model in a long sentence.", "n_tokens": 24}},
        {"name": "Tiny ticket", "params": {"text": "[MASK]", "n_tokens": 2}},
    ],
    "tokenizer-embeddings": [
        {"name": "Short single", "params": {"seq_len": 8, "sentence_pair": False}},
        {"name": "Sentence pair", "params": {"seq_len": 24, "sentence_pair": True}},
        {"name": "Over 512", "params": {"seq_len": 600, "sentence_pair": False}},
        {"name": "Single token", "params": {"seq_len": 1, "sentence_pair": False}},
    ],
    "attention-encoder": [
        {"name": "Tiny residual", "params": {"seq_len": 4, "residual": True, "apply_padding_mask": False}},
        {"name": "Padded", "params": {"seq_len": 32, "residual": True, "apply_padding_mask": True}},
        {"name": "No residual", "params": {"seq_len": 16, "residual": False, "apply_padding_mask": False}},
        {"name": "Longer seq", "params": {"seq_len": 64, "residual": True, "apply_padding_mask": False}},
    ],
    "encoder-heads": [
        {"name": "MLM", "params": {"mode": "mlm", "seq_len": 16}},
        {"name": "QA span", "params": {"mode": "qa", "seq_len": 32}},
        {"name": "Sequence class", "params": {"mode": "sequence", "seq_len": 12}},
        {"name": "Zero-shot 6", "params": {"mode": "zero_shot", "n_classes": 6}},
    ],
    "seq2seq-t5": [
        {"name": "Vanilla T5 short", "params": {"model": "t5-base", "input_tokens": 8, "output_tokens": 4}},
        {"name": "Flan longer", "params": {"model": "flan-t5-large", "input_tokens": 24, "output_tokens": 16}},
        {"name": "T5-large", "params": {"model": "t5-large", "input_tokens": 12, "output_tokens": 8}},
        {"name": "One-step decode", "params": {"model": "t5-base", "input_tokens": 4, "output_tokens": 1}},
    ],
    "multimodal": [
        {"name": "Whisper base", "params": {"kind": "whisper", "audio_seconds": 8, "whisper_size": "base"}},
        {"name": "Whisper large", "params": {"kind": "whisper", "audio_seconds": 20, "whisper_size": "large-v2"}},
        {"name": "ViT-GPT2", "params": {"kind": "caption", "caption_model": "vit-gpt2"}},
        {"name": "CLIP retrieve", "params": {"kind": "clip"}},
    ],
    "decoder-sampling": [
        {"name": "Greedy", "params": {"do_sample": False, "temperature": 0.01, "max_length": 20}},
        {"name": "Hot sample", "params": {"do_sample": True, "temperature": 1.4, "max_length": 40}},
        {"name": "Chat template", "params": {"chat_template": True, "temperature": 0.6}},
        {"name": "Short seed", "params": {"max_length": 8, "seed": 1, "do_sample": True}},
    ],
    "quantization-memory": [
        {"name": "13B 4-bit", "params": {"params_billion": 13, "bits": 4, "method": "gptq"}},
        {"name": "70B 16-bit", "params": {"params_billion": 70, "bits": 16, "method": "naive"}},
        {"name": "70B 8-bit", "params": {"params_billion": 70, "bits": 8, "method": "bitsandbytes"}},
        {"name": "13B 16-bit", "params": {"params_billion": 13, "bits": 16, "method": "naive"}},
    ],
    "langchain-memory": [
        {"name": "Short buffer", "params": {"turns": 3, "mode": "buffer", "context_limit": 1024}},
        {"name": "Overflow buffer", "params": {"turns": 30, "tokens_per_turn": 200, "mode": "buffer", "context_limit": 256}},
        {"name": "Summary", "params": {"turns": 20, "mode": "summary", "context_limit": 512}},
        {"name": "Summary buffer", "params": {"turns": 12, "mode": "summary_buffer", "context_limit": 1024}},
    ],
    "rag-agent": [
        {"name": "Ask user", "params": {"tool": "Ask-For-Input Tool", "loop": "dialog", "steps": 3}},
        {"name": "REPL hazard", "params": {"tool": "Python REPL", "loop": "behind_the_scenes", "steps": 4}},
        {"name": "RAG chunks", "params": {"tool": "Vector store", "retrieved_chunks": 6, "loop": "behind_the_scenes"}},
        {"name": "No retrieval", "params": {"retrieved_chunks": 0, "tool": "Ask-For-Input Tool"}},
    ],
    "assessment-agent": [
        {"name": "Pass three", "params": {"memory": True, "image": True, "toxicity": True, "code": False, "emotion": False}},
        {"name": "Fail two", "params": {"memory": True, "image": False, "toxicity": False, "code": False, "emotion": False}},
        {"name": "Toxic user", "params": {"toxicity": True, "user_toxicity": 0.9}},
        {"name": "All five", "params": {"memory": True, "image": True, "code": True, "toxicity": True, "emotion": True}},
    ],
    "incident-diagnosis": [
        {"name": "Forgot last turn", "params": {"symptom": "second_turn_amnesia", "guess": "llmchain-no-memory", "committed": False}},
        {"name": "REPL blast", "params": {"symptom": "exec_blew_up", "guess": "python-repl", "committed": False}},
        {"name": "Image silent", "params": {"symptom": "caption_never_fires", "guess": "missing-image-syntax", "committed": False}},
        {"name": "Commit amnesia", "params": {"symptom": "second_turn_amnesia", "guess": "llmchain-no-memory", "committed": True}},
    ],
    "risk-radar": [
        {"name": "REPL on", "params": {"python_repl": True, "untrusted_tool_text": 0.8}},
        {"name": "Tight GPU", "params": {"gpu_ram_used": 0.95, "python_repl": False}},
        {"name": "Clean tools", "params": {"python_repl": False, "license_unknown": False, "untrusted_tool_text": 0.1}},
        {"name": "Toxic + injection", "params": {"user_toxicity": 0.9, "untrusted_tool_text": 0.95}},
    ],
}


def _attach_suggestions() -> None:
    for t in TWIN_CATALOG:
        t["suggested"] = SUGGESTED.get(
            t["id"],
            [
                {"name": "Default", "params": {c["key"]: c.get("default") for c in t["controls"]}},
                {"name": "Stress", "params": {c["key"]: c.get("max", c.get("default")) for c in t["controls"]}},
                {"name": "Gentle", "params": {c["key"]: c.get("min", c.get("default")) for c in t["controls"]}},
            ],
        )


_attach_suggestions()
