import streamlit as st

from src.agent import run_agent, AgentError
from src.llm import LLMError
from src.pdf_processing import extract_pages, chunk_pages, PDFError
from src.rag import answer_question
from src.vector_store import add_chunks, clear_collection, stored_documents, VectorStoreError

st.set_page_config(page_title="Document Intelligence Agent", page_icon="📄", layout="wide")

st.title("📄 AI Research & Document Intelligence Agent")

# ---------- Sidebar: upload, index, stored documents ----------
with st.sidebar:
    st.header("Documents")
    uploaded_files = st.file_uploader(
        "Upload PDF files", type=["pdf"], accept_multiple_files=True
    )

    if st.button("Process documents"):
        if not uploaded_files:
            st.warning("Please upload at least one PDF first.")
        else:
            with st.spinner("Reading and indexing documents..."):
                for f in uploaded_files:
                    try:
                        pages = extract_pages(f.getvalue(), f.name)
                        added = add_chunks(chunk_pages(pages))
                        if added:
                            st.success(f"{f.name}: indexed {added} new chunks.")
                        else:
                            st.info(f"{f.name}: already indexed.")
                    except (PDFError, VectorStoreError) as e:
                        st.error(str(e))

    st.divider()
    st.subheader("Stored documents")
    docs = stored_documents()
    if docs:
        st.dataframe(docs, hide_index=True)
        if st.button("Clear all documents"):
            clear_collection()
            st.session_state.pop("result", None)
            st.rerun()
    else:
        st.caption("No documents stored yet.")

# ---------- Main area ----------
mode = st.radio("Mode", ["Agent (chooses tools)", "Direct RAG"], horizontal=True)
question = st.text_area("Your question")

if st.button("Ask"):
    if not question.strip():
        st.warning("Please type a question first.")
    elif not docs:
        st.warning("Upload and process at least one PDF first.")
    else:
        try:
            with st.spinner("Working on your question..."):
                if mode.startswith("Agent"):
                    result = run_agent(question)
                    result["mode"] = "agent"
                else:
                    result = answer_question(question)
                    result["mode"] = "rag"
                    result["tool_calls"] = []
            st.session_state.result = result
        except (LLMError, VectorStoreError, AgentError) as e:
            st.error(str(e))

# Show the last result (it survives reruns because it lives in session_state)
result = st.session_state.get("result")
if result:
    st.markdown(result["answer"])

    if result["mode"] == "agent":
        calls = result["tool_calls"]
        with st.expander(f"Agent steps ({len(calls)} tool call(s))"):
            if calls:
                for i, c in enumerate(calls, start=1):
                    st.text(f"{i}. {c['tool']}  |  input: {c['args']}")
            else:
                st.write("No tools used. The agent answered directly.")

    if result["sources"]:
        st.subheader("Sources")
        for s in result["sources"]:
            label = f"{s['source']} - page {s['page']}"
            if s.get("score") is not None:
                label += f" (similarity {s['score']})"
            if s["text"] is None:
                st.warning(f"Could not verify this citation: {label}")
            else:
                with st.expander(label):
                    st.text(s["text"])