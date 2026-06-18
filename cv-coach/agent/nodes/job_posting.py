import logging
import time

from google import genai
from google.genai import types

from ..models import JobPosting
from ..states import CVAgentState

logger = logging.getLogger(__name__)


def parse_job_posting(raw_text: str) -> JobPosting:
    """Parse a raw job posting string into a structured JobPosting."""
    logger.debug("job_posting: sending %d chars to Gemini", len(raw_text))
    client = genai.Client()
    t0 = time.perf_counter()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=raw_text,
        config=types.GenerateContentConfig(
            system_instruction="Extract structured information from the job posting. Only use information present in the text.",
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=JobPosting,
        ),
    )
    elapsed = time.perf_counter() - t0
    if response.parsed is None:
        raise ValueError(f"Failed to parse job posting: {response.text}")
    logger.debug("job_posting: LLM call took %.2fs", elapsed)
    return response.parsed


def job_posting_node(state: CVAgentState) -> CVAgentState:
    """LangGraph node: parses the raw job description into state."""
    raw = state.get("job_description")
    if not raw:
        logger.warning("job_posting_node skipped — no job_description in state")
        return state

    logger.info("job_posting_node: parsing job description (%d chars)", len(raw))
    job_posting = parse_job_posting(raw)
    logger.info(
        "job_posting_node: parsed — title=%r  company=%r  keywords=%d",
        job_posting.title,
        job_posting.company or "n/a",
        len(job_posting.keywords),
    )
    return {
        **state,
        "job_posting": job_posting.model_dump(),
        "target_role": job_posting.title,
    }
