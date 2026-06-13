import streamlit as st
import os
from utils import process_pdf, create_qa_chain
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

st.set_page_config(page_title="AI Document Q&A", page_icon="📄")
st.title("📄 AI Document Q&A")
st.caption("อัปโหลด PDF แล้วถามคำถามได้เลย")

# Upload PDF
uploaded_file = st.file_uploader("อัปโหลดไฟล์ PDF", type="pdf")

if uploaded_file:
    with st.spinner("กำลังประมวลผลเอกสาร..."):
        if "qa_chain" not in st.session_state:
            chunks = process_pdf(uploaded_file)
            st.session_state.qa_chain = create_qa_chain(chunks)
            st.session_state.messages = []
    st.success("พร้อมแล้ว! ถามคำถามได้เลย")

    # Chat history
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # Input
    if question := st.chat_input("ถามอะไรก็ได้เกี่ยวกับเอกสาร..."):
        st.session_state.messages.append({"role": "user", "content": question})
        st.chat_message("user").write(question)

        with st.spinner("กำลังคิด..."):
            result = st.session_state.qa_chain(question)

        st.session_state.messages.append({"role": "assistant", "content": result})
        st.chat_message("assistant").write(result)