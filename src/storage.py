import os

import pymupdf

from src.config import BASE_DIR

UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")
LEGACY_DIR = os.path.join(BASE_DIR, "data")   # PDFs you copied here by hand earlier


def _safe(name):
    return os.path.basename(name)


def save_pdf(name, data):
    """Keep a copy of an uploaded PDF so we can preview and download it later."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    with open(os.path.join(UPLOAD_DIR, _safe(name)), "wb") as f:
        f.write(data)


def pdf_path(name):
    for folder in (UPLOAD_DIR, LEGACY_DIR):
        path = os.path.join(folder, _safe(name))
        if os.path.isfile(path):
            return path
    return None


def read_pdf(name):
    path = pdf_path(name)
    if not path:
        return None
    with open(path, "rb") as f:
        return f.read()


def uploaded_at(name):
    """When the PDF file was saved (seconds since 1970), or None if we don't have the file."""
    path = pdf_path(name)
    return os.path.getmtime(path) if path else None


def delete_pdf(name):
    """Delete our uploaded copy. PDFs you placed in data/ yourself are never touched."""
    path = os.path.join(UPLOAD_DIR, _safe(name))
    if os.path.isfile(path):
        os.remove(path)


def render_pages(name, first=0, count=1, width=300):
    """Render pages of a PDF as PNG images. Returns a list of PNG bytes (empty if no file)."""
    path = pdf_path(name)
    if not path:
        return []
    images = []
    try:
        with pymupdf.open(path) as doc:
            for i in range(first, min(first + count, doc.page_count)):
                page = doc[i]
                zoom = width / page.rect.width
                pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
                images.append(pix.tobytes("png"))
    except Exception:
        return []
    return images