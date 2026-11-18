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


def page_header(icon, title, subtitle):
    st.markdown(
        f'<div class="rm-header"><div class="rm-icon">{icon}</div>'
        f'<div><div class="rm-title">{esc(title)}</div><div class="rm-sub">{esc(subtitle)}</div></div></div>',
        unsafe_allow_html=True,
    )


def empty_state(icon, title, text):
    st.markdown(
        f'<div class="rm-empty"><div class="big">{icon}</div><b>{esc(title)}</b><span>{esc(text)}</span></div>',
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
    with st.expander("🔍 How I found this answer"):
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
        label = f"📄 {s['source']} - page {s['page']}"
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