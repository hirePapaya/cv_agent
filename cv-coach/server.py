from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from agent.graph import cv_editor_agent

app = FastAPI(title="CV Studio Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatTurn(BaseModel):
    role: str
    text: str


class EditCvRequest(BaseModel):
    cv: dict
    history: list[ChatTurn] = []
    instruction: str


class EditCvResponse(BaseModel):
    reply: str
    log: list[str]
    ops: list[dict]


@app.post("/edit-cv", response_model=EditCvResponse)
def edit_cv(request: EditCvRequest) -> EditCvResponse:
    result = cv_editor_agent.invoke({
        "cv": request.cv,
        "history": [turn.model_dump() for turn in request.history],
        "instruction": request.instruction,
        "reply": "",
        "log": [],
        "ops": [],
    })
    return EditCvResponse(reply=result["reply"], log=result["log"], ops=result["ops"])


@app.websocket("/ws/edit-cv")
async def edit_cv_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            payload = await websocket.receive_json()
            result = await run_in_threadpool(
                cv_editor_agent.invoke,
                {
                    "cv": payload.get("cv", {}),
                    "history": payload.get("history", []),
                    "instruction": payload.get("instruction", ""),
                    "reply": "",
                    "log": [],
                    "ops": [],
                },
            )
            await websocket.send_json({
                "reply": result["reply"],
                "log": result["log"],
                "ops": result["ops"],
            })
    except WebSocketDisconnect:
        pass
