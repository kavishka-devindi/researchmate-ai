import re
from src.llm import generate_answer
from src.vector_store import search_chunks

TOP_K = 4          # how many chunks to retrieve
MIN_SCORE = 0.6    # chunks below this similarity are treated as irrelevant

NOT_FOUND = "I could not find this in the uploaded documents."

SYSTEM_PROMPT = f"""You are a careful document assistant.
Answer the question using ONLY the context provided.
If the context does not contain the answer, reply exactly: "{NOT_FOUND}"
Do not use outside knowledge and do not guess.
After each fact you use, cite its source like [Source: file name, page N].
Keep the answer clear and concise."""


def build_context(hits):
    """Format retrieved chunks as numbered, labelled blocks of text."""
    blocks = []
    for i, h in enumerate(hits, start=1):
        blocks.append(f"[{i}] (Source: {h['source']}, page {h['page']})\n{h['text']}")
    return "\n\n".join(blocks)

CITATION_PATTERN = re.compile(r"\[Source:\s*(.+?),\s*pages?\s*(\d+)", re.IGNORECASE)


def cited_sources(answer, sources):
    """Keep only the chunks whose (file, page) the answer actually cites."""
    cited = {(m.group(1).strip(), int(m.group(2))) for m in CITATION_PATTERN.finditer(answer)}
    used = [s for s in sources if (s["source"], s["page"]) in cited]
    return used or sources  # if no citation could be read, show everything retrieved

def answer_question(question):
    """Answer a question from the stored documents.

    Returns {"answer": text, "sources": list of the chunks that were used}
    """
    hits = search_chunks(question, k=TOP_K)
    relevant = [h for h in hits if h["score"] >= MIN_SCORE]

    if not relevant:
        return {"answer": NOT_FOUND, "sources": []}

    prompt = f"Context:\n{build_context(relevant)}\n\nQuestion: {question}\n\nAnswer:"
    answer = generate_answer(prompt, system_instruction=SYSTEM_PROMPT)
    return {"answer": answer, "sources": cited_sources(answer, relevant)}