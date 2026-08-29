# NVIDIA runtime scaffolding

Place NIM containers, future Dynamo jobs, and NVCF functions here — not in `apps/web`.

Example NIM compose fragment:

```yaml
nim:
  image: nvcr.io/nim/meta/llama-3.1-8b-instruct:latest
  environment:
    NGC_API_KEY: ${NVIDIA_API_KEY}
  ports: ["8001:8000"]
```

Point the academy at it:

```
NIM_BASE_URL=http://localhost:8001/v1
NVIDIA_API_KEY=...
```

The tutor settings UI will show NVIDIA NIM as connected only when those variables are set. Offline NIM never silently becomes OpenAI.
