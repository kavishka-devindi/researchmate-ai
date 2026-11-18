import json
import os
import re

from src.config import BASE_DIR
from src.llm import generate_answer, LLMError
from src.vector_store import get_document_chunks

ANALYSIS_PATH = os.path.join(BASE_DIR, "data", "analysis.json")
NOT_STATED = "Not stated"
MAX_CHARS = 24000          # how much document text we send (about 6,000 tokens)

TEXT_FIELDS = ["title", "authors", "year", "objective", "dataset", "methodology",
               "models", "metrics", "key_results", "limitations", "future_work"]
LIST_FIELDS = ["topics", "keywords", "methods", "gaps"]

SYSTEM_PROMPT = f"""You extract structured facts from a document (usually a research paper).
Use ONLY the text provided. If something is not stated, write "{NOT_STATED}". Never guess.
Reply with ONE JSON object and nothing else (no markdown fences), with exactly these keys:
"title", "authors" (short, e.g. "Vaswani et al."), "year" (publication year),
"objective", "dataset", "methodology", "models" (models or algorithms used),
"metrics" (evaluation metrics), "key_results", "limitations", "future_work",
"topics" (list of 2-4 broad research areas, e.g. "Natural Language Processing"),
"keywords" (list of up to 6 keywords), "methods" (list of up to 4 methods or techniques),
"gaps" (list of up to 3 research gaps or open problems the document mentions).
Keep every text value under 25 words."""


class AnalysisError(Exception):
    """Raised with a user-friendly message when a document can't be analysed."""


def _load():
    try:
        with open(ANALYSIS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _save(data):
    os.makedirs(os.path.dirname(ANALYSIS_PATH), exist_ok=True)
    with open(ANALYSIS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)


def all_analyses():
    """All saved analyses: {file name: analysis}."""
    return _load()


def get_analysis(filename):
    return _load().get(filename)


def remove_analysis(filename):
    data = _load()
    if data.pop(filename, None) is not None:
        _save(data)


def _document_text(filename):
    chunks = get_document_chunks(filename)
    if not chunks:
        raise AnalysisError(f"'{filename}' has no stored text.")
    blocks = [f"[page {c['page']}] {c['text']}" for c in chunks]
    if sum(len(b) for b in blocks) <= MAX_CHARS:
        return "\n\n".join(blocks)
    head, rest = blocks[:8], blocks[8:]                 # title, authors and abstract come first
    room = MAX_CHARS - sum(len(b) for b in head)
    stride = max(1, -(-sum(len(b) for b in rest) // max(room, 1)))
    return "\n\n".join(head + rest[::stride])


def _parse_json(text):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object")
    return json.loads(text[start:end + 1])


def _clean(raw, filename):
    result = {}
    for key in TEXT_FIELDS:
        value = str(raw.get(key) or NOT_STATED).strip()
        result[key] = value[:300] or NOT_STATED
    if result["title"] == NOT_STATED:
        result["title"] = os.path.splitext(filename)[0]
    for key in LIST_FIELDS:
        value = raw.get(key) or []
        if isinstance(value, str):
            value = [value]
        result[key] = [str(v).strip()[:80] for v in value if str(v).strip()][:8]
    return result


def analyze_document(filename, force=False):
    """Extract title, authors, methods, results and so on. Costs one LLM request.

    The result is saved in data/analysis.json, so each document is analysed only once.
    """
    data = _load()
    if filename in data and not force:
        return data[filename]

    text = _document_text(filename)
    try:
        answer = generate_answer(f"Document text:\n\n{text}", system_instruction=SYSTEM_PROMPT)
    except LLMError as e:
        raise AnalysisError(str(e)) from e
    try:
        analysis = _clean(_parse_json(answer), filename)
    except (ValueError, TypeError) as e:
        raise AnalysisError("The AI reply could not be read. Please try again.") from e

    data[filename] = analysis
    _save(data)
    return analysis