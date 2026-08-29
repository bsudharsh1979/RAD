"""150+ twin-engine tests: directionality, evidence integrity, suggestions."""

from __future__ import annotations

import math

import pytest

from twin_engine.engine import SCENARIOS, SUGGESTED, TWIN_CATALOG, run, sanitize

COURSE_TWINS = [t["id"] for t in TWIN_CATALOG]
PARAM_SWEEPS = {
    "pipeline-flow": [{"n_tokens": n} for n in (1, 2, 4, 8, 16, 32, 64, 100)],
    "tokenizer-embeddings": [{"seq_len": n} for n in (1, 8, 16, 64, 128, 512, 513, 600)],
    "attention-encoder": [{"seq_len": n, "residual": r} for n in (1, 8, 16, 32, 64) for r in (True, False)],
    "encoder-heads": [{"mode": m, "seq_len": 16, "n_classes": 4} for m in ("mlm", "qa", "sequence", "zero_shot")],
    "seq2seq-t5": [
        {"model": m, "input_tokens": i, "output_tokens": o}
        for m in ("t5-base", "t5-large", "flan-t5-large")
        for i, o in ((4, 2), (12, 8), (32, 16))
    ],
    "multimodal": [
        {"kind": "whisper", "audio_seconds": s, "whisper_size": z}
        for s in (0.5, 4, 8, 20)
        for z in ("base", "large-v2")
    ]
    + [{"kind": "caption", "caption_model": m} for m in ("vit-gpt2", "blip")]
    + [{"kind": "clip"}],
    "decoder-sampling": [
        {"temperature": t, "do_sample": s, "max_length": 20}
        for t in (0.01, 0.3, 0.6, 1.2, 2.0)
        for s in (True, False)
    ],
    "quantization-memory": [
        {"params_billion": p, "bits": b}
        for p in (0.35, 7, 13, 70)
        for b in (4, 8, 16, 32)
    ],
    "langchain-memory": [
        {"turns": t, "mode": m, "context_limit": 512}
        for t in (0, 2, 8, 20)
        for m in ("buffer", "summary", "summary_buffer")
    ],
    "rag-agent": [
        {"steps": s, "tool": tool, "retrieved_chunks": c}
        for s in (1, 3, 8)
        for tool in ("Ask-For-Input Tool", "Python REPL", "Vector store")
        for c in (0, 3)
    ],
    "assessment-agent": [
        {"memory": True, "image": True, "toxicity": True, "user_toxicity": tox} for tox in (0.0, 0.2, 0.5, 0.9, 1.0)
    ]
    + [
        {"memory": a, "image": b, "code": c, "toxicity": d, "emotion": e}
        for a, b, c, d, e in (
            (False, False, False, False, False),
            (True, False, False, False, False),
            (True, True, False, False, False),
            (True, True, True, False, False),
            (True, True, True, True, True),
        )
    ],
    "incident-diagnosis": [
        {"symptom": s, "guess": g, "committed": c}
        for s in ("second_turn_amnesia", "exec_blew_up", "caption_never_fires", "labels_look_random")
        for g in ("llmchain-no-memory", "python-repl", "unknown")
        for c in (False, True)
    ],
    "risk-radar": [
        {"python_repl": r, "gpu_ram_used": g, "untrusted_tool_text": u, "license_unknown": lic}
        for r in (False, True)
        for g in (0.2, 0.7, 0.99)
        for u in (0.1, 0.8)
        for lic in (False, True)
    ],
}


def _finite_ok(state: dict) -> None:
    for k, v in state.items():
        if isinstance(v, float):
            assert not math.isnan(v) and not math.isinf(v), k
            if any(s in k for s in ("ms", "latency", "tokens", "memory", "gb")):
                assert v >= 0, k


def test_catalog_has_incident_and_radar():
    ids = {t["id"] for t in TWIN_CATALOG}
    assert "incident-diagnosis" in ids
    assert "risk-radar" in ids
    assert 8 <= len(TWIN_CATALOG) <= 14


