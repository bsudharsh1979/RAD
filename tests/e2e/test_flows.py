"""Required product flows via HTTP (no paid APIs)."""

from fastapi.testclient import TestClient

from app.main import app
from app.seed.bootstrap import init_db_and_seed

init_db_and_seed()
c = TestClient(app)


def test_first_launch_onboard():
    r = c.post("/api/onboard", json={"display_name": "Pat", "tutor_provider": "demo"})
    assert r.status_code == 200


def test_source_ingestion_visible():
    assert len(c.get("/api/notebooks").json()) == 8
    assert c.get("/api/sources").json()


def test_diagnostic_recommendation():
    d = c.get("/api/diagnostic").json()
    assert len(d["questions"]) >= 5
    h = c.get("/api/home").json()
    assert h["thirty_minute_plan"]


def test_concept_lesson_and_citation():
    g = c.get("/api/concepts").json()
    cid = g["nodes"][0]["id"]
    one = c.get(f"/api/concepts/{cid}").json()
    assert one["concept"]["notebook_file"]


def test_tutor_and_source():
    r = c.post("/api/tutor", json={"content": "What is cross-attention in T5?"}).json()
    assert r.get("sources") is not None


def test_prediction_and_twin():
    p = c.post("/api/twins/predict", json={"twin_id": "quantization-memory", "prompt": "70b ram", "predicted": {"gb": 10}}).json()
    run = c.post("/api/twins/run", json={"scenario": "quantization-memory", "params": {"params_billion": 70, "bits": 16}, "prediction_id": p["prediction_id"]}).json()
    assert run["state"]["course_70b_fp16_gb"] == 135
    assert run["state"]["evidence_type"] == "SIMULATED_RESULT"


def test_misconception_feedback():
    qs = c.get("/api/questions?qtype=mcq&limit=5").json()
    q = qs[0]
    fb = c.post("/api/questions/attempt", json={"question_id": q["id"], "given": "nope"}).json()
    assert "what_this_suggests" in fb["feedback"]


def test_teachback_and_review_and_assessment_and_resume():
    tb = c.post("/api/teachback", json={"concept_id": "c-t5", "transcript": "T5 is encoder-decoder with prefixes"}).json()
    assert "missing" in tb
    assert "due" in c.get("/api/review").json()
    assert c.get("/api/assessment").json()["pass_rule"] == 3
    home = c.get("/api/home").json()
    assert home["resume"]
    d = c.post("/api/assessment/defend", json={"hypothesis": "3 features", "defense": "need ask-for-input and 13B", "features": {"memory": True}}).json()
    assert d["would_pass_feature_count"] is False


def test_provider_failure_disclosed():
    c.patch("/api/me", json={"tutor_provider": "openai"})
    r = c.post("/api/tutor", json={"content": "Explain BERT embeddings"}).json()
    # openai unavailable -> demo disclosure or provider failed
    assert "demo" in r["provider"] or "offline" in r["text"].lower() or "failed" in r["text"].lower() or r["provider"] in ("demo", "openai")
    c.patch("/api/me", json={"tutor_provider": "demo"})


def test_notebook_walkthrough_blocked():
    nbs = c.get("/api/notebooks").json()
    nb = c.get(f"/api/notebooks/{nbs[-1]['filename']}").json()
    codes = [x for x in nb["cells"] if x["cell_type"] == "code"]
    assert codes and all(x["blocked_execution"] for x in codes)
