import json

from google import genai
from google.genai import types
from pydantic import ValidationError

from ..models import JobPosting, JobPostingDraft
from ..states import ChatState

SYSTEM_PROMPT = """You are a friendly CV coach helping the user prepare for a job application.

Your goal is to gather enough information about the job the user is applying for to \
build a structured job posting profile:
- title (required): the job title
- company (optional): the hiring company, if mentioned
- location (optional): city/country or "Remote", if mentioned
- description (required): a concise summary of the role and its responsibilities
- requirements: key requirements/qualifications the user has shared
- nice_to_have: preferred/bonus qualifications, if mentioned
- keywords: generate relevant technologies, tools and domain terms for ATS/CV \
matching, based on everything gathered so far

You are given the job posting info collected so far and the conversation history. \
On each turn:
1. Extract any new details from the user's latest message and merge them with what \
is already known (do not drop previously known fields).
2. Set `ready` to true only once you have at least a clear title and a short \
description of the role. Otherwise set it to false.
3. If not ready, write a short, friendly `reply` asking specifically for the \
missing details (e.g. job title, company, a short description, key requirements).
4. If ready, fill in `keywords` with relevant ATS keywords inferred from the title, \
description and requirements, and write a short `reply` confirming you have what \
you need and will start tailoring the CV.

Only include information that was actually provided or that can be reasonably \
inferred (keywords). Do not invent companies, requirements, etc."""


def gather_job_posting(history: list[dict], instruction: str, job_posting: dict | None) -> JobPostingDraft:
    """Ask Gemini to merge the latest message into the job posting gathered so far."""
    client = genai.Client()
    context = {
        "known_job_posting": job_posting or {},
        "conversation_history": history,
        "latest_message": instruction,
    }
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=json.dumps(context),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
            response_mime_type="application/json",
            response_schema=JobPostingDraft,
        ),
    )
    parsed = response.parsed
    if parsed is None:
        raise ValueError(f"Failed to parse chat reply: {response.text}")
    return parsed


def chat_node(state: ChatState) -> ChatState:
    """LangGraph node: gathers job posting details from the conversation, asking
    follow-up questions until there's enough info to start tailoring the CV."""
    draft = gather_job_posting(
        state.get("history", []),
        state.get("instruction", ""),
        state.get("job_posting"),
    )

    job_posting = dict(state.get("job_posting") or {})
    for field in ("title", "company", "location", "description"):
        value = getattr(draft, field)
        if value:
            job_posting[field] = value
    for field in ("requirements", "nice_to_have", "keywords"):
        value = getattr(draft, field)
        if value:
            job_posting[field] = value

    ready = draft.ready
    if ready:
        try:
            JobPosting(**job_posting)
        except ValidationError:
            ready = False

    return {
        **state,
        "job_posting": job_posting,
        "ready": ready,
        "reply": draft.reply,
        "log": [],
        "ops": [],
    }


def run_enhance_node(state: ChatState) -> ChatState:
    """LangGraph node: runs the CV enhancement graph now that the job posting is ready,
    and surfaces its logs to the user."""
    from ..graph import agent  # deferred import: graph.py imports this module

    job_posting = JobPosting(**(state.get("job_posting") or {}))

    result = agent.invoke({
        "raw_cv": "",
        "sections": {},
        "current_section": "",
        "section_order": [],
        "user_profile": {},
        "target_role": job_posting.title,
        "job_description": None,
        "job_posting": job_posting.model_dump(),
        "messages": [],
        "final_cv": None,
    })

    log = [str(m) for m in (result.get("messages") or [])]
    if not log:
        log = [f"Started tailoring your CV for {job_posting.title}."]

    return {**state, "job_posting": job_posting.model_dump(), "log": log}


def close_chat_node(state: ChatState) -> ChatState:
    """LangGraph node: sends the completion reply once the CV enhancement run has finished."""
    job_posting = state.get("job_posting") or {}
    title = job_posting.get("title", "this role")
    company = job_posting.get("company")
    where = f" at {company}" if company else ""
    return {
        **state,
        "reply": (
            f"Got it — I've kicked off the CV tailoring for {title}{where}. "
            f"Check the log above for progress, and let me know if you'd like any edits."
        ),
    }
