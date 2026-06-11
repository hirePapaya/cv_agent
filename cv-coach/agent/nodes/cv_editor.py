import json

from google import genai
from google.genai import types

from ..states import CVEditState

CV_PATHS = """Paths address the current CV (all indices zero-based):
- "name", "title", "summary"  (strings)
- "contact[i].label", "contact[i].href"
- "experience[i].company", "experience[i].role", "experience[i].location", "experience[i].dates"
- "experience[i].bullets"  (the WHOLE array of bullet strings for that job)
- "education[i].school", "education[i].degree", "education[i].location", "education[i].dates"
- "skills[i].label", "skills[i].items"
Array paths for add/reorder/remove: "experience", "education", "skills", "contact"."""


def build_prompt(cv: dict, history: list[dict], instruction: str) -> str:
    """Build the editing prompt, mirroring CV Studio's buildPrompt (cv-studio.jsx)."""
    convo = "\n".join(
        ("User: " if turn.get("role") == "user" else "Editor: ") + str(turn.get("text", ""))
        for turn in history[-6:]
    )
    convo_section = f"Recent conversation:\n{convo}\n" if convo else ""

    return f"""You are the editing agent inside "CV Studio", a tool for refining one résumé. You make precise, tasteful edits and explain them briefly. Voice: calm, direct, operator-to-operator. Never invent facts (employers, dates, metrics) the user did not give — if a request needs missing info, ask for it and make no edits.

Respond with ONLY a JSON object — no prose, no markdown fences — with exactly these keys:
{{
  "reply": string,        // one short conversational sentence to the user
  "log": [string],        // past-tense, concrete change notes (e.g. "Tightened the summary to two sentences"). [] if nothing changed.
  "ops": [Operation]      // the edits to apply, smallest possible. [] if nothing changed.
}}

An Operation is ONE of:
{{ "op": "set", "path": <path>, "value": <string or array> }}
{{ "op": "add", "path": <arrayPath>, "value": <object>, "index": <number, optional> }}
{{ "op": "remove", "path": <path> }}
{{ "op": "reorder", "path": <arrayPath>, "order": [<indices in new order>] }}

{CV_PATHS}

Edit only what is asked; leave everything else intact. Do NOT re-send the whole CV — only the operations that change. Keep bullets concise and results-oriented.

Current CV (JSON):
{json.dumps(cv)}

{convo_section}New user request: {instruction}

Return the JSON object now."""


def cv_editor_node(state: CVEditState) -> CVEditState:
    """LangGraph node: asks Gemini for CV edit operations from a chat instruction."""
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=build_prompt(state["cv"], state.get("history", []), state["instruction"]),
        config=types.GenerateContentConfig(
            temperature=0.3,
            response_mime_type="application/json",
        ),
    )
    try:
        result = json.loads(response.text)
    except (TypeError, json.JSONDecodeError):
        result = {}

    return {
        **state,
        "reply": str(result.get("reply") or ""),
        "log": [str(x) for x in result.get("log") or []],
        "ops": [op for op in result.get("ops") or [] if isinstance(op, dict)],
    }
