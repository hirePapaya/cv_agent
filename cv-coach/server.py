from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

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


@app.websocket("/ws/edit-cv")
async def edit_cv_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_json({"reply": WELCOME_MESSAGE, "log": [], "ops": []})

    job_posting: dict | None = None
    try:
        while True:
            payload = await websocket.receive_json()
            instruction = payload.get("instruction", "")

            if job_posting is None:
                result = await run_in_threadpool(agent.invoke, {"job_description": instruction})
                job_posting = result.get("job_posting") or {}
                title = job_posting.get("title") or "this role"
                company = job_posting.get("company")
                where = f" at {company}" if company else ""
                await websocket.send_json({
                    "reply": f"Got it — I'll tailor your CV for {title}{where}. Tell me what to edit.",
                    "log": ["Parsed the job posting."],
                    "ops": [],
                })
                continue

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
            await websocket.send_json({
                "reply": result["reply"],
                "log": result["log"],
                "ops": result["ops"],
            })
    except WebSocketDisconnect:
        pass
