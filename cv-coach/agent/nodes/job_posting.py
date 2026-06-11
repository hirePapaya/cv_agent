from google import genai
from google.genai import types

from ..models import JobPosting
from ..states import CVAgentState

SYSTEM_PROMPT = """You are a job posting parser. Extract structured information \
from the raw job posting text provided by the user.

Rules:
- title: the job title as posted
- company: the hiring company name; if not stated, use an empty string
- location: city/country or "Remote"; null if not mentioned
- description: a concise 2-4 sentence summary of the role
- requirements: each distinct requirement/qualification as its own list item, \
preserving specifics (years of experience, technologies, certifications)
- keywords: technologies, tools, methodologies and domain terms useful for \
CV/ATS matching (e.g. "Kubernetes", "Terraform", "CI/CD")

Extract only what is present in the text. Do not invent information."""


def parse_job_posting(raw_text: str) -> JobPosting:
    """Parse a raw job posting string into a structured JobPosting."""
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=raw_text,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=JobPosting,
        ),
    )
    parsed = response.parsed
    if parsed is None:
        # model failed to produce valid JSON matching the schema
        raise ValueError(f"Failed to parse job posting: {response.text}")
    return parsed



def job_posting_node(state: CVAgentState) -> CVAgentState:
    """LangGraph node: parses the raw job description into state."""
    raw = state.get("job_description")
    if not raw:
        return state   
    job_posting = parse_job_posting(raw)
    return {
        **state,
        "job_posting": job_posting.model_dump(),  # dict for safe checkpointing
        "target_role": job_posting.title,
    }