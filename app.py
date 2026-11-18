import base64
import re
from datetime import datetime
from html import escape

import streamlit as st

from src.agent import run_agent, resolve_citations, AgentError
from src.history import add_entry, load_history, time_ago
from src.llm import LLMError
from src.pdf_processing import extract_pages, chunk_pages, PDFError
from src.rag import answer_question
from src.tools import summarize_document, compare_documents
from src.vector_store import add_chunks, clear_collection, stored_documents, VectorStoreError

APP_NAME = "PaperPilot"   # change this one line to rename the app

st.set_page_config(page_title=APP_NAME, page_icon="📄", layout="wide")

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

# Transparent colours, so everything looks right in both light and dark mode
st.markdown(
    """<style>
.hero {display: flex; justify-content: space-between; align-items: center; gap: 1rem;
       padding: 1.4rem 1.8rem; border-radius: 22px; margin-bottom: 1rem;
       background: linear-gradient(135deg, rgba(234,88,12,0.20), rgba(251,191,36,0.12));
       border: 1px solid rgba(234,88,12,0.28);}
.hero-title {font-size: 2rem; font-weight: 700; margin-bottom: 0.3rem;}
.hero p {margin: 0; opacity: 0.8; max-width: 34rem;}
.hero img {height: 120px; flex-shrink: 0;}
.stat-card {display: flex; align-items: center; gap: 0.9rem; padding: 1rem 1.1rem;
            border-radius: 16px; background: rgba(128,128,128,0.08);
            border: 1px solid rgba(128,128,128,0.22);}
.stat-card .icon {display: flex; align-items: center; justify-content: center;
                  width: 2.8rem; height: 2.8rem; border-radius: 14px; font-size: 1.4rem;
                  background: rgba(234,88,12,0.16);}
.stat-card .num {font-size: 1.8rem; font-weight: 700; line-height: 1.1;}
.stat-card .lbl {opacity: 0.75; font-size: 0.85rem;}
.doc-row {display: flex; justify-content: space-between; align-items: center;
          padding: 0.55rem 0.1rem; border-bottom: 1px solid rgba(128,128,128,0.2);}
.doc-row:last-child {border-bottom: none;}
.pill {padding: 0.15rem 0.65rem; border-radius: 999px; font-size: 0.75rem;
       background: rgba(34,197,94,0.20);}
.activity {padding: 0.35rem 0; font-size: 0.92rem;}
.muted {opacity: 0.65; font-size: 0.8rem;}
.power-card {padding: 0.9rem 1rem; border-radius: 16px; text-align: center; font-size: 0.85rem;
             background: linear-gradient(135deg, rgba(234,88,12,0.18), rgba(251,191,36,0.10));
             border: 1px solid rgba(234,88,12,0.25);}
.st-key-qa_upload button, .st-key-qa_chat button,
.st-key-qa_summary button, .st-key-qa_compare button {
    min-height: 3.2rem; border-radius: 14px; font-weight: 600;}
.st-key-qa_upload button {background: rgba(234,88,12,0.15); border: 1px solid rgba(234,88,12,0.35);}
.st-key-qa_chat button {background: rgba(245,158,11,0.15); border: 1px solid rgba(245,158,11,0.35);}
.st-key-qa_summary button {background: rgba(124,58,237,0.14); border: 1px solid rgba(124,58,237,0.35);}
.st-key-qa_compare button {background: rgba(34,197,94,0.14); border: 1px solid rgba(34,197,94,0.35);}
.st-key-chip_summary button, .st-key-chip_compare button, .st-key-chip_docs button {
    border-radius: 999px; font-size: 0.85rem; padding: 0.15rem 0.9rem;}
</style>""",
    unsafe_allow_html=True,
)

TOOL_LABELS = {
    "list_documents": "Checked which documents are uploaded",
    "search_documents": "Searched the documents",
    "answer_from_documents": "Looked up an answer",
    "summarize_document": "Read a document to summarise it",
    "compare_documents": "Compared two documents",
}
ACTIVITY_ICONS = {"question": "💬", "summary": "📝", "comparison": "⚖️", "upload": "📁"}
ACTIVITY_VERBS = {"question": "Asked", "summary": "Summarised", "comparison": "Compared", "upload": "Uploaded"}

