from langchain_text_splitters import RecursiveCharacterTextSplitter
import re
from collections import Counter
import pymupdf

# A page with fewer characters than this is treated as "no real text"
MIN_PAGE_CHARS = 20
# If the whole document has fewer characters than this, it's probably scanned
MIN_TOTAL_CHARS = 100

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150


class PDFError(Exception):
    """Raised with a user-friendly message when a PDF can't be processed."""


def clean_text(text):
    """Tidy text extracted from a PDF page."""
    text = text.replace("\u00a0", " ")           # non-breaking space -> normal space
    text = re.sub(r"-\n(\w)", r"\1", text)       # join words split by a hyphen at line end
    text = re.sub(r"[ \t]+", " ", text)          # collapse repeated spaces and tabs
    text = re.sub(r" *\n *", "\n", text)         # remove spaces around line breaks
    text = re.sub(r"\n{3,}", "\n\n", text)       # at most one blank line in a row
    return text.strip()

def remove_repeated_lines(pages, threshold=0.4):
    """Remove lines (headers/footers) that appear on many pages."""
    if len(pages) < 5:
        return pages  # too few pages to judge what repeats

    counts = Counter()
    for page in pages:
        for line in set(page["text"].split("\n")):
            counts[line.strip()] += 1

    repeated = {
        line for line, n in counts.items()
        if line and n / len(pages) >= threshold
    }

    for page in pages:
        lines = [l for l in page["text"].split("\n") if l.strip() not in repeated]
        if lines and lines[-1].strip().isdigit():  # a lone page number at the end
            lines.pop()
        page["text"] = "\n".join(lines).strip()
    return pages

def extract_pages(file_bytes, filename):
    """Read a PDF and return a list of pages.

    Each page is a dict: {"source": filename, "page": human page number, "text": cleaned text}
    Raises PDFError with a readable message if the file can't be used.
    """
    try:
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise PDFError(f"'{filename}' could not be opened. It may be corrupted.") from e

    if doc.needs_pass:
        raise PDFError(f"'{filename}' is password-protected and can't be read.")

    pages = []
    for index, page in enumerate(doc):
        text = clean_text(page.get_text())
        if text:
            pages.append({"source": filename, "page": index + 1, "text": text})

    pages = remove_repeated_lines(pages)
    pages = [p for p in pages if len(p["text"]) >= MIN_PAGE_CHARS]

    total_chars = sum(len(p["text"]) for p in pages)
    if total_chars < MIN_TOTAL_CHARS:
        raise PDFError(
            f"'{filename}' has almost no readable text. It may be a scanned PDF (images only)."
        )

    return pages

def chunk_pages(pages, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    """Split each page's text into overlapping chunks.

    Returns a list of dicts:
    {"source", "page", "chunk_id", "text"}
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []
    for page in pages:
        pieces = splitter.split_text(page["text"])
        for i, piece in enumerate(pieces):
            chunks.append(
                {
                    "source": page["source"],
                    "page": page["page"],
                    "chunk_id": f"{page['source']}-p{page['page']}-c{i}",
                    "text": piece,
                }
            )
    return chunks