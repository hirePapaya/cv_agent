import json
import logging
import time

from google import genai
from google.genai import types

from ..models import CurriculumVitae
from ..states import CVAgentState
from ..utils.rw import get_ats_rule, load_cv, update_cv_section

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a professional CV editor performing a final quality pass \
on a fully tailored CV.

Review the entire CV against the two rule sets below and return a corrected version.

--- COMMON ERRORS RULES ---
{common_errors_rules}

--- KEYWORD RULES ---
{keywords_rules}

Fix any issues you find. Preserve all factual information — do not change dates, \
company names, job titles, or degrees. Only correct errors, improve consistency, \
and strengthen keyword alignment where the candidate genuinely has the experience."""


def check_and_fix_cv(cv: CurriculumVitae, job_posting: dict) -> CurriculumVitae:
    common_errors_rules = get_ats_rule("common_errors")
    keywords_rules = get_ats_rule("keywords")
    logger.debug(
        "Loaded ATS rules — common_errors: %d chars, keywords: %d chars",
        len(common_errors_rules),
        len(keywords_rules),
    )

    client = genai.Client()
    contents = json.dumps({
        "cv": cv.model_dump(mode="json"),
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
            system_instruction=SYSTEM_PROMPT.format(
                common_errors_rules=common_errors_rules,
                keywords_rules=keywords_rules,
            ),
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=CurriculumVitae,
        ),
    )
    elapsed = time.perf_counter() - t0

    if response.parsed is None:
        raise ValueError(f"Failed to parse checked CV: {response.text}")
    logger.debug("general_check: LLM %.2fs", elapsed)
    return response.parsed


def general_check_node(state: CVAgentState) -> dict:
    """LangGraph node: final quality pass over the full CV using common_errors
    and keywords ATS rules. Runs after all section nodes complete."""
    job_posting = state.get("job_posting")
    if not job_posting:
        logger.warning("general_check_node skipped — no job_posting in state")
        return {}

    t_node = time.perf_counter()
    logger.info(
        "general_check_node: start — role=%r  running common_errors + keywords pass",
        job_posting.get("title", "unknown"),
    )

    cv = load_cv()
    logger.info(
        "general_check_node: CV loaded — %d jobs, %d education, %d skill categories",
        len(cv.experience.jobs),
        len(cv.education.entries),
        len(cv.skills.categories),
    )

    fixed_cv = check_and_fix_cv(cv, job_posting)

    update_cv_section(fixed_cv.profile)
    update_cv_section(fixed_cv.experience)
    update_cv_section(fixed_cv.education)
    update_cv_section(fixed_cv.skills)

    logger.info("general_check_node: done in %.2fs", time.perf_counter() - t_node)
    return {}
