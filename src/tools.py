from langchain_core.tools import tool

from src.llm import generate_answer, LLMError
from src.rag import MIN_SCORE, build_context, answer_question
from src.vector_store import (
    search_chunks, stored_documents, get_document_chunks, VectorStoreError,
)

MAX_SUMMARY_CHARS = 60000   # about 15,000 tokens


def _document_names():
    return [d["File"] for d in stored_documents()]


def _unknown_name_message(name):
    return f"No document named '{name}'. Available documents: {', '.join(_document_names()) or 'none'}."


@tool
def list_documents() -> str:
    """List the names of all uploaded documents. Use this first when you need
    the exact file name for summarize_document or compare_documents."""
    docs = stored_documents()
    if not docs:
        return "No documents have been uploaded."
    return "\n".join(f"{d['File']} ({d['Chunks']} chunks)" for d in docs)


@tool
def search_documents(query: str, source: str = "") -> str:
    """Find passages in the uploaded documents that are relevant to a specific
    question or topic. Use this for factual questions about document content.
    Returns passages labelled with the file name and page number."""
    try:
        hits = [
            h for h in search_chunks(query, k=6, source=source or None)
            if h["score"] >= MIN_SCORE
        ]
    except VectorStoreError as e:
        return f"Search failed: {e}"
    if not hits:
        return "No relevant passages found in the uploaded documents."
    return build_context(hits)


@tool
def summarize_document(filename: str) -> str:
    """Summarise ONE whole document. Use when the user asks for a summary or
    overview of a document. filename must exactly match a name from list_documents."""
    if filename not in _document_names():
        return _unknown_name_message(filename)

    chunks = get_document_chunks(filename)
    blocks = [f"[page {c['page']}] {c['text']}" for c in chunks]
    total = sum(len(b) for b in blocks)
    note = ""
    if total > MAX_SUMMARY_CHARS:
        stride = -(-total // MAX_SUMMARY_CHARS)   # round up
        blocks = blocks[::stride]
        note = f"\n(Note: the document is long, so this summary used about 1 in {stride} text sections.)"

    system = (
        "You summarise documents. Use ONLY the text provided. "
        "Write 5 to 8 clear bullet points covering the main ideas. "
        f"Cite pages like [Source: {filename}, page N]. Do not add outside information."
    )
    try:
        summary = generate_answer("\n\n".join(blocks), system_instruction=system)
    except LLMError as e:
        return f"Summary failed: {e}"
    return summary + note


@tool
def compare_documents(filename_a: str, filename_b: str, topic: str) -> str:
    """Compare two different documents on a given topic. Use when the user asks
    about similarities or differences between two documents. Both file names must
    exactly match names from list_documents."""
    names = _document_names()
    for name in (filename_a, filename_b):
        if name not in names:
            return _unknown_name_message(name)

    contexts = {}
    try:
        for name in (filename_a, filename_b):
            hits = [h for h in search_chunks(topic, k=4, source=name) if h["score"] >= MIN_SCORE]
            contexts[name] = build_context(hits) if hits else "(no relevant passages found)"
    except VectorStoreError as e:
        return f"Comparison failed: {e}"

    prompt = (
        f"Topic: {topic}\n\n"
        f"=== Document A: {filename_a} ===\n{contexts[filename_a]}\n\n"
        f"=== Document B: {filename_b} ===\n{contexts[filename_b]}"
    )
    system = (
        "You compare two documents using ONLY the passages provided. "
        "Give: 1) what they have in common, 2) key differences, 3) a one-line conclusion. "
        "If one document has no relevant passages, say so instead of guessing. "
        "Cite like [Source: file name, page N]."
    )
    try:
        return generate_answer(prompt, system_instruction=system)
    except LLMError as e:
        return f"Comparison failed: {e}"

@tool
def answer_from_documents(question: str) -> str:
    """Get a complete, cited answer to ONE self-contained factual question using
    the uploaded documents (for example 'What is an ODS?'). Do not use this for
    summaries, comparisons, or questions that need several different searches."""
    try:
        result = answer_question(question)
    except (LLMError, VectorStoreError) as e:
        return f"Answering failed: {e}"
    return result["answer"]

TOOLS = [list_documents, search_documents, answer_from_documents, summarize_document, compare_documents]