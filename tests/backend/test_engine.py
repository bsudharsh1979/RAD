import math

from app.domains.twins.engine import run, sanitize
from app.ingestion.safety import inspect_code  # noqa: E402
from app.domains.experiments.importer import compare_runs, parse_import  # noqa: E402
from app.domains.mastery.fsrs import review  # noqa: E402
from app.seed.questions import all_questions  # noqa: E402
from app.seed.concepts import CONCEPTS  # noqa: E402


def test_notebook_code_never_auto_executes():
    src = "%%bash\nnvidia-smi\nexec('rm -rf /')\n"
    flags = inspect_code(src)
    assert "jupyter_bash_magic" in flags
    assert "nvidia_smi" in flags
    assert "exec" in flags


def test_simulation_never_labeled_actual():
    st = run("pipeline-flow", {"n_tokens": 8})
    assert st["evidence_type"] == "SIMULATED_RESULT"
    assert st["evidence_type"] != "ACTUAL_RUN"


def test_expected_notebook_not_actual():
    # Ingested cells without outputs must not be ACTUAL_RUN
    from app.ingestion.engine import NOTEBOOK_META

    assert NOTEBOOK_META  # course commentary exists
    st = run("seq2seq-t5", {"output_tokens": 4})
    assert st["evidence_type"] == "SIMULATED_RESULT"


def test_twin_boundaries_no_nan():
    cases = [
        ("pipeline-flow", {"n_tokens": 0}),
        ("tokenizer-embeddings", {"seq_len": 1}),
        ("attention-encoder", {"seq_len": 1}),
        ("seq2seq-t5", {"output_tokens": 1, "input_tokens": 1}),
        ("quantization-memory", {"params_billion": 70, "bits": 4}),
        ("langchain-memory", {"turns": 0, "context_limit": 128}),
        ("decoder-sampling", {"max_length": 1, "temperature": 0.01}),
        ("rag-agent", {"steps": 1, "retrieved_chunks": 0}),
        ("assessment-agent", {"memory": False, "user_toxicity": 1}),
        ("multimodal", {"audio_seconds": 0.5}),
    ]
    for sc, p in cases:
        st = run(sc, p)
        for k, v in st.items():
            if isinstance(v, float):
                assert not math.isnan(v) and not math.isinf(v), k
                if "ms" in k or "latency" in k:
                    assert v >= 0


def test_sanitize_nukes_nan():
    s = sanitize({"ttft_ms": float("nan"), "util": 2.5, "evidence_type": "SIMULATED_RESULT"})
    assert s["ttft_ms"] == 0.0
    assert 0 <= s["util"] <= 1


def test_zero_decode_workers_not_applicable_but_keda_disclosed():
    st = run("keda-autoscaling", {})
    assert st["available"] is False
    assert "not established" in st["teaching"].lower()


def test_quantization_does_not_claim_universal_win():
    st = run("quantization-memory", {"bits": 4, "params_billion": 13})
    assert "never_claim" in st
    assert st["evidence_type"] == "SIMULATED_RESULT"


def test_import_is_actual_run():
    parsed = parse_import("run.json", '{"ttft": 12.5, "model": "llama"}', "json")
    assert parsed["evidence_type"] == "ACTUAL_RUN"
    assert parsed["raw"]["ttft"] == 12.5


def test_compare_detects_confounders():
    a = {"metadata": {"gpu_count": 1, "isl": 128}, "normalized": {"metrics": {"throughput": 10}}}
    b = {"metadata": {"gpu_count": 8, "isl": 2048}, "normalized": {"metrics": {"throughput": 80}}}
    cmp = compare_runs(a, b)
    fields = {c["field"] for c in cmp["confounds"]}
    assert "gpu_count" in fields
    assert "isl" in fields
    assert "not proven" in cmp["causality"].lower() or "Correlation" in cmp["causality"]


def test_question_bank_size_and_provenance():
    qs = all_questions()
    assert len(qs) >= 500
    missing = [q for q in qs if not q.get("source_file")]
    assert not missing
    types = {q["qtype"] for q in qs}
    assert "mcq" in types
    assert "troubleshooting" in types or "compare" in types


def test_concepts_seeded():
    assert len(CONCEPTS) >= 90
    slugs = [c["slug"] for c in CONCEPTS]
    assert "huggingface-pipeline" in slugs
    assert "rag" in slugs
    assert "quantization" in slugs


def test_fsrs_progresses():
    s, d, due = review(0.4, 5.0, 3, 1)
    assert s > 0 and d >= 1
    s2, _, _ = review(s, d, 1, 2)
    assert s2 > 0


def test_pig_latin_expected_fail_is_course_claim():
    st = run("seq2seq-t5", {"model": "flan-t5-large"})
    assert st["pig_latin_expected_fail"] is True
