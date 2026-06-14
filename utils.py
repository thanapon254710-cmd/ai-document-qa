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
            f"""You are a helpful document assistant. Answer based on the context only.
            IMPORTANT: Do NOT use markdown formatting. No **bold**, no *italic*, no bullet points with *.
            Use plain text only. Use numbers (1. 2. 3.) for lists instead.

            Context: {context}

            Question: {question}"""
        )
        return response.text

    return answer