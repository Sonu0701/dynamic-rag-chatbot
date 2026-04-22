import os
from dotenv import load_dotenv

from langchain_pinecone import PineconeVectorStore
from langchain_mistralai import ChatMistralAI
from pinecone import Pinecone   # 🔥 NEW

from helper import load_pdf, split_documents, get_embeddings

# Load env
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

index_name = "dynamic-rag"

# 🔥 FIXED NAMESPACE
NAMESPACE = "current-doc"


# 🔥 STEP 1: Create vectorstore from uploaded PDF
def create_vectorstore(file_path):
    # 🔥 CONNECT TO PINECONE
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(index_name)

    # 🔥 DELETE OLD DATA (CRITICAL FIX)
    try:
        index.delete(delete_all=True, namespace=NAMESPACE)
        print("🧹 Old vectors deleted")
    except Exception as e:
        print("⚠️ Delete warning:", e)

    # load PDF
    docs = load_pdf(file_path)

    # split into chunks
    chunks = split_documents(docs)

    # metadata
    for doc in chunks:
        doc.metadata["source"] = os.path.basename(file_path)

    # 🔥 CREATE NEW VECTORSTORE
    vectorstore = PineconeVectorStore.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        index_name=index_name,
        namespace=NAMESPACE
    )

    print("✅ New vectorstore created")

    return vectorstore


# 🔥 STEP 2: Get retriever + model
def get_chain(vectorstore):
    # 🔥 RETRIEVER (same namespace)
    retriever = vectorstore.as_retriever(
        search_kwargs={
            "k": 5,
            "namespace": NAMESPACE
        }
    )

    # LLM
    model = ChatMistralAI(
        model="mistral-small",
        api_key=MISTRAL_API_KEY,
        temperature=0
    )

    return retriever, model