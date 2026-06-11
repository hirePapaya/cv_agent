from langgraph.graph import StateGraph

from .states import CVAgentState, ChatState
from .nodes import chat_node, close_chat_node, job_posting_node





job_posting_graph = StateGraph(state_schema=CVAgentState)
job_posting_graph.set_entry_point("job_posting")
job_posting_graph.add_node("job_posting", job_posting_node)
job_posting_graph.set_finish_point("job_posting")
agent = job_posting_graph.compile()



chat_graph = StateGraph(state_schema=ChatState)
chat_graph.set_entry_point("chat")
chat_graph.add_node("chat", chat_node)
chat_graph.add_node("close_chat", close_chat_node)
chat_graph.add_edge("chat", "close_chat")
chat_graph.set_finish_point("close_chat")
chat_agent = chat_graph.compile()
