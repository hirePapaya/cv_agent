from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from agent.cv_data import load_cv_studio_data
from agent.graph import agent, chat_agent

app = FastAPI(title="CV Studio Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

WELCOME_MESSAGE = (
    "Hi! I'm your CV Coach. Let's work together to make your résumé shine. "
    "To get started, paste the job posting you're targeting."
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


@app.get("/cv")
def get_cv() -> dict:
    try:
        return load_cv_studio_data()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="CV data not found")


@app.websocket("/ws/edit-cv")
async def edit_cv_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_json({"reply": WELCOME_MESSAGE, "log": [], "ops": []})

    job_posting: dict | None = None
    try:
        while True:
            payload = await websocket.receive_json() 
            instruction = payload.get("instruction", "")
            result = await run_in_threadpool(
                chat_agent.invoke,
                {
                    "cv": payload.get("cv", {}),
                    "history": payload.get("history", []),
                    "instruction": instruction,
                    "job_posting": job_posting,
                    "reply": "",
                    "log": [],
                    "ops": [],
                },
            )
            job_posting = result.get("job_posting")
            await websocket.send_json({
                "reply": result["reply"],
                "log": result["log"],
                "ops": result["ops"],
            })
    except WebSocketDisconnect:
        pass
