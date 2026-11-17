import streamlit as st

from src.llm import generate_answer, LLMError

st.set_page_config(page_title="Document Intelligence Agent", page_icon="📄")

st.title("📄 AI Research & Document Intelligence Agent")
st.write("Ask the model anything. (Document features come in later phases.)")

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