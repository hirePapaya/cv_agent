import json
from ..states import CVEditState


def cv_editor_node(state: CVEditState) -> CVEditState:
    """LangGraph node: asks Gemini for CV edit operations from a chat instruction."""
    return {
        **state,
        "reply": str(result.get("reply") or ""),
        "log": [str(x) for x in result.get("log") or []],
        "ops": [op for op in result.get("ops") or [] if isinstance(op, dict)],
    }
