from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import asyncio
import httpx

from rag_pipeline import create_vectorstore, get_chain

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
vectorstore  = None
retriever    = None
model        = None
current_file = None
chat_history = []
MAX_HISTORY  = 10

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── Keep-Alive Ping ──
@app.on_event("startup")
async def keep_alive():
    async def ping():
        while True:
            await asyncio.sleep(14 * 60)
            try:
                async with httpx.AsyncClient() as client:
                    await client.get(
                        "https://dynamic-rag-chatbot-tgpt.onrender.com/health"
                    )
            except:
                pass
    asyncio.create_task(ping())


@app.get("/")
def home():
    return {"message": "Dynamic RAG Chatbot is running 🚀"}


# ── Health Endpoint ──
@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    global vectorstore, retriever, model, chat_history, current_file

    try:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

        unique_name = f"{uuid.uuid4()}_{file.filename}"
        file_path   = os.path.join(UPLOAD_DIR, unique_name)

        with open(file_path, "wb") as f:
            f.write(await file.read())

        print(f"📄 File saved: {file_path}")

        # Reset all state on new upload
        chat_history = []
        vectorstore  = None
        retriever    = None
        model        = None
        current_file = file.filename

        print("⚡ Creating vectorstore...")
        vectorstore = create_vectorstore(file_path)

        if vectorstore is None:
            raise Exception("Vectorstore creation failed.")

        retriever, model = get_chain(vectorstore)

        if retriever is None or model is None:
            raise Exception("Retriever or model initialization failed.")

        print("✅ Ready")
        return {
            "message": f"{file.filename} uploaded and indexed ✅",
            "current_file": current_file
        }

    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        print("❌ Upload error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chat")
def chat(query: str = Query(..., min_length=1)):
    global retriever, model, chat_history

    try:
        if retriever is None or model is None:
            return {"answer": "Please upload a PDF first.", "sources": []}

        query = query.strip()

        # Greeting filter
        if query.lower() in ["hi", "hello", "hii", "hey"]:
            return {
                "answer": "👋 Hi! Ask me anything about your uploaded document.",
                "sources": []
            }

        # Short query filter
        if len(query.split()) < 2:
            return {"answer": "Please ask a more detailed question.", "sources": []}

        # ✅ Retrieve with score threshold
        docs = retriever.invoke(query)

        print(f"🔍 Query: '{query}' → {len(docs)} chunks passed threshold")

        if not docs:
            return {
                "answer": "❌ This question does not appear to be related to the uploaded document. Please ask something from the PDF.",
                "sources": []
            }

        # Build context with page labels
        context_parts = []
        for doc in docs:
            page = doc.metadata.get("page", "?")
            context_parts.append(f"[Page {int(page) + 1 if isinstance(page, (int, float)) else page}]\n{doc.page_content}")
        context = "\n\n---\n\n".join(context_parts)

        # Build history string
        history_text = ""
        if len(chat_history) >= 2:
            history_text = "\n".join(chat_history[-6:])

        # Strict grounded prompt
        prompt = f"""You are a precise document assistant. Answer ONLY using the document context provided below.

STRICT RULES:
- Use ONLY information from the context below.
- If the context does not contain the answer, say exactly: "This information is not available in the document."
- Do NOT use your general knowledge or training data under any circumstances.
- Be concise and structured.
- Use bullet points (•) for lists.
- Use simple section labels (no markdown symbols like *, **, ##).

{f"Conversation so far:{chr(10)}{history_text}{chr(10)}" if history_text else ""}

Document Context:
{context}

Question: {query}

Answer:"""

        result   = model.invoke(prompt)
        response = result.content.strip()

        if not response:
            response = "This information is not available in the document."

        # Sources with clean name + page
        seen    = set()
        sources = []
        for doc in docs:
            src = os.path.basename(doc.metadata.get("source", "unknown"))
            if "_" in src:
                src = "_".join(src.split("_")[1:])
            raw_page   = doc.metadata.get("page", None)
            page_label = f"page {int(raw_page) + 1}" if raw_page is not None else "page ?"
            label      = f"{src} ({page_label})"
            if label not in seen:
                seen.add(label)
                sources.append(label)

        # Save to memory
        chat_history.append(f"User: {query}")
        chat_history.append(f"Bot: {response}")
        if len(chat_history) > MAX_HISTORY:
            chat_history = chat_history[-MAX_HISTORY:]

        return {"answer": response, "sources": sources}

    except Exception as e:
        err = str(e)
        print("❌ Chat error:", err)

        if "429" in err or "rate-limited" in err or "capacity" in err.lower():
            return {
                "answer": "⏳ The AI model is temporarily overloaded. Please wait 30–60 seconds and try again.",
                "sources": []
            }

        return {"answer": f"Something went wrong: {err}", "sources": []}