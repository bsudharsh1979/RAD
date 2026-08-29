# NVIDIA Omniverse / NVCF deployment

Keep this stack **separate** from Vercel/web.

The learning app does **not** require Omniverse, NIM GPUs, or NVCF.

## Suggested topology

1. Run `services/api` with TwinStateEngine.
2. Run `services/omniverse-bridge` (`uvicorn main:bridge --app-dir services/omniverse-bridge --port 8010` with `PYTHONPATH=services/api`).
3. Kit extension subscribes to `ws://bridge:8010/ws`.
4. Stream the viewport with Omniverse Streaming or NVCF when you have a Kit app to vendor.

## Environment

```
OMNIVERSE_BRIDGE_URL=http://localhost:8010
NVCF_API_KEY=
```

Until a Kit repo is added under `integrations/omniverse-twin`, the Settings page will show Omniverse as offline. That is expected.
