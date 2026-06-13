import google.generativeai as genai
import tempfile, os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

def process_pdf(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
        f.write(uploaded_file.read())
        tmp_path = f.name
    loader = PyPDFLoader(tmp_path)
    pages = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(pages)
    os.unlink(tmp_path)
    return chunks

def create_qa_chain(chunks):
    context = "\n\n".join([c.page_content for c in chunks])
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel("gemini-2.5-flash")

    def answer(question):
        response = model.generate_content(
            f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer based on the context only."
        )
        return response.text

    return answer