from ..states import CVAgentState


def welcome_node(state: CVAgentState) -> CVAgentState:
    """LangGraph node: just a friendly greeting at the start of the conversation."""
    return {
         **state,
        "reply": "Hi! I'm your CV Coach. Let's work together to make your résumé shine. To get started, please paste the job posting you're targeting, and your current CV.",
        "log": ["Workflow started."],
        "ops": [],
    }