if "messages" not in st.session_state:
    st.session_state.messages = []


# ---------- Helpers ----------
def greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    return "Good afternoon" if hour < 18 else "Good evening"


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


# ---------- Data and settings used by all pages ----------
docs = stored_documents()
names = [d["File"] for d in docs]

with st.sidebar:
    with st.expander("Advanced"):
        style = st.radio(
            "Answer style",
            ["Smart assistant (recommended)", "Quick answer"],
            help="Smart assistant works out what you need: it can search, summarise or "
            "compare documents. Quick answer simply searches once and replies.",
        )
        show_steps = st.checkbox("Show how answers were found", value=True)
    use_agent = style.startswith("Smart")

    st.markdown(
        f'<div class="power-card"><b>{escape(APP_NAME)}</b><br>'
        "Powered by Gemini · RAG · LangGraph</div>",
        unsafe_allow_html=True,
    )
    st.caption("Switch light/dark mode in the ⋮ menu, then Settings.")
    st.caption("Uses the Gemini free tier. Please avoid uploading private or sensitive documents.")


# ---------- Page: Dashboard ----------
def page_dashboard():
    st.markdown(
        f'<div class="hero"><div><div class="hero-title">{greeting()}! 👋</div>'
        f"<p>Welcome to {escape(APP_NAME)}, your AI research assistant. Ask questions, summarise "
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
            st.switch_page(P_CHAT)

    chip1, chip2, chip3, _ = st.columns([2, 2, 2.4, 3])
    if chip1.button("💡 Summarise a document", key="chip_summary"):
        st.switch_page(P_SUM)
    if chip2.button("⚖️ Compare documents", key="chip_compare"):
        st.switch_page(P_CMP)
    if chip3.button("❓ What documents do I have?", key="chip_docs"):
        st.session_state.pending_question = "What documents do I have?"
        st.switch_page(P_CHAT)
    st.write("")

    history = load_history()
    questions = sum(1 for h in history if h["kind"] == "question")
    stats = [
        ("📄", len(docs), "Documents"),
        ("📑", sum(d["Pages"] for d in docs), "Pages with text"),
        ("🧩", sum(d["Chunks"] for d in docs), "Searchable sections"),
        ("💬", questions, "Questions asked"),
    ]
    for col, (icon, num, label) in zip(st.columns(4), stats):
        col.markdown(
            f'<div class="stat-card"><div class="icon">{icon}</div>'
            f'<div><div class="num">{num}</div><div class="lbl">{label}</div></div></div>',
            unsafe_allow_html=True,
        )
    st.write("")

    left, right = st.columns([3, 2])
    with left:
        with st.container(border=True):
            st.markdown("#### 📄 Your documents")
            if docs:
                rows = "".join(
                    f'<div class="doc-row"><div><b>{escape(d["File"])}</b>'
                    f'<div class="muted">{d["Pages"]} pages with text</div></div>'
                    '<span class="pill">Ready</span></div>'
                    for d in docs[:5]
                )
                st.markdown(rows, unsafe_allow_html=True)
            else:
                st.caption("No documents yet.")
                if st.button("Upload your first document", type="primary", key="dash_upload_first"):
                    st.switch_page(P_DOCS)

        with st.container(border=True):
            st.markdown("#### 🕘 Recent activity")
            recent = history[-5:][::-1]
            if recent:
                rows = "".join(
                    f'<div class="activity">{ACTIVITY_ICONS.get(h["kind"], "•")} '
                    f'{ACTIVITY_VERBS.get(h["kind"], "")}: {escape(h["text"])} '
                    f'<span class="muted">· {time_ago(h["time"])}</span></div>'
                    for h in recent
                )
                st.markdown(rows, unsafe_allow_html=True)
            else:
                st.caption("Your questions and uploads will appear here.")

    with right:
        with st.container(border=True):
            st.markdown("#### ⚡ Quick actions")
            if st.button("📁 Upload documents", use_container_width=True, key="qa_upload"):
                st.switch_page(P_DOCS)
            if st.button("💬 Ask a question", use_container_width=True, key="qa_chat"):
                st.switch_page(P_CHAT)
            if st.button("📝 Summarise a document", use_container_width=True, key="qa_summary"):
                st.switch_page(P_SUM)
            if st.button("⚖️ Compare documents", use_container_width=True, key="qa_compare"):
                st.switch_page(P_CMP)


# ---------- Page: Chat ----------
def page_chat():
    st.subheader("Chat with your documents")
    if not docs:
        st.info("Upload one or more PDFs in **My Documents** to begin.")
        if st.button("Go to My Documents", key="chat_to_docs"):
            st.switch_page(P_DOCS)
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
                if msg.get("agent") and show_steps:
                    render_steps(msg["tool_calls"])
                render_sources(msg["sources"])

    typed = st.chat_input("Ask about your documents...", disabled=not docs)
    question = typed or st.session_state.pop("pending_question", None)

    if question:
        add_entry("question", question[:80])
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        try:
            with st.spinner("Thinking..."):
                if use_agent:
                    res = run_agent(question)
                else:
                    res = answer_question(question)
                    res["tool_calls"] = []
            st.session_state.messages.append(
                {"role": "assistant", "content": res["answer"], "tool_calls": res["tool_calls"],
                 "sources": res["sources"], "agent": use_agent}
            )
        except (LLMError, VectorStoreError, AgentError) as e:
            st.session_state.messages.append(
                {"role": "assistant", "content": f"⚠️ {e}", "tool_calls": [], "sources": [], "agent": False}
            )
        st.rerun()

    if st.session_state.messages:
        if st.button("🗑️ Clear chat", key="clear_chat"):
            st.session_state.messages = []
            st.rerun()


# ---------- Page: My Documents ----------
def page_documents():
    st.subheader("My documents")
    with st.container(border=True):
        uploaded_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)
        if st.button("Process documents", type="primary"):
            if not uploaded_files:
                st.warning("Please upload at least one PDF first.")
            else:
                report = []
                with st.spinner("Reading and indexing documents..."):
                    for f in uploaded_files:
                        try:
                            pages = extract_pages(f.getvalue(), f.name)
                            added = add_chunks(chunk_pages(pages))
                            if added:
                                report.append(("success", f"{f.name}: ready ({added} sections indexed)."))
                                add_entry("upload", f.name)
                            else:
                                report.append(("info", f"{f.name}: already uploaded."))
                        except (PDFError, VectorStoreError) as e:
                            report.append(("error", str(e)))
                st.session_state.upload_report = report
                st.rerun()

    for kind, message in st.session_state.get("upload_report", []):
        getattr(st, kind)(message)

    st.markdown("#### Stored documents")
    if docs:
        st.dataframe(docs, hide_index=True, use_container_width=True)
        if st.button("Remove all documents"):
            clear_collection()
            st.session_state.messages = []
            for key in ("summary", "comparison", "upload_report"):
                st.session_state.pop(key, None)
            st.rerun()
    else:
        st.caption("No documents yet.")


# ---------- Page: Summary ----------
def page_summary():
    st.subheader("Summarise a document")
    if not names:
        st.info("Upload and process at least one PDF first.")
        return
    with st.container(border=True):
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


# ---------- Page: Compare ----------
def page_compare():
    st.subheader("Compare two documents")
    if len(names) < 2:
        st.info("Upload and process at least two PDFs to compare them.")
        return
    with st.container(border=True):
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


# ---------- Navigation ----------
P_DASH = st.Page(page_dashboard, title="Dashboard", icon=":material/home:", default=True)
P_CHAT = st.Page(page_chat, title="Chat", icon=":material/chat:")
P_DOCS = st.Page(page_documents, title="My Documents", icon=":material/folder:")
P_SUM = st.Page(page_summary, title="Summary", icon=":material/summarize:")
P_CMP = st.Page(page_compare, title="Compare", icon=":material/compare_arrows:")

st.navigation([P_DASH, P_CHAT, P_DOCS, P_SUM, P_CMP]).run()