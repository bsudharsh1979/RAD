# Launch runbook — LLM Twin Academy

Not affiliated with or endorsed by NVIDIA. `course-materials/` is bring-your-own, personal-use licensed content.

## Local (zero keys)

```bash
python3 -m pip install -r services/api/requirements.txt
python3 -m pip install -e services/twin-engine
cd apps/web && npm install && cd ../..
./scripts/dev.sh
```

Open http://localhost:3000 — start, then open **The model that hides its homework**.

## Tests

```bash
PYTHONPATH=services/api:services/twin-engine pytest tests -q
cd apps/web && npm run lint && npm run build
```

## Modal (live)

Profile: `gamgn` (the authenticated Modal CLI profile on the machine that deploys).

App names: `llm-twin-academy-api` and `llm-twin-academy-web`.

Current deployment:

- **API:** https://gamgn--llm-twin-academy-api-fastapi-app.modal.run
- **Web:** https://gamgn--llm-twin-academy-web-web.modal.run
- Dashboards: [API](https://modal.com/apps/gamgn/main/deployed/llm-twin-academy-api) · [Web](https://modal.com/apps/gamgn/main/deployed/llm-twin-academy-web)

The Next.js image bakes `NEXT_PUBLIC_API_BASE` at build time. Redeploy web whenever the API URL changes.

Keep `MODAL_MIN_CONTAINERS=0` after the first live check so both apps stay inside the Modal $30 credit. Cold start is expected.

Create an empty-ok secret once:

```bash
modal secret create academy-env --force || true
```

If `academy-env` already exists, skip.

Keep `MODAL_MIN_CONTAINERS=0` after the first live check so both apps stay inside the Modal $30 credit.

### 1. API

```bash
MODAL_MIN_CONTAINERS=1 MODAL_MAX_CONTAINERS=1 modal deploy deploy/modal/modal_app.py
```

Copy the printed `*.modal.run` URL. That is `API_URL`.

### 2. Web (requires the API URL)

```bash
NEXT_PUBLIC_API_BASE="$API_URL" MODAL_MIN_CONTAINERS=1 MODAL_MAX_CONTAINERS=1 \
  modal deploy deploy/modal/modal_web.py
```

`NEXT_PUBLIC_API_BASE` is required. The image build hard-exits if it is unset.

### 3. Verify live

```bash
API_URL=https://<api>.modal.run
WEB_URL=https://<web>.modal.run

curl -sS "$API_URL/api/notebooks" | python3 -m json.tool | head
ID=$(python3 -c "import json,sys,urllib.request; print(json.load(urllib.request.urlopen('$API_URL/api/notebooks'))[0]['id'])")
curl -sS -o /tmp/nb1.json -w "%{http_code}" "$API_URL/api/notebooks/$ID"
echo
curl -sS -o /tmp/nb2.json -w "%{http_code}" "$API_URL/api/notebooks/$ID"
python3 -c "import json; a=json.load(open('/tmp/nb1.json')); b=json.load(open('/tmp/nb2.json')); assert a['id']==b['id']"
curl -sS -o /dev/null -w "%{http_code}" "$API_URL/api/notebooks/01_llm_intro.ipynb"
echo
curl -sS "$API_URL/api/notebooks/01_llm_intro.ipynb/walkthrough" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['depth']=='simple'; print(len(d['steps']),'simple steps')"
curl -sS "$API_URL/api/notebooks/01_llm_intro.ipynb/walkthrough?depth=expert" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['depth']=='expert'; print(len(d['steps']),'expert steps')"
curl -sS "$API_URL/api/voice/status"
curl -sS -o /dev/null -w "%{http_code}\n" "$WEB_URL/notebooks"
```

### 4. Scale back to idle (credits)

```bash
MODAL_MIN_CONTAINERS=0 MODAL_MAX_CONTAINERS=1 modal deploy deploy/modal/modal_app.py
NEXT_PUBLIC_API_BASE="$API_URL" MODAL_MIN_CONTAINERS=0 MODAL_MAX_CONTAINERS=1 \
  modal deploy deploy/modal/modal_web.py
```

SQLite is pinned to `max_containers=1` plus `@modal.concurrent(max_inputs=100)`. Do not raise `MODAL_MAX_CONTAINERS` while using SQLite.

## Five-step demo path

1. Home → start (Demo or NIM) → pick **The model that hides its homework**.
2. Read the moving parts → Hear the lecture (`?walkthrough=1`) → SIMPLE, then EXPERT.
3. Run the **HuggingFace Pipeline** twin: lock a prediction, then run.
4. Tutor: ask “What actually happens between the sentence I type and the [MASK] guess?”
5. Next story: **Why the chatbot forgot your name** → Incident diagnosis twin → commit a cause.
