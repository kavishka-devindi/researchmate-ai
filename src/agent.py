from typing import Annotated, Sequence, TypedDict
from src.config import CHAT_MODEL, GEMINI_API_KEY
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from src.config import CHAT_MODEL, GEMINI_API_KEY, TEMPERATURE
from src.rag import NOT_FOUND
from src.tools import TOOLS

MAX_STEPS = 6  # safety cap on LLM calls per question

SYSTEM_PROMPT = f"""You are a research assistant for the user's uploaded documents.
You must use your tools. Never answer questions about document content from memory.

Tool guide:
- Greetings, or questions about what you can do: answer directly, no tools.
- Any other question: call a tool first, even if it seems unrelated to the documents.
- Facts or details: search_documents.
- Summary or overview of one document: list_documents (if you don't know the exact name), then summarize_document.
- Comparing two documents: list_documents (if needed), then compare_documents.

Base your answer ONLY on tool results. If the tools find nothing relevant, reply exactly: "{NOT_FOUND}"
After each fact you use, cite it like [Source: file name, page N]."""


class AgentError(Exception):
    """Raised with a user-friendly message when the agent fails."""


# ---- State: the data passed between nodes ----
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    steps: int


# ---- The model, with our tools attached ----
llm = ChatGoogleGenerativeAI(
    model=CHAT_MODEL,
    google_api_key=GEMINI_API_KEY,
    max_retries=2,
)
model = llm.bind_tools(TOOLS)
tools_by_name = {t.name: t for t in TOOLS}


# ---- Nodes ----
def call_model(state: AgentState):
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(state["messages"])
    response = model.invoke(messages)
    return {"messages": [response], "steps": state["steps"] + 1}


def call_tools(state: AgentState):
    outputs = []
    for call in state["messages"][-1].tool_calls:
        try:
            result = tools_by_name[call["name"]].invoke(call["args"])
        except Exception as e:
            result = f"Tool error: {e}"
        outputs.append(ToolMessage(content=result, name=call["name"], tool_call_id=call["id"]))
    return {"messages": outputs}


# ---- Conditional edge: the agent's decision point ----
def should_continue(state: AgentState):
    last = state["messages"][-1]
    if last.tool_calls and state["steps"] < MAX_STEPS:
        return "tools"
    return "end"


# ---- Build the graph ----
workflow = StateGraph(AgentState)
workflow.add_node("llm", call_model)
workflow.add_node("tools", call_tools)
workflow.set_entry_point("llm")
workflow.add_conditional_edges("llm", should_continue, {"tools": "tools", "end": END})
workflow.add_edge("tools", "llm")
graph = workflow.compile()


def message_text(message):
    """Get plain text from a model message (content may be a string or a list of blocks)."""
    content = message.content
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "".join(parts)


def run_agent(question):
    """Run the agent. Returns {"answer": text, "tool_calls": [{"tool", "args"}, ...]}"""
    try:
        result = graph.invoke({"messages": [HumanMessage(content=question)], "steps": 0})
    except Exception as e:
        raise AgentError(
            "The agent could not finish. The AI service may be busy or rate-limited. "
            "Please try again in a minute."
        ) from e

    messages = result["messages"]
    tool_calls = [
        {"tool": c["name"], "args": c["args"]}
        for m in messages
        for c in (getattr(m, "tool_calls", None) or [])
    ]
    answer = message_text(messages[-1]).strip()
    if not answer:
        answer = "The agent stopped before producing an answer. Try a more specific question."
    return {"answer": answer, "tool_calls": tool_calls}