import streamlit as st

from src.llm import LLMError
from src.pdf_processing import extract_pages, chunk_pages, PDFError
from src.vector_store import add_chunks, clear_collection, stored_documents, VectorStoreError
from src.rag import answer_question

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
            st.rerun()
    else:
        st.caption("No documents stored yet.")

# ---------- Main area: question answering ----------
st.subheader("Ask a question about your documents")
question = st.text_area("Your question")

if st.button("Ask"):
    if not question.strip():
        st.warning("Please type a question first.")
    elif not docs:
        st.warning("Upload and process at least one PDF first.")
    else:
        try:
            with st.spinner("Searching documents and generating an answer..."):
                result = answer_question(question)
            st.markdown(result["answer"])
            if result["sources"]:
                st.subheader("Sources")
                for s in result["sources"]:
                    with st.expander(f"{s['source']} - page {s['page']} (similarity {s['score']})"):
                        st.text(s["text"])
        except (LLMError, VectorStoreError) as e:
            st.error(str(e))