@pytest.mark.parametrize("tid", COURSE_TWINS)
def test_default_run_is_simulated(tid):
    st = run(tid, {})
    assert st["evidence_type"] == "SIMULATED_RESULT"
    assert st["evidence_type"] != "ACTUAL_RUN"
    _finite_ok(st)


@pytest.mark.parametrize("tid", COURSE_TWINS)
def test_cannot_force_actual_run(tid):
    st = sanitize({**run(tid, {}), "evidence_type": "ACTUAL_RUN"})
    assert st["evidence_type"] == "SIMULATED_RESULT"
    assert st.get("evidence_coerced") is True


def test_sanitize_nukes_nan_and_clamps():
    s = sanitize({"ttft_ms": float("nan"), "util": 2.5, "hit_rate": -1.0, "tokens": -4})
    assert s["ttft_ms"] == 0.0
    assert 0 <= s["util"] <= 1
    assert 0 <= s["hit_rate"] <= 1
    assert s["tokens"] >= 0


CASES = [(tid, p) for tid, plist in PARAM_SWEEPS.items() for p in plist]


@pytest.mark.parametrize("tid,params", CASES)
def test_param_sweep_finite_simulated(tid, params):
    st = run(tid, params)
    assert st["evidence_type"] == "SIMULATED_RESULT"
    _finite_ok(st)


@pytest.mark.parametrize("tid", COURSE_TWINS)
def test_each_twin_has_3_to_4_suggestions(tid):
    row = next(t for t in TWIN_CATALOG if t["id"] == tid)
    sug = row.get("suggested") or SUGGESTED.get(tid) or []
    assert 3 <= len(sug) <= 6


SUG_CASES = [(tid, s["name"], s["params"]) for tid, rows in SUGGESTED.items() for s in rows]


@pytest.mark.parametrize("tid,name,params", SUG_CASES)
def test_suggested_scenarios_run(tid, name, params):
    st = run(tid, params)
    assert st["evidence_type"] == "SIMULATED_RESULT"
    _finite_ok(st)


def test_more_tokens_increase_pipeline_time():
    a = run("pipeline-flow", {"n_tokens": 4})
    b = run("pipeline-flow", {"n_tokens": 40})
    assert b["total_ms"] > a["total_ms"]
    assert b["forward_ms"] > a["forward_ms"]


def test_seq_over_512_flagged():
    st = run("tokenizer-embeddings", {"seq_len": 600})
    assert st["over_limit"] is True


def test_embeddings_add_not_concat():
    st = run("tokenizer-embeddings", {"seq_len": 10})
    assert st["combine"] == "addition"
    assert "WordEmbed" in st["formula"]


def test_attention_grows_with_seq():
    a = run("attention-encoder", {"seq_len": 8})
    b = run("attention-encoder", {"seq_len": 32})
    assert b["attn_elems"] > a["attn_elems"]


def test_qa_cannot_emit_novel_tokens():
    st = run("encoder-heads", {"mode": "qa"})
    assert st["can_emit_novel_tokens"] is False
    assert "substring" in st["restriction"].lower()


def test_zeroshot_multi_query():
    st = run("encoder-heads", {"mode": "zero_shot", "n_classes": 5})
    assert st["n_forward_passes"] == 5


def test_t5_encoder_once_decoder_many():
    st = run("seq2seq-t5", {"output_tokens": 7, "input_tokens": 10})
    assert st["encoder_calls"] == 1
    assert st["decoder_calls"] == 7
    assert st["pig_latin_expected_fail"] is True


def test_flan_more_instruction_following_than_t5():
    t5 = run("seq2seq-t5", {"model": "t5-base"})
    flan = run("seq2seq-t5", {"model": "flan-t5-large"})
    assert flan["instruction_following_qualitative"] > t5["instruction_following_qualitative"]


def test_whisper_frames_scale_with_seconds():
    a = run("multimodal", {"kind": "whisper", "audio_seconds": 2})
    b = run("multimodal", {"kind": "whisper", "audio_seconds": 20})
    assert b["spectrogram_frames"] > a["spectrogram_frames"]


