import json
import logging
import time

from google import genai
from google.genai import types

from ..models import ExperienceContent
from ..states import CVAgentState
from ..utils.rw import get_ats_rule, load_cv, update_cv_section

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a professional CV writer. Rewrite the work experience achievements \
to better target the job posting provided.

Rules you must follow:
{rules}

Preserve all factual details (company names, job titles, dates, locations). Only rewrite the \
achievements list items to use stronger action verbs and incorporate relevant keywords from the \
job posting. Do not invent new roles or experiences."""


def rewrite_experience(current: ExperienceContent, job_posting: dict) -> ExperienceContent:
    rules = get_ats_rule("work_experience")
    logger.debug("Loaded ATS rules for work_experience (%d chars)", len(rules))

    client = genai.Client()
    contents = json.dumps({
        "current_experience": current.model_dump(mode="json"),
        "job_title": job_posting.get("title", ""),
        "job_description": job_posting.get("description", ""),
        "requirements": job_posting.get("requirements", []),
        "keywords": job_posting.get("keywords", []),
    })

    t0 = time.perf_counter()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT.format(rules=rules),
            temperature=0.2,
            response_mime_type="application/json",
            response_schema=ExperienceContent,
        ),
    )
    elapsed = time.perf_counter() - t0

    if response.parsed is None:
        raise ValueError(f"Failed to parse rewritten experience: {response.text}")
    result = response.parsed
    total_bullets = sum(len(j.achievements) for j in result.jobs)
    logger.debug(
        "experience: LLM %.2fs — %d jobs, %d bullets total",
        elapsed, len(result.jobs), total_bullets,
    )
    return result


def experience_node(state: CVAgentState) -> dict:
    """LangGraph node: rewrites work experience and persists it to output.json."""
    job_posting = state.get("job_posting")
    if not job_posting:
        logger.warning("experience_node skipped — no job_posting in state")
        return {}

    t_node = time.perf_counter()
    logger.info("experience_node: start — role=%r", job_posting.get("title", "unknown"))

    cv = load_cv()
    logger.info(
        "experience_node: rewriting %d jobs",
        len(cv.experience.jobs),
    )
    updated = rewrite_experience(cv.experience, job_posting)
    update_cv_section(updated)

    logger.info("experience_node: done in %.2fs", time.perf_counter() - t_node)
    return {}
