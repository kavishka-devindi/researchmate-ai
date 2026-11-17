import streamlit as st

from src.llm import generate_answer, LLMError
from src.pdf_processing import extract_pages, chunk_pages, PDFError

st.set_page_config(page_title="Document Intelligence Agent", page_icon="📄", layout="wide")

# Memory that survives reruns
if "chunks" not in st.session_state:
    st.session_state.chunks = []
    st.session_state.doc_stats = []

st.title("📄 AI Research & Document Intelligence Agent")

# ---------- Sidebar: upload and process ----------
with st.sidebar:
    st.header("Documents")
    uploaded_files = st.file_uploader(
        "Upload PDF files", type=["pdf"], accept_multiple_files=True
    )

    if st.button("Process documents"):
        if not uploaded_files:
            st.warning("Please upload at least one PDF first.")
        else:
            all_chunks, stats = [], []
            with st.spinner("Reading documents..."):
                for f in uploaded_files:
                    try:
                        pages = extract_pages(f.getvalue(), f.name)
                        chunks = chunk_pages(pages)
                        all_chunks.extend(chunks)
                        stats.append(
                            {"File": f.name, "Pages with text": len(pages), "Chunks": len(chunks)}
                        )
                    except PDFError as e:
                        st.error(str(e))
            st.session_state.chunks = all_chunks
            st.session_state.doc_stats = stats
            if stats:
                st.success(f"Processed {len(stats)} document(s).")

# ---------- Main area ----------
if st.session_state.doc_stats:
    st.subheader("Processed documents")
    st.dataframe(st.session_state.doc_stats, hide_index=True)

    with st.expander("Preview the first 3 chunks"):
        for c in st.session_state.chunks[:3]:
            st.caption(f"{c['source']} - page {c['page']} ({c['chunk_id']})")
            st.text(c["text"])
else:
    st.info("Upload PDFs in the sidebar and click 'Process documents'.")

st.divider()
st.subheader("Ask the model (no documents used yet)")
question = st.text_area("Your question")

if st.button("Ask"):
    if not question.strip():
        st.warning("Please type a question first.")
    else:
        try:
            with st.spinner("Thinking..."):
                answer = generate_answer(question)
            st.write(answer)
        except LLMError as e:
            st.error(str(e))