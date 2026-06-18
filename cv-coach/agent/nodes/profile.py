import json
import logging
import time

from google import genai
from google.genai import types

from ..models import ProfileContent
from ..states import CVAgentState
from ..utils.rw import get_ats_rule, load_cv, update_cv_section

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a professional CV writer. Rewrite the candidate's \
professional summary so it better targets the job posting provided.

Rules you must follow:
{rules}

Return ONLY the rewritten summary text — no labels, no extra commentary."""


def rewrite_profile(current_text: str, job_posting: dict) -> ProfileContent:
    rules = get_ats_rule("professional_summary")
    logger.debug("Loaded ATS rules for professional_summary (%d chars)", len(rules))

    client = genai.Client()
    contents = json.dumps({
        "current_summary": current_text,
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
            response_mime_type="text/plain",
        ),
    )
    elapsed = time.perf_counter() - t0

    rewritten = response.text.strip()
    logger.debug(
        "profile: LLM %.2fs — %d chars → %d chars",
        elapsed, len(current_text), len(rewritten),
    )
    return ProfileContent(text=rewritten)


def profile_node(state: CVAgentState) -> dict:
    """LangGraph node: rewrites the profile summary and persists it to output.json."""
    job_posting = state.get("job_posting")
    if not job_posting:
        logger.warning("profile_node skipped — no job_posting in state")
        return {}

    t_node = time.perf_counter()
    logger.info("profile_node: start — role=%r", job_posting.get("title", "unknown"))

    cv = load_cv()
    updated_profile = rewrite_profile(cv.profile.text, job_posting)
    update_cv_section(updated_profile)

    logger.info("profile_node: done in %.2fs", time.perf_counter() - t_node)
    return {}
