import json
import logging
import time

from google import genai
from google.genai import types

from ..models import EducationContent
from ..states import CVAgentState
from ..utils.rw import get_ats_rule, load_cv, update_cv_section

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a professional CV writer. Review the education section and ensure \
it is formatted and framed to best support the target job posting.

Rules you must follow:
{rules}

Preserve all factual data (institution names, degrees, dates, GPA). You may add or improve \
a brief description field if it helps highlight relevant coursework or achievements for the \
target role. Do not invent qualifications."""


def rewrite_education(current: EducationContent, job_posting: dict) -> EducationContent:
    rules = get_ats_rule("education")
    logger.debug("Loaded ATS rules for education (%d chars)", len(rules))

    client = genai.Client()
    contents = json.dumps({
        "current_education": current.model_dump(mode="json"),
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
            response_schema=EducationContent,
        ),
    )
    elapsed = time.perf_counter() - t0
    if response.parsed is None:
        raise ValueError(f"Failed to parse rewritten education: {response.text}")
    result = response.parsed
    logger.debug(
        "education: LLM %.2fs — %d entries",
        elapsed, len(result.entries),
    )
    return result


def education_node(state: CVAgentState) -> dict:
    """LangGraph node: rewrites education section and persists it to output.json."""
    job_posting = state.get("job_posting")
    if not job_posting:
        logger.warning("education_node skipped — no job_posting in state")
        return {}

    t_node = time.perf_counter()
    logger.info("education_node: start — role=%r", job_posting.get("title", "unknown"))

    cv = load_cv()
    logger.info(
        "education_node: rewriting %d education entries",
        len(cv.education.entries),
    )
    updated = rewrite_education(cv.education, job_posting)
    update_cv_section(updated)

    logger.info("education_node: done in %.2fs", time.perf_counter() - t_node)
    return {}
