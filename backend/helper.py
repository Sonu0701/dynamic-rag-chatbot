from langchain_mistralai import MistralAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader


# 🔥 Load single PDF
def load_pdf(file_path):
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    # metadata
    for doc in docs:
        doc.metadata["source"] = file_path
        doc.metadata["page"] = doc.metadata.get("page", 0)

    return docs


# 🔥 Split documents
def split_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150
    )
    return splitter.split_documents(docs)


# 🔥 Mistral Embeddings
def get_embeddings():
    return MistralAIEmbeddings(
        model="mistral-embed"
    )