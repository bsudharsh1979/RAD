from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.domains.twins.engine import run

bridge = FastAPI(title="Omniverse Twin Bridge")
bridge.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@bridge.get("/health")
def health():
    return {"ok": True, "omniverse_required": False}


@bridge.post("/state")
def push_state(payload: dict):
    scenario = payload.get("scenario") or "pipeline-flow"
    params = payload.get("params") or {}
    return run(scenario, params)


@bridge.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            msg = await websocket.receive_json()
            state = run(msg.get("scenario") or "pipeline-flow", msg.get("params") or {})
            await websocket.send_json(state)
    except WebSocketDisconnect:
        return
