import os
import time
from dotenv import load_dotenv

from langchain_pinecone import PineconeVectorStore
from langchain_mistralai import ChatMistralAI
from pinecone import Pinecone

from helper import load_pdf, split_documents, get_embeddings

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
MISTRAL_API_KEY  = os.getenv("MISTRAL_API_KEY")

index_name = "dynamic-rag-mistral"
NAMESPACE  = "current-doc"

# ✅ Minimum cosine similarity score to accept a chunk as relevant
# Chunks scoring below this are rejected — model never sees them
RELEVANCE_THRESHOLD = 0.75


# 🔥 STEP 1: Create vectorstore from uploaded PDF
def create_vectorstore(file_path):
    pc    = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(index_name)

    # A: Count old vectors
    try:
        stats_before = index.describe_index_stats()
        old_count = stats_before.get("namespaces", {}).get(NAMESPACE, {}).get("vector_count", 0)
        print(f"📊 Vectors BEFORE delete: {old_count}")
    except Exception as e:
        print(f"⚠️ Pre-delete stats error: {e}")
        old_count = 0

    # B: Delete old namespace
    try:
        index.delete(delete_all=True, namespace=NAMESPACE)
        print("🧹 Delete command sent...")
    except Exception as e:
        print(f"⚠️ Delete warning: {e}")

    # C: Poll until Pinecone confirms deletion
    if old_count > 0:
        print("⏳ Waiting for deletion to complete...")
        for _ in range(10):
            time.sleep(2)
            try:
                remaining = index.describe_index_stats().get("namespaces", {}).get(NAMESPACE, {}).get("vector_count", 0)
                print(f"   → Remaining: {remaining}")
                if remaining == 0:
                    print("✅ Old vectors fully deleted!")
                    break
            except Exception as e:
                print(f"   ⚠️ Stats check error: {e}")
        else:
            print("⚠️ Deletion may be incomplete — proceeding anyway")
    else:
        print("✅ No old vectors — clean slate")

    # D: Load & chunk new PDF
    docs   = load_pdf(file_path)
    chunks = split_documents(docs)

    # Clean filename (strip UUID prefix)
    clean_name = os.path.basename(file_path)
    if "_" in clean_name:
        clean_name = "_".join(clean_name.split("_")[1:])
    for doc in chunks:
        doc.metadata["source"] = clean_name

    # E: Upload to Pinecone
    print(f"⬆️  Uploading {len(chunks)} chunks...")
    vectorstore = PineconeVectorStore.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        index_name=index_name,
        namespace=NAMESPACE
    )

    # F: Verify upload
    try:
        time.sleep(2)
        new_count = index.describe_index_stats().get("namespaces", {}).get(NAMESPACE, {}).get("vector_count", 0)
        print(f"📊 Vectors AFTER upload: {new_count}")
    except Exception as e:
        print(f"⚠️ Post-upload stats error: {e}")

    print("✅ Vectorstore ready!")
    return vectorstore


# 🔥 STEP 2: Get retriever + model
def get_chain(vectorstore):
    # ✅ Use similarity_score_threshold retrieval instead of MMR
    # This REJECTS chunks below the threshold before they reach the LLM
    retriever = vectorstore.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "score_threshold": RELEVANCE_THRESHOLD,  # reject irrelevant chunks
            "k": 6,
            "namespace": NAMESPACE
        }
    )

    model = MistralWithFallback(api_key=MISTRAL_API_KEY)
    return retriever, model


# 🔥 Mistral with model fallback on 429
class MistralWithFallback:
    MODEL_PRIORITY = [
        "open-mistral-nemo",
        "open-mistral-7b",
        "mistral-small-latest",
    ]

    def __init__(self, api_key):
        self.api_key = api_key

    def invoke(self, prompt):
        last_error = None
        for model_name in self.MODEL_PRIORITY:
            for attempt in range(2):
                try:
                    llm = ChatMistralAI(
                        model=model_name,
                        api_key=self.api_key,
                        temperature=0
                    )
                    print(f"🤖 Using model: {model_name}")
                    return llm.invoke(prompt)
                except Exception as e:
                    err = str(e)
                    if "429" in err or "capacity" in err.lower():
                        print(f"⚠️ 429 on {model_name} (attempt {attempt+1}), waiting...")
                        time.sleep(3 * (attempt + 1))
                        last_error = e
                        continue
                    else:
                        raise
        raise Exception(
            f"All Mistral models are rate-limited. Last error: {last_error}. "
            "Please wait 30–60 seconds and try again."
        )