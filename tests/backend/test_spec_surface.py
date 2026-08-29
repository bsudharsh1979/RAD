"""80+ API tests for deterministic ids, walkthroughs, TTS clip=false, CORS."""

from __future__ import annotations

import os
import re
import shutil
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.domains.walkthrough.engine import STEP_KINDS, build_walkthrough, structure_kinds
from app.domains.walkthrough.frames import FRAMES
from app.domains.walkthrough.glossary import GLOSSARY, apply_glossary
from app.domains.walkthrough.speech import JARGON_BLOCKLIST_SIMPLE, clip_text, humanize_title, speak_normalize
from app.ids import artifact_id, notebook_id, span_id
from app.main import app
from app.seed.concepts import CONCEPTS
from app.seed.questions import all_questions

client = TestClient(app)

NOTEBOOKS = [
    "01_llm_intro.ipynb",
    "02_llm_intake.ipynb",
    "03_encoder_task.ipynb",
    "04_seq2seq.ipynb",
    "05_multimodal.ipynb",
    "06_textgen.ipynb",
    "07_stateful_models.ipynb",
    "08_assessment.ipynb",
]


def test_health_and_setup():
    h = client.get("/api/health")
    assert h.status_code == 200
    s = client.get("/api/setup").json()
    assert s["zero_key_demo"] is True
    assert "not affiliated" in s["disclaimer"].lower()