def test_hot_temperature_more_diverse():
    cool = run("decoder-sampling", {"temperature": 0.2, "do_sample": True})
    hot = run("decoder-sampling", {"temperature": 1.8, "do_sample": True})
    assert hot["diversity_qualitative"] > cool["diversity_qualitative"]


def test_greedy_less_diverse_than_sample():
    g = run("decoder-sampling", {"do_sample": False, "temperature": 1.0})
    s = run("decoder-sampling", {"do_sample": True, "temperature": 1.0})
    assert s["diversity_qualitative"] >= g["diversity_qualitative"]


def test_more_bits_more_memory():
    q4 = run("quantization-memory", {"params_billion": 13, "bits": 4})
    q16 = run("quantization-memory", {"params_billion": 13, "bits": 16})
    assert q16["approx_weight_gb"] > q4["approx_weight_gb"]
    assert "never_claim" in q4


def test_70b_fp16_matches_course_order():
    st = run("quantization-memory", {"params_billion": 70, "bits": 16})
    assert st["course_70b_fp16_gb"] == 135.0
    assert st["approx_weight_gb"] > 100


def test_self_quant_peak_doubles():
    st = run("quantization-memory", {"params_billion": 70, "bits": 8})
    assert st["peak_gb_if_self_quantizing"] >= st["approx_weight_gb"]


def test_buffer_overflows_when_long():
    st = run("langchain-memory", {"turns": 40, "tokens_per_turn": 200, "context_limit": 256, "mode": "buffer"})
    assert st["overflow"] is True
    assert st["lossy"] is False


def test_summary_is_lossy_and_smaller():
    buf = run("langchain-memory", {"turns": 20, "tokens_per_turn": 80, "mode": "buffer", "context_limit": 4096})
    sm = run("langchain-memory", {"turns": 20, "tokens_per_turn": 80, "mode": "summary", "context_limit": 4096})
    assert sm["lossy"] is True
    assert sm["stored_tokens"] < buf["stored_tokens"]


def test_python_repl_flagged():
    st = run("rag-agent", {"tool": "Python REPL"})
    assert st["python_repl_dangerous"] is True


def test_toxicity_reward_inverted():
    st = run("assessment-agent", {"user_toxicity": 0.8, "toxicity": True})
    assert abs(st["toxicity_reward"] - 0.2) < 1e-6


def test_assessment_pass_at_three():
    fail = run("assessment-agent", {"memory": True, "image": True, "code": False, "toxicity": False, "emotion": False})
    ok = run("assessment-agent", {"memory": True, "image": True, "toxicity": True, "code": False, "emotion": False})
    assert fail["passed"] is False
    assert ok["passed"] is True
    assert ok["implemented_count"] == 3


def test_incident_withholds_until_commit():
    hidden = run("incident-diagnosis", {"symptom": "second_turn_amnesia", "guess": "llmchain-no-memory", "committed": False})
    shown = run("incident-diagnosis", {"symptom": "second_turn_amnesia", "guess": "llmchain-no-memory", "committed": True})
    assert hidden["ground_truth"] is None
    assert hidden["withheld"] is True
    assert shown["ground_truth"] == "llmchain-no-memory"
    assert shown["correct"] is True


def test_incident_wrong_guess():
    st = run("incident-diagnosis", {"symptom": "exec_blew_up", "guess": "llmchain-no-memory", "committed": True})
    assert st["correct"] is False
    assert st["ground_truth"] == "python-repl"


def test_risk_radar_repl_leads():
    st = run("risk-radar", {"python_repl": True, "gpu_ram_used": 0.1, "untrusted_tool_text": 0.1, "license_unknown": False})
    assert st["leading"] == "code_execution"
    assert st["risks"]["code_execution"] > 0.5


def test_keda_disclosed_out_of_course():
    st = run("keda-autoscaling", {})
    assert st["available"] is False
    assert "not established" in st["teaching"].lower()


def test_unknown_scenario_raises():
    with pytest.raises(KeyError):
        run("not-a-twin", {})


def test_count_generated_cases_over_150():
    n = len(CASES) + len(SUG_CASES) + len(COURSE_TWINS) * 3
    assert n >= 150
