import json
import logging
import time

from google import genai
from google.genai import types

from ..models import SkillsContent
from ..states import CVAgentState
from ..utils.rw import get_ats_rule, load_cv, update_cv_section

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a professional CV writer. Update the skills section to better \
match the target job posting, maximising ATS keyword coverage.

Rules you must follow:
{rules}

Keep existing skills that are still relevant. Add missing skills from the job requirements \
that the candidate plausibly has based on their experience. Remove or de-emphasise skills \
that are irrelevant to the target role. Do not invent skills the candidate clearly does not have."""


def rewrite_skills(current: SkillsContent, job_posting: dict) -> SkillsContent:
    rules = get_ats_rule("skills")
    logger.debug("Loaded ATS rules for skills (%d chars)", len(rules))

    client = genai.Client()
    contents = json.dumps({
        "current_skills": current.model_dump(mode="json"),
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
            response_schema=SkillsContent,
        ),
    )
    elapsed = time.perf_counter() - t0

    if response.parsed is None:
        raise ValueError(f"Failed to parse rewritten skills: {response.text}")
    result = response.parsed
    category_names = list(result.categories.keys())
    logger.debug(
        "skills: LLM %.2fs — %d categories: %s",
        elapsed, len(category_names), ", ".join(category_names),
    )
    return result


def skills_node(state: CVAgentState) -> dict:
    """LangGraph node: rewrites skills section and persists it to output.json."""
    job_posting = state.get("job_posting")
    if not job_posting:
        logger.warning("skills_node skipped — no job_posting in state")
        return {}

    t_node = time.perf_counter()
    logger.info("skills_node: start — role=%r", job_posting.get("title", "unknown"))

    cv = load_cv()
    logger.info(
        "skills_node: rewriting %d skill categories",
        len(cv.skills.categories),
    )
    updated = rewrite_skills(cv.skills, job_posting)
    update_cv_section(updated)

    logger.info("skills_node: done in %.2fs", time.perf_counter() - t_node)
    return {}