def test_cors_regex_allows_modal():
    r = client.options(
        "/api/health",
        headers={
            "Origin": "https://llm-twin-academy-web-dev.modal.run",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert r.headers.get("access-control-allow-origin")


def test_cors_regex_allows_localhost():
    r = client.options(
        "/api/health",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
    )
    assert r.headers.get("access-control-allow-origin")


def test_notebooks_list_eight():
    nbs = client.get("/api/notebooks").json()
    assert len(nbs) == 8
    assert {n["filename"] for n in nbs} == set(NOTEBOOKS)


def test_ids_are_sha1_not_uuid():
    nbs = client.get("/api/notebooks").json()
    sha = re.compile(r"^[0-9a-f]{40}$")
    for n in nbs:
        assert sha.match(n["id"]), n["id"]


def test_name_fallback_and_stable_detail():
    nbs = client.get("/api/notebooks").json()
    one = nbs[0]
    by_id = client.get(f"/api/notebooks/{one['id']}")
    by_name = client.get(f"/api/notebooks/{one['filename']}")
    assert by_id.status_code == 200
    assert by_name.status_code == 200
    assert by_id.json()["id"] == by_name.json()["id"] == one["id"]
    again = client.get(f"/api/notebooks/{one['id']}")
    assert again.json()["id"] == one["id"]


def test_stale_notebook_404_explains():
    r = client.get("/api/notebooks/not-a-real-notebook")
    assert r.status_code == 404
    assert "stale" in r.text.lower() or "sha1" in r.text.lower() or "unknown notebook" in r.text.lower()


def test_stale_source_404_explains():
    r = client.get("/api/sources/missing-file.pdf")
    assert r.status_code == 404
    assert "sha1" in r.text.lower() or "unknown source" in r.text.lower()


def test_ids_stable_across_two_fresh_dbs():
    from app.config import settings
    from app.db.models import Base, Notebook
    from app.ingestion.engine import ingest_course_materials

    ids = []
    for _ in range(2):
        tmp = tempfile.mkdtemp()
        url = "sqlite:///" + str(Path(tmp) / "t.db")
        engine = create_engine(url)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        db = Session()
        try:
            ingest_course_materials(db)
            rows = db.query(Notebook).order_by(Notebook.filename).all()
            ids.append([(n.filename, n.id) for n in rows])
        finally:
            db.close()
            engine.dispose()
            shutil.rmtree(tmp, ignore_errors=True)
    assert ids[0] == ids[1]
    assert len(ids[0]) == 8
    _ = settings  # keep import used


def test_artifact_and_span_helpers():
    a = artifact_id("notebooks/01_llm_intro.ipynb")
    b = artifact_id("notebooks/01_llm_intro.ipynb")
    assert a == b
    assert len(a) == 40
    s1 = span_id(a, "cell:0", "markdown", 0)
    s2 = span_id(a, "cell:0", "markdown", 0)
    assert s1 == s2
    assert notebook_id("notebooks/01_llm_intro.ipynb") != a


@pytest.mark.parametrize("fname", NOTEBOOKS)
@pytest.mark.parametrize("depth", ["simple", "expert"])
def test_walkthrough_both_depths(fname, depth):
    r = client.get(f"/api/notebooks/{fname}/walkthrough", params={"depth": depth})
    assert r.status_code == 200
    body = r.json()
    assert body["depth"] == depth
    kinds = [s["kind"] for s in body["steps"]]
    assert kinds[0] == "big_idea"
    assert "model" in kinds
    assert "game_plan" in kinds
    assert "stage" in kinds
    assert kinds[-1] == "one_thing"
    assert body["steps"]


@pytest.mark.parametrize("fname", NOTEBOOKS)
def test_walkthrough_structure_parity(fname):
    simple = client.get(f"/api/notebooks/{fname}/walkthrough", params={"depth": "simple"}).json()
    expert = client.get(f"/api/notebooks/{fname}/walkthrough", params={"depth": "expert"}).json()
    assert structure_kinds(simple["steps"]) == structure_kinds(expert["steps"])
    assert [s["kind"] for s in simple["steps"]] == [s["kind"] for s in expert["steps"]]


@pytest.mark.parametrize("fname", NOTEBOOKS)
def test_walkthrough_range_coverage(fname):
    n = client.get(f"/api/notebooks/{fname}").json()
    n_cells = len(n["cells"])
    wt = client.get(f"/api/notebooks/{fname}/walkthrough").json()
    covered = set()
    for s in wt["steps"]:
        if s["kind"] == "stage":
            for i in range(s["cell_start"], s["cell_end"] + 1):
                covered.add(i)
    missing = [i for i in range(n_cells) if i not in covered]
    assert not missing, missing


@pytest.mark.parametrize("fname", NOTEBOOKS)
def test_frames_and_simple_model_complete(fname):
    frame = FRAMES[fname]
    assert frame["simple_model"].strip()
    assert frame["expert_model"].strip()
    assert frame["game_plan"].strip()
    assert frame["one_thing"].strip()
    assert frame["big_idea"]["hook"]
    assert frame["stages"]
    nb = client.get(f"/api/notebooks/{fname}").json()
    n = len(nb["cells"])
    last = max(st["end"] for st in frame["stages"])
    assert last >= n - 1


def test_walkthrough_default_is_simple():
    r = client.get("/api/notebooks/01_llm_intro.ipynb/walkthrough").json()
    assert r["depth"] == "simple"


def test_simple_mode_glossary_once_only():
    r = client.get("/api/notebooks/01_llm_intro.ipynb/walkthrough?depth=simple").json()
    blob = " ".join(s["narration"] for s in r["steps"])
    for term, _gloss in GLOSSARY:
        if f"{term} (" in blob:
            assert blob.count(f"{term} (") == 1, term


def test_simple_mode_blocks_inference_jargon():
    r = client.get("/api/notebooks/07_stateful_models.ipynb/walkthrough?depth=simple").json()
    blob = " ".join(s["narration"] for s in r["steps"]).lower()
    for banned in JARGON_BLOCKLIST_SIMPLE:
        assert banned not in blob, banned


@pytest.mark.parametrize("fname", NOTEBOOKS)
def test_simple_stage_compression_bound(fname):
    r = client.get(f"/api/notebooks/{fname}/walkthrough?depth=simple").json()
    for s in r["steps"]:
        if s["kind"] == "stage":
            assert len(s["narration"]) <= 640


def test_speech_naturalness_helpers():
    assert "then" in speak_normalize("A → B")
    assert "equals" in speak_normalize("reward = 1 - toxicity")
    assert "of" in speak_normalize("3/5 features")
    assert "or" in speak_normalize("t5/flan")
    assert "?" in speak_normalize("What?.")
    assert not humanize_title("2.3.4.1 Decoder steps").startswith("2")


def test_headings_not_read_twice_in_title():
    t = humanize_title("2.3.4.1 The model")
    assert t == "The model"


def test_tts_clip_false_never_truncates():
    long = "word " * 400
    r = client.post("/api/voice/tts", json={"text": long, "clip": False, "provider": "auto"}).json()
    assert r["truncated"] is False
    assert r["char_count"] == len(long)
    assert r["text"] == long
    assert clip_text(long, clip=False) == long
    assert len(clip_text(long, clip=True, limit=520)) == 520


def test_voice_status_and_stt():
    st = client.get("/api/voice/status").json()
    assert st["browser_fallback"] == "available"
    s = client.post("/api/voice/stt", json={"note": "browser"}).json()
    assert s["ok"] is False


def test_risks_catalog():
    rows = client.get("/api/risks").json()
    assert 15 <= len(rows) <= 25
    assert all(r.get("twin") and r.get("leading_signal") for r in rows)


def test_lessons_list_and_detail():
    rows = client.get("/api/lessons").json()
    assert len(rows) >= 40
    one = client.get(f"/api/lessons/{rows[0]['id']}").json()
    assert one["steps"]


def test_concepts_have_analogy_and_count():
    g = client.get("/api/concepts").json()
    assert len(g["nodes"]) >= 90
    assert all(n.get("analogy") for n in g["nodes"])
    one = client.get(f"/api/concepts/{g['nodes'][0]['id']}").json()
    assert one["concept"]["analogy"]


def test_question_bank_500():
    assert len(all_questions()) >= 500
    assert len(CONCEPTS) >= 90


def test_twins_include_suggestions_and_alias_run():
    rows = client.get("/api/twins").json()
    assert any(t["id"] == "incident-diagnosis" for t in rows)
    t = next(x for x in rows if x["id"] == "pipeline-flow")
    assert t["suggested"]
    r = client.post("/api/twins/pipeline-flow/run", json={"params": {"n_tokens": 6}}).json()
    assert r["state"]["evidence_type"] == "SIMULATED_RESULT"
    hidden = client.post(
        "/api/twins/incident-diagnosis/run",
        json={"params": {"symptom": "second_turn_amnesia", "committed": False}},
    ).json()
    assert hidden["state"]["ground_truth"] is None


def test_spans_and_sources():
    arts = client.get("/api/sources").json()
    assert arts
    src = client.get(f"/api/sources/{arts[0]['file']}").json()
    assert src["spans"]
    sid = src["spans"][0]["id"]
    span = client.get(f"/api/spans/{sid}")
    assert span.status_code == 200
    assert span.json()["evidence_type"] == "COURSE_SOURCE"


def test_learning_reviews_due_alias():
    r = client.get("/api/learning/reviews/due")
    assert r.status_code == 200
    assert "due" in r.json()


def test_tutor_session_sse():
    s = client.post("/api/tutor/sessions", json={"mode": "COURSE"}).json()
    assert s["session_id"]
    r = client.post(
        f"/api/tutor/sessions/{s['session_id']}/messages",
        json={"content": "What is a HuggingFace pipeline?", "provider": "demo"},
    )
    assert r.status_code == 200
    assert "text" in r.text or "event:" in r.text


def test_business_impact_tab_present():
    n = client.get("/api/notebooks/01_llm_intro.ipynb").json()
    code = next(c for c in n["cells"] if c["cell_type"] == "code")
    assert "BUSINESS_IMPACT" in code["tabs"]
    assert code["tabs"]["BUSINESS_IMPACT"]


def test_cell_commentary_never_execute():
    n = client.get("/api/notebooks/01_llm_intro.ipynb").json()
    for c in n["cells"]:
        if c["cell_type"] == "code":
            assert c["blocked_execution"] is True


def test_search_and_meta_nav():
    s = client.get("/api/search", params={"q": "pipeline"}).json()
    assert s
    m = client.get("/api/meta").json()
    assert "risks" in m["nav"]


def test_walkthrough_unknown_notebook_404():
    r = client.get("/api/notebooks/nope.ipynb/walkthrough")
    assert r.status_code == 404


def test_glossary_skips_title_case():
    steps = apply_glossary([{"narration": "Pipeline is Title Case here and pipeline appears later."}])
    text = steps[0]["narration"]
    assert text.count("pipeline (") == 1


def test_build_walkthrough_kinds_order():
    cells = [{"cell_index": i} for i in range(25)]
    concepts = [{"id": "c-pipeline", "name": "Pipeline", "school": "school", "research": "research", "analogy": "drawer"}]
    w = build_walkthrough("01_llm_intro.ipynb", cells, concepts, depth="simple")
    kinds = structure_kinds(w["steps"])
    assert kinds[0] == "big_idea"
    assert kinds[-1] == "one_thing"
    assert set(STEP_KINDS) <= set(kinds) | {"concept"}


@pytest.mark.parametrize("fname", NOTEBOOKS)
def test_simple_and_expert_differ_on_model_step(fname):
    s = client.get(f"/api/notebooks/{fname}/walkthrough?depth=simple").json()
    e = client.get(f"/api/notebooks/{fname}/walkthrough?depth=expert").json()
    sm = next(x["narration"] for x in s["steps"] if x["kind"] == "model")
    em = next(x["narration"] for x in e["steps"] if x["kind"] == "model")
    assert sm != em


@pytest.mark.parametrize("fname", NOTEBOOKS)
def test_no_double_question_punct(fname):
    for depth in ("simple", "expert"):
        body = client.get(f"/api/notebooks/{fname}/walkthrough", params={"depth": depth}).json()
        for step in body["steps"]:
            assert "?." not in step["narration"]


@pytest.mark.parametrize("tid", ["pipeline-flow", "quantization-memory", "incident-diagnosis", "risk-radar", "assessment-agent"])
def test_twin_alias_and_catalog(tid):
    rows = {t["id"]: t for t in client.get("/api/twins").json()}
    assert tid in rows
    assert 3 <= len(rows[tid]["suggested"]) <= 6
    r = client.post(f"/api/twins/{tid}/run", json={"params": rows[tid]["suggested"][0]["params"]})
    assert r.status_code == 200
    assert r.json()["state"]["evidence_type"] == "SIMULATED_RESULT"


def test_integrity_and_misconceptions():
    integ = client.get("/api/integrity").json()
    assert integ["questions_total"] >= 500
    misc = client.get("/api/misconceptions").json()
    assert 15 <= len(misc) <= 30


def test_providers_still_demo():
    r = client.get("/api/providers").json()
    assert r["status"]["demo"] == "connected"
