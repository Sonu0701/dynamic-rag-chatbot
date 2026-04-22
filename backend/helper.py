from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader


# 🔥 Load single PDF (dynamic)
def load_pdf(file_path):
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    # ✅ Add clean metadata
    for doc in docs:
        doc.metadata["source"] = file_path
        doc.metadata["page"] = doc.metadata.get("page", 0)

    return docs


# 🔥 Split into chunks
def split_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,        # 🔥 increased (better context)
        chunk_overlap=150      # 🔥 improved overlap
    )
    return splitter.split_documents(docs)


# 🔥 Embeddings
def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )