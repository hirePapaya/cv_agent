import asyncio
import logging

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from agent.cv_data import load_cv_studio_data
from agent.graph import agent, chat_agent
from agent.models import ProfileContent, ExperienceContent, EducationContent, SkillsContent
from agent.utils.rw import update_cv_section

logger = logging.getLogger(__name__)

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


@app.patch("/cv/profile")
def patch_profile(body: ProfileContent) -> dict:
    update_cv_section(body)
    return load_cv_studio_data()


@app.patch("/cv/experience")
def patch_experience(body: ExperienceContent) -> dict:
    update_cv_section(body)
    return load_cv_studio_data()


@app.patch("/cv/education")
def patch_education(body: EducationContent) -> dict:
    update_cv_section(body)
    return load_cv_studio_data()


@app.patch("/cv/skills")
def patch_skills(body: SkillsContent) -> dict:
    update_cv_section(body)
    return load_cv_studio_data()


@app.websocket("/ws/edit-cv")
async def edit_cv_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_json({"reply": WELCOME_MESSAGE, "log": [], "ops": []})

    loop = asyncio.get_event_loop()
    job_posting: dict | None = None

    try:
        while True:
            payload = await websocket.receive_json()
            instruction = payload.get("instruction", "")

            # Phase 1: gather job posting info via chat
            chat_result = await run_in_threadpool(
                chat_agent.invoke,
                {
                    "message": instruction,
                    "history": payload.get("history", []),
                    "instruction": instruction,
                    "job_posting": job_posting,
                    "ready": False,
                    "reply": "",
                    "log": [],
                    "ops": [],
                },
            )
            job_posting = chat_result.get("job_posting")

            await websocket.send_json({
                "reply": chat_result["reply"],
                "log": chat_result.get("log", []),
                "ops": chat_result.get("ops", []),
            })

            if not chat_result.get("ready"):
                continue

            # Phase 2: stream cv_enhance_graph — send cv_updated after each node
            logger.info("Starting CV enhancement stream for job: %s", (job_posting or {}).get("title"))

            def stream_enhance():
                for event in agent.stream({
                    "raw_cv": "",
                    "sections": {},
                    "current_section": "",
                    "section_order": [],
                    "user_profile": {},
                    "target_role": (job_posting or {}).get("title"),
                    "job_description": None,
                    "job_posting": job_posting,
                    "messages": [],
                    "final_cv": None,
                }):
                    for node_name in event:
                        if node_name.startswith("__") or node_name == "finish":
                            continue
                        logger.info("cv_enhance_graph node done: %s", node_name)
                        asyncio.run_coroutine_threadsafe(
                            websocket.send_json({"type": "cv_updated", "section": node_name}),
                            loop,
                        ).result()

            await run_in_threadpool(stream_enhance)

            title = (job_posting or {}).get("title", "this role")
            company = (job_posting or {}).get("company")
            where = f" at {company}" if company else ""
            await websocket.send_json({
                "reply": (
                    f"Done! I've tailored your CV for {title}{where}. "
                    "Let me know if you'd like any adjustments."
                ),
                "log": [f"Tailored CV for {title}{where}."],
                "ops": [],
            })

    except WebSocketDisconnect:
        pass
