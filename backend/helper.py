from langchain_mistralai import MistralAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
import re


# 🔥 Load single PDF
def load_pdf(file_path):
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    # Clean extracted text (remove excessive whitespace, artifacts)
    for doc in docs:
        doc.page_content = clean_text(doc.page_content)
        doc.metadata["source"] = file_path
        doc.metadata["page"] = doc.metadata.get("page", 0)

    # Filter out empty or near-empty pages
    docs = [doc for doc in docs if len(doc.page_content.strip()) > 50]

    print(f"📄 Loaded {len(docs)} pages from PDF")
    return docs


def clean_text(text: str) -> str:
    """Remove common PDF extraction noise."""
    # Collapse multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove non-printable characters
    text = re.sub(r'[^\x20-\x7E\n]', ' ', text)
    # Collapse multiple spaces
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


# 🔥 Split documents — larger chunks with more overlap for better context
def split_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,       # ⬆ was 800 — captures more context per chunk
        chunk_overlap=250,     # ⬆ was 150 — reduces boundary cut-offs
        separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    print(f"✂️  Split into {len(chunks)} chunks")
    return chunks


# 🔥 Mistral Embeddings
def get_embeddings():
    return MistralAIEmbeddings(
        model="mistral-embed"
    )