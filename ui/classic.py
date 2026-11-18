"""Dashboard, chat, summary and compare pages carried over from the earlier version.
They keep working while each one is redesigned in a later step."""
import base64
from datetime import datetime

import streamlit as st

from src.agent import run_agent, resolve_citations, AgentError
from src.history import add_entry, load_history, time_ago
from src.llm import LLMError
from src.rag import answer_question
from src.tools import summarize_document, compare_documents
from src.vector_store import stored_documents, VectorStoreError
from ui.components import (
    esc, icon_markup, pdf_icon_markup, page_header, empty_state, format_answer, render_steps, render_sources, show_tool_text,
)
from ui.nav import goto, APP_NAME

HERO_SVG = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 220 150'>
<ellipse cx='105' cy='138' rx='85' ry='8' fill='#000' opacity='0.08'/>
<rect x='40' y='100' width='130' height='28' rx='6' fill='#EA580C'/>
<rect x='50' y='104' width='110' height='4' rx='2' fill='#FDBA74'/>
<rect x='50' y='72' width='115' height='28' rx='6' fill='#F97316'/>
<rect x='60' y='76' width='95' height='4' rx='2' fill='#FED7AA'/>
<rect x='58' y='44' width='100' height='28' rx='6' fill='#FB923C'/>
<rect x='68' y='48' width='80' height='4' rx='2' fill='#FFEDD5'/>
<circle cx='160' cy='30' r='30' fill='#FDE047' opacity='0.25'/>
<circle cx='160' cy='30' r='21' fill='#FDE047'/>
<rect x='151' y='49' width='18' height='8' rx='3' fill='#A8A29E'/>
<path d='M152 28 q8 -10 16 0' stroke='#F59E0B' stroke-width='3' fill='none' stroke-linecap='round'/>
</svg>"""
HERO_IMG = base64.b64encode(HERO_SVG.encode()).decode()

ACTIVITY_ICONS = {"question": "chat", "summary": "document", "comparison": "scale", "upload": "document"}
ACTIVITY_VERBS = {"question": "Asked", "summary": "Summarised", "comparison": "Compared", "upload": "Uploaded"}


def _greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    return "Good afternoon" if hour < 18 else "Good evening"


def _settings():
    return st.session_state.setdefault("settings", {"smart": True, "show_steps": True})


# ---------- Dashboard ----------
def page_dashboard():
    docs = stored_documents()
    st.markdown(
        f'<div class="hero"><div><div class="hero-title">{_greeting()}, Researcher</div>'
        f"<p>Welcome to {esc(APP_NAME)}, your AI research assistant. Ask questions, summarise "
        "or compare your documents, and see exactly where every answer comes from.</p></div>"
        f'<img src="data:image/svg+xml;base64,{HERO_IMG}" alt=""></div>',
        unsafe_allow_html=True,
    )

    with st.form("hero_form", border=False):
        c1, c2 = st.columns([5, 1])
        q = c1.text_input("Ask", placeholder="Ask anything about your documents...", label_visibility="collapsed")
        asked = c2.form_submit_button("Ask", type="primary", use_container_width=True)
    if asked:
        if not docs:
            st.warning("Upload a document first.")
        elif not q.strip():
            st.warning("Type a question first.")
        else:
            st.session_state.pending_question = q.strip()
            goto("workspace")

    chip1, chip2, chip3, _ = st.columns([2, 2, 2.4, 3])
    if chip1.button("Summarise a document", key="chip_summary"):
        goto("summary")
    if chip2.button("Compare documents", key="chip_compare"):
        goto("compare")
    if chip3.button("What documents do I have?", key="chip_docs"):
        st.session_state.pending_question = "What documents do I have?"
        goto("workspace")
    st.write("")

    history = load_history()
    questions = sum(1 for h in history if h["kind"] == "question")
    stats = [
        ("document", len(docs), "Documents"),
        ("document", sum(d["Pages"] for d in docs), "Pages with text"),
        ("chart", sum(d["Chunks"] for d in docs), "Searchable sections"),
        ("chat", questions, "Questions asked"),
    ]
    for col, (icon, num, label) in zip(st.columns(4), stats):
        col.markdown(
            f'<div class="stat-card"><div class="icon">{icon_markup(icon, "1.35rem")}</div>'
            f'<div><div class="num">{num}</div><div class="lbl">{label}</div></div></div>',
            unsafe_allow_html=True,
        )
    st.write("")

    left, right = st.columns([3, 2])
    with left:
        with st.container(border=True, key="box_dash_docs"):
            st.markdown("#### Recent documents")
            if docs:
                rows = "".join(
                    f'<div class="doc-row"><div class="doc-row-main">{pdf_icon_markup("1.55rem")}'
                    f'<div><b>{esc(d["File"])}</b>'
                    f'<div class="muted">{d["Pages"]} pages with text</div></div></div>'
                    '<span class="pill">Ready</span></div>'
                    for d in docs[:5]
                )
                st.markdown(rows, unsafe_allow_html=True)
            else:
                st.caption("No documents yet.")
                if st.button("Upload your first document", type="primary", key="dash_upload_first"):
                    goto("documents")

        with st.container(border=True, key="box_dash_activity"):
            st.markdown("#### Recent activity")
            recent = history[-5:][::-1]
            if recent:
                rows = "".join(
                    f'<div class="activity"><span class="activity-icon">'
                    f'{icon_markup(ACTIVITY_ICONS.get(h["kind"], "spark"), "1rem")}</span>'
                    f'{ACTIVITY_VERBS.get(h["kind"], "")}: {esc(h["text"])} '
                    f'<span class="muted">· {time_ago(h["time"])}</span></div>'
                    for h in recent
                )
                st.markdown(rows, unsafe_allow_html=True)
            else:
                st.caption("Your questions and uploads will appear here.")

    with right:
        with st.container(border=True, key="box_dash_actions"):
            st.markdown("#### Quick actions")
            if st.button("Upload documents", use_container_width=True, key="qa_upload"):
                goto("documents")
            if st.button("Ask a question", use_container_width=True, key="qa_chat"):
                goto("workspace")
            if st.button("Summarise a document", use_container_width=True, key="qa_summary"):
                goto("summary")
            if st.button("Compare documents", use_container_width=True, key="qa_compare"):
                goto("compare")
        st.markdown(
            '<div class="rm-insight-banner"><div><b>Turn your research into insights</b>'
            '<span>Let ResearchMate AI analyze your library and uncover meaningful findings.</span>'
            '<span class="rm-insight-cta">Start exploring</span></div>'
            '<svg class="rm-insight-art" viewBox="0 0 180 112" xmlns="http://www.w3.org/2000/svg" '
            'aria-label="Research insights illustration">'
            '<ellipse cx="102" cy="96" rx="63" ry="7" fill="#7C2D12" opacity=".10"/>'
            '<rect x="43" y="20" width="78" height="62" rx="7" fill="#FFF7ED" stroke="#334155" stroke-width="4"/>'
            '<rect x="53" y="31" width="58" height="7" rx="3.5" fill="#FDBA74"/>'
            '<rect x="53" y="44" width="58" height="6" rx="3" fill="#FED7AA"/>'
            '<path d="M58 68l14-10 12 5 16-18 8 7" fill="none" stroke="#F97316" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
            '<circle cx="72" cy="58" r="4" fill="#EA580C"/><circle cx="84" cy="63" r="4" fill="#EA580C"/><circle cx="100" cy="45" r="4" fill="#EA580C"/>'
            '<circle cx="132" cy="49" r="20" fill="#FFF7ED" stroke="#334155" stroke-width="4"/>'
            '<path d="M145 62l20 20" stroke="#334155" stroke-width="7" stroke-linecap="round"/>'
            '<rect x="17" y="79" width="52" height="16" rx="4" fill="#EA580C"/>'
            '<rect x="25" y="70" width="54" height="12" rx="4" fill="#FB923C"/>'
            '</svg></div>',
            unsafe_allow_html=True,
        )


# ---------- Research Workspace (chat) ----------
def page_chat():
    docs = stored_documents()
    names = [d["File"] for d in docs]
    settings = _settings()
    st.session_state.setdefault("messages", [])

    page_header("chat", "Research Workspace", "Ask questions about your documents and get answers with sources.")

    with st.expander("Answer settings"):
        style = st.radio(
            "Answer style",
            ["Smart assistant (recommended)", "Quick answer"],
            index=0 if settings["smart"] else 1,
            horizontal=True,
            help="Smart assistant works out what you need: it can search, summarise or compare "
            "documents. Quick answer simply searches once and replies.",
        )
        settings["smart"] = style.startswith("Smart")
        settings["show_steps"] = st.checkbox("Show how answers were found", value=settings["show_steps"])
        scope_options = ["All uploaded documents"] + names
        previous_scope = st.session_state.get("document_scope", "All uploaded documents")
        if previous_scope not in scope_options:
            previous_scope = "All uploaded documents"
        selected_scope = st.selectbox(
            "Search in",
            scope_options,
            index=scope_options.index(previous_scope),
        )
        st.session_state.document_scope = selected_scope

    if not docs:
        empty_state("document", "No documents yet", "Upload one or more PDFs in My Documents to begin.")
        if st.button("Go to My Documents", key="chat_to_docs"):
            goto("documents")
    elif not st.session_state.messages:
        st.markdown("#### What would you like to know?")
        st.caption("Try one of these, or type your own question below.")
        examples = ["What documents do I have?", f"Summarise {names[0]}", "What are the main topics covered?"]
        for col, example in zip(st.columns(len(examples)), examples):
            if col.button(example, use_container_width=True, key=f"ex_{example}"):
                st.session_state.pending_question = example

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(format_answer(msg["content"]))
            if msg["role"] == "assistant":
                if msg.get("agent") and settings["show_steps"]:
                    render_steps(msg["tool_calls"])
                render_sources(msg["sources"])

    typed = st.chat_input("Ask about your documents...", disabled=not docs)
    question = typed or st.session_state.pop("pending_question", None)

    if question and docs:
        add_entry("question", question[:80])
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        try:
            with st.spinner("Thinking..."):
                selected_scope = st.session_state.get("document_scope", "All uploaded documents")
                source = None if selected_scope == "All uploaded documents" else selected_scope
                if settings["smart"]:
                    res = run_agent(question, source=source)
                else:
                    res = answer_question(question, source=source)
                    res["tool_calls"] = []
            st.session_state.messages.append(
                {"role": "assistant", "content": res["answer"], "tool_calls": res["tool_calls"],
                 "sources": res["sources"], "agent": settings["smart"]}
            )
        except (LLMError, VectorStoreError, AgentError) as e:
            st.session_state.messages.append(
                {"role": "assistant", "content": f"Error: {e}", "tool_calls": [], "sources": [], "agent": False}
            )
        st.rerun()

    if st.session_state.messages:
        if st.button("Clear chat", key="clear_chat"):
            st.session_state.messages = []
            st.rerun()


# ---------- Summary ----------
def page_summary():
    names = [d["File"] for d in stored_documents()]
    page_header("document", "Summary", "Get a short, cited summary of any document.")
    if not names:
        empty_state("document", "No documents yet", "Upload and process at least one PDF first.")
        return
    with st.container(border=True, key="box_summary"):
        chosen = st.selectbox("Choose a document", names, key="sum_doc")
        if st.button("Summarise", key="sum_btn", type="primary"):
            with st.spinner("Reading and summarising..."):
                text = summarize_document.invoke({"filename": chosen})
            if not text.startswith(("Summary failed", "No document named")):
                add_entry("summary", chosen)
            st.session_state.summary = {"doc": chosen, "text": text, "sources": resolve_citations(text)}
    summary = st.session_state.get("summary")
    if summary:
        st.markdown(f"### Summary of {summary['doc']}")
        show_tool_text(summary["text"])
        render_sources(summary["sources"])


# ---------- Compare ----------
def page_compare():
    names = [d["File"] for d in stored_documents()]
    page_header("scale", "Compare Papers", "Analyze and compare documents side by side.")
    if len(names) < 2:
        empty_state("scale", "Two documents needed", "Upload and process at least two PDFs to compare them.")
        return
    with st.container(border=True, key="box_compare"):
        col_a, col_b = st.columns(2)
        doc_a = col_a.selectbox("First document", names, key="cmp_a")
        doc_b = col_b.selectbox("Second document", names, index=1, key="cmp_b")
        topic = st.text_input("What should I compare?", key="cmp_topic", placeholder="e.g. model architecture")
        if st.button("Compare", key="cmp_btn", type="primary"):
            if doc_a == doc_b:
                st.warning("Please choose two different documents.")
            elif not topic.strip():
                st.warning("Please enter a topic to compare.")
            else:
                with st.spinner("Comparing..."):
                    text = compare_documents.invoke(
                        {"filename_a": doc_a, "filename_b": doc_b, "topic": topic}
                    )
                if not text.startswith(("Comparison failed", "No document named")):
                    add_entry("comparison", f"{doc_a} and {doc_b}")
                st.session_state.comparison = {
                    "title": f"{doc_a} vs {doc_b}: {topic}",
                    "text": text,
                    "sources": resolve_citations(text),
                }
    comparison = st.session_state.get("comparison")
    if comparison:
        st.markdown(f"### {comparison['title']}")
        show_tool_text(comparison["text"])
        render_sources(comparison["sources"])