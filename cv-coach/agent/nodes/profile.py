import json
import logging

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

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT.format(rules=rules),
            temperature=0.2,
            response_mime_type="text/plain",
        ),
    )

    rewritten = response.text.strip()
    logger.debug("Rewritten profile summary (%d chars)", len(rewritten))
    return ProfileContent(text=rewritten)


def profile_node(state: CVAgentState) -> CVAgentState:
    """LangGraph node: rewrites the profile summary and persists it to output.json."""
    job_posting = state.get("job_posting")
    if not job_posting:
        logger.warning("profile_node skipped — no job_posting in state")
        return state

    logger.info("profile_node: loading current CV profile")
    cv = load_cv()
    logger.info(
        "profile_node: rewriting profile for role '%s'",
        job_posting.get("title", "unknown"),
    )

    updated_profile = rewrite_profile(cv.profile.text, job_posting)

    logger.info("profile_node: persisting updated profile to output.json")
    update_cv_section(updated_profile)

    logger.info("profile_node: done")
    return {
        **state,
        "current_section": "profile",
    }
