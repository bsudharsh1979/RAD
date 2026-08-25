from fastapi.testclient import TestClient

from app.main import app  # noqa: E402
from app.seed.bootstrap import init_db_and_seed  # noqa: E402

init_db_and_seed()
client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_providers_ask_which_api():
    r = client.get("/api/providers")
    body = r.json()
    assert "demo" in body["choices"]["tutor"]
    assert body["status"]["demo"] == "connected"


def test_onboard_and_home():
    r = client.post(
        "/api/onboard",
        json={"display_name": "Ada", "tutor_provider": "demo", "voice_provider": "none"},
    )
    assert r.json()["ok"] is True
    h = client.get("/api/home").json()
    assert "thirty_minute_plan" in h
    assert "reviews_due" in h


def test_notebooks_ingested():
    nbs = client.get("/api/notebooks").json()
    assert len(nbs) == 8
    one = client.get(f"/api/notebooks/{nbs[0]['filename']}").json()
    assert one["cells"]
    code = [c for c in one["cells"] if c["cell_type"] == "code"]
    assert all(c["blocked_execution"] for c in code)


def test_diagnostic_and_attempt():
    diag = client.get("/api/diagnostic").json()
    assert diag["questions"]
    q = diag["questions"][0]
    att = client.post(
        "/api/questions/attempt",
        json={"question_id": q["id"], "given": "definitely-wrong", "hints_used": 1},
    ).json()
    assert att["correct"] is False
    assert att["feedback"]["try_again"] is True
    assert att["feedback"]["source_evidence"]["file"]


def test_tutor_course_mode_grounding():
    r = client.post("/api/tutor", json={"content": "What is a HuggingFace pipeline?"}).json()
    assert r["sources"] or "not established" in r["text"].lower()
    assert r["evidence_type"] in {"TUTOR_INTERPRETATION", "COURSE_SOURCE"}


def test_tutor_missing_topic():
    r = client.post("/api/tutor", json={"content": "How do I configure Grove PodGang with KEDA?"}).json()
    # may retrieve nothing useful
    assert "KEDA" in r["text"] or "not established" in r["text"].lower() or r["mode"] == "COURSE"


def test_twin_prediction_then_run():
    pred = client.post(
        "/api/twins/predict",
        json={"twin_id": "seq2seq-t5", "prompt": "Will encoder run once?", "predicted": {"encoder_calls": 4}},
    ).json()
    run = client.post(
        "/api/twins/run",
        json={"scenario": "seq2seq-t5", "params": {"output_tokens": 5}, "prediction_id": pred["prediction_id"]},
    ).json()
    assert run["state"]["encoder_calls"] == 1
    assert run["state"]["evidence_type"] == "SIMULATED_RESULT"


def test_teachback():
    r = client.post(
        "/api/teachback",
        json={"concept_id": "c-pipeline", "transcript": "A pipeline is tokenizer preprocess plus model forward plus postprocess."},
    ).json()
    assert "quality" in r
    assert r["evidence_type"] == "TUTOR_INTERPRETATION"


def test_experiment_import_and_compare(tmp_path=None):
    files = {
        "file": ("aiperf.json", b'{"ttft": 10, "throughput": 3, "model": "x"}', "application/json"),
    }
    a = client.post("/api/experiments/import", files=files).json()
    assert a["evidence_type"] == "ACTUAL_RUN"
    files = {
        "file": ("b.json", b'{"ttft": 40, "throughput": 1, "model": "y"}', "application/json"),
    }
    b = client.post("/api/experiments/import", files=files).json()
    cmp = client.post("/api/experiments/compare", json={"a": a["run_id"], "b": b["run_id"]}).json()
    assert "confounds" in cmp or "deltas" in cmp


def test_integrity_dashboard():
    r = client.get("/api/integrity").json()
    assert r["questions_total"] >= 150
    assert r["notebooks_without_outputs"] is True


def test_assessment_arena():
    r = client.get("/api/assessment").json()
    assert r["pass_rule"] == 3
    assert "memory" in r["features"]


def test_concept_map():
    r = client.get("/api/concepts").json()
    assert len(r["nodes"]) >= 40
    assert r["edges"]
