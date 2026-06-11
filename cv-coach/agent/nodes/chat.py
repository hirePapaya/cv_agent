import json
from ..states import ChatState

def chat_node(state: ChatState) -> ChatState:
    """LangGraph node: asks Gemini for CV edit operations from a chat instruction."""
    return {
        **state,
        "reply": "Hey I'm the chat node",
        "log": ["This is the log of changes made so far."],
        "ops": ["Empty", "For", "Now"],
    }



def close_chat_node(state: ChatState) -> ChatState:
    """LangGraph node: asks Gemini for CV edit operations from a chat instruction."""
    return {
        **state,
        "reply": "This is the final reply from the close chat node. The chat is now closed.",
        "log": ["That was great chatting with you!"],
        "ops": ["Empty", "For", "Now"],
    }