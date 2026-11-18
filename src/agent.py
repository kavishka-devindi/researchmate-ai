import re
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from src.config import AGENT_MODEL, GEMINI_API_KEY
from src.rag import NOT_FOUND, CITATION_PATTERN, _norm
from src.tools import TOOLS
from src.vector_store import stored_documents, get_document_chunks

MAX_STEPS = 6  # safety cap on LLM calls per question

SYSTEM_PROMPT = f"""You are a research assistant for the user's uploaded documents.
You must use your tools. Never answer questions about document content from memory.

Tool guide:
- Greetings, or questions about what you can do: answer directly, no tools.
- Any other question: call a tool first, even if it seems unrelated to the documents.
- A direct factual question with one clear answer: answer_from_documents.
- Exploring a topic, or gathering passages from several angles: search_documents.
- Summary or overview of one document: list_documents (if you don't know the exact name), then summarize_document.
- Comparing two documents: list_documents (if needed), then compare_documents.

Base your answer ONLY on tool results. If the tools find nothing relevant, reply exactly: "{NOT_FOUND}"
After each fact you use, cite it like [Source: file name, page N].
Write normal English with a space between every word, and copy file names exactly as written, including spaces."""


class AgentError(Exception):
    """Raised with a user-friendly message when the agent fails."""


# ---- State: the data passed between nodes ----
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    steps: int
    selected_source: str


# ---- The model, with our tools attached ----
llm = ChatGoogleGenerativeAI(
    model=AGENT_MODEL,
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
            args = dict(call["args"])
            if call["name"] == "search_documents" and state.get("selected_source"):
                args["source"] = state["selected_source"]
            result = tools_by_name[call["name"]].invoke(args)
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

def resolve_citations(answer):
    """Turn [Source: file, page N] citations into checkable source records.

    Each record: {"source", "page", "text"}; text is None if the file or page doesn't exist.
    """
    names = {_norm(d["File"]): d["File"] for d in stored_documents()}
    seen, records = set(), []
    for m in CITATION_PATTERN.finditer(answer):
        file_key = _norm(m.group(1))
        for number in re.findall(r"\d+", m.group(2)):
            page = int(number)
            if (file_key, page) in seen:
                continue
            seen.add((file_key, page))
            real_name = names.get(file_key)
            text = None
            if real_name:
                pieces = [c["text"] for c in get_document_chunks(real_name) if c["page"] == page]
                text = "\n\n".join(pieces) or None
            records.append({"source": real_name or m.group(1).strip(), "page": page, "text": text})
    return records


def run_agent(question, source=None):
    """Run the agent.

    Returns {"answer": text, "tool_calls": [{"tool", "args"}, ...], "sources": [...]}
    """
    try:
        selected_source = source or ""
        prompt = question
        if selected_source:
            prompt = (
                f"The user selected this PDF: {selected_source}\n"
                "Use only this selected PDF for document searches and summaries.\n\n"
                f"{question}"
            )
        result = graph.invoke({
            "messages": [HumanMessage(content=prompt)],
            "steps": 0,
            "selected_source": selected_source,
        })
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
    return {"answer": answer, "tool_calls": tool_calls, "sources": resolve_citations(answer)}