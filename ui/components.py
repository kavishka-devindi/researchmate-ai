"""Small reusable pieces shared by all pages."""
from html import escape as esc
import re

import streamlit as st

TOOL_LABELS = {
    "list_documents": "Checked which documents are uploaded",
    "search_documents": "Searched the documents",
    "answer_from_documents": "Looked up an answer",
    "summarize_document": "Read a document to summarise it",
    "compare_documents": "Compared two documents",
}

ICON_PATHS = {
    "home": "M3 11.5 12 4l9 7.5v8a1.5 1.5 0 0 1-1.5 1.5H15v-6H9v6H4.5A1.5 1.5 0 0 1 3 19.5z",
    "chat": "M4 5.5h16A2.5 2.5 0 0 1 22.5 8v7A2.5 2.5 0 0 1 20 17.5H11l-4.5 3v-3H4A2.5 2.5 0 0 1 1.5 15V8A2.5 2.5 0 0 1 4 5.5z",
    "document": "M5 2.5h9l5 5v14H5a2 2 0 0 1-2-2v-15a2 2 0 0 1 2-2zm9 0v5h5M7 12h10M7 16h7",
    "scale": "M6 4v16M18 4v16M3 7h6M15 7h6M3 17h6M15 17h6M4 4h4l-2 3zM16 20h4l-2-3z",
    "chart": "M4 20V10M10 20V5M16 20v-8M22 20H2",
    "history": "M12 5a7 7 0 1 1-6.2 3.75M5 5v4h4M12 8v4l3 2",
    "settings": "M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7zm0-6 1 2.1a7.7 7.7 0 0 1 2 .8l2.2-.7 1.7 1.7-.7 2.2a7.7 7.7 0 0 1 .8 2L21 11v2l-2.1 1a7.7 7.7 0 0 1-.8 2l.7 2.2-1.7 1.7-2.2-.7a7.7 7.7 0 0 1-2 .8L12 22l-2-1-1-2.1a7.7 7.7 0 0 1-2-.8l-2.2.7-1.7-1.7.7-2.2a7.7 7.7 0 0 1-.8-2L1 13v-2l2.1-1a7.7 7.7 0 0 1 .8-2l-.7-2.2 1.7-1.7 2.2.7a7.7 7.7 0 0 1 2-.8L10 2.5z",
    "spark": "M12 2l1.5 6.5L20 10l-6.5 1.5L12 18l-1.5-6.5L4 10l6.5-1.5z",
}

def icon_markup(icon, size="1.7rem"):
    key = icon if icon in ICON_PATHS else "spark"
    path = ICON_PATHS[key]
    return (
        f'<svg class="rm-inline-icon" width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
        f'stroke-linejoin="round"><path d="{path}"/></svg>'
    )


def pdf_icon_markup(size="1.45rem"):
    """Adobe-style PDF marker recreated as a lightweight inline SVG."""
    width = size
    height = size
    return (
        f'<svg class="rm-pdf-svg" width="{width}" height="{height}" viewBox="0 0 32 36" '
        'xmlns="http://www.w3.org/2000/svg" aria-label="PDF document">'
        '<path d="M6 1h13l7 7v21a5 5 0 0 1-5 5H6a5 5 0 0 1-5-5V6a5 5 0 0 1 5-5z" fill="#EE3B36"/>'
        '<path d="M19 1v8h7" fill="#C92D2A"/>'
        '<path d="M19 2v6h6" fill="#F6A09D"/>'
        '<path d="M7 29l3.2-10h2.1l3.1 10h-2l-.6-2H9.7l-.6 2zm3.2-3.7h2.1l-1-3.4z" fill="#fff"/>'
        '<path d="M16.2 29v-10h3.4c2 0 3.2 1 3.2 2.7 0 1.8-1.2 2.8-3.2 2.8h-1.4V29zm2-6.2h1.2c.9 0 1.4-.4 1.4-1.1 0-.7-.5-1.1-1.4-1.1h-1.2z" fill="#fff"/>'
        '<path d="M24 29v-10h6v1.8h-4v2.2h3.5V25H26v4z" fill="#fff"/>'
        '</svg>'
    )


def page_header(icon, title, subtitle):
    st.markdown(
        f'<div class="rm-header"><div class="rm-icon">{icon_markup(icon)}</div>'
        f'<div><div class="rm-title">{esc(title)}</div><div class="rm-sub">{esc(subtitle)}</div></div></div>',
        unsafe_allow_html=True,
    )


def empty_state(icon, title, text):
    st.markdown(
        f'<div class="rm-empty"><div class="big">{icon_markup(icon, "2.1rem")}</div><b>{esc(title)}</b><span>{esc(text)}</span></div>',
        unsafe_allow_html=True,
    )


def status_chip(label, kind="ok"):
    return f'<span class="rm-chip {kind}">{esc(label)}</span>'


def format_answer(text):
    """Turn inline bullet symbols into a proper Markdown list."""
    text = re.sub(r"[ \t]*[•●▪◦][ \t]*", "\n- ", text)
    out = []
    for line in text.split("\n"):
        is_item = line.lstrip().startswith(("- ", "* "))
        prev_is_item = bool(out) and out[-1].lstrip().startswith(("- ", "* "))
        if is_item and out and out[-1].strip() and not prev_is_item:
            out.append("")
        out.append(line)
    return "\n".join(out)


def render_steps(calls):
    with st.expander("How I found this answer"):
        if not calls:
            st.write("No document lookup was needed for this message.")
        for i, c in enumerate(calls, start=1):
            label = TOOL_LABELS.get(c["tool"], c["tool"])
            detail = ", ".join(str(v) for v in c["args"].values())
            st.text(f"{i}. {label}" + (f": {detail}" if detail else "") + f"   [{c['tool']}]")


def render_sources(sources):
    if not sources:
        return
    st.markdown("**Sources**")
    for s in sources:
        label = f"Document: {s['source']} - page {s['page']}"
        if s.get("score") is not None:
            label += f" (match {s['score']})"
        if s.get("text") is None:
            st.warning(f"Could not verify this citation: {label}")
        else:
            with st.expander(label):
                st.text(s["text"])


def show_tool_text(text):
    """Show a tool result; tool failures come back as plain text starting with these phrases."""
    if text.startswith(("Summary failed", "Comparison failed", "No document named")):
        st.error(text)
    else:
        st.markdown(format_answer(text))