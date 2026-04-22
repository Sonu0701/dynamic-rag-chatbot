from fastapi import FastAPI, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid

from rag_pipeline import create_vectorstore, get_chain

app = FastAPI()

# CORS (for React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 GLOBAL STATE
vectorstore = None
retriever = None
model = None
current_file = None

# memory
chat_history = []
MAX_HISTORY = 10

# ensure uploads folder exists
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
def home():
    return {"message": "Dynamic RAG Chatbot is running 🚀"}


# 🚀 Upload API
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    global vectorstore, retriever, model, chat_history, current_file

    try:
        # unique filename (avoid overwrite issues)
        unique_name = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, unique_name)

        # save file
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # 🔥 RESET SYSTEM
        chat_history = []
        vectorstore = None
        retriever = None
        model = None

        # track file name (for UI)
        current_file = file.filename

        # create vectorstore
        vectorstore = create_vectorstore(file_path)
        retriever, model = get_chain(vectorstore)

        return {
            "message": f"{file.filename} uploaded and indexed ✅",
            "current_file": current_file
        }

    except Exception as e:
        print("❌ Upload error:", str(e))
        return {"error": "Upload failed"}


# 🚀 Chat API
@app.get("/chat")
def chat(query: str = Query(..., min_length=1)):
    global retriever, model, chat_history

    try:
        if retriever is None or model is None:
            return {"answer": "Please upload a PDF first.", "sources": []}

        query = query.strip()

        # 🔥 FILTER GREETINGS
        if query.lower() in ["hi", "hello", "hii", "hey"]:
            return {
                "answer": "👋 Hi! Please ask something from your uploaded document.",
                "sources": []
            }

        # 🔥 FILTER SHORT QUESTIONS
        if len(query.split()) < 2:
            return {
                "answer": "Please ask a more detailed question.",
                "sources": []
            }

        # 🔥 MEMORY CONTEXT
        if len(chat_history) >= 2:
            history_text = "\n".join(chat_history[-6:])
            enhanced_query = f"""
Previous conversation:
{history_text}

Current question:
{query}
"""
        else:
            enhanced_query = query

        # 🔥 RETRIEVAL
        docs = retriever.invoke(enhanced_query)

        if not docs:
            return {
                "answer": "I don't know based on the document.",
                "sources": []
            }

        # 🔥 CONTEXT BUILD
        context = "\n\n".join([d.page_content for d in docs[:5]])

        # 🔥 IMPROVED PROMPT (KEY CHANGE)
        prompt = f"""
You are a helpful AI assistant.

Your job is to answer clearly and in a structured way.

Formatting rules:
- Use simple headings (no ** or markdown symbols)
- Use bullet points (•)
- Add spacing between sections
- Keep answers clean and easy to read
- Avoid long paragraphs
- Do NOT include symbols like *, **, ##

If answer is not found:
I don't know based on the document

---------------------

Context:
{context}

Question:
{enhanced_query}

---------------------

Answer:
"""

        # 🔥 LLM CALL
        result = model.invoke(prompt)
        response = result.content.strip()

        if not response:
            response = "I don't know based on the document."

        # 🔥 SOURCES
        sources = list(set([
            os.path.basename(doc.metadata.get("source", "unknown"))
            for doc in docs
        ]))

        # 🔥 SAVE MEMORY
        chat_history.append(f"User: {query}")
        chat_history.append(f"Bot: {response}")

        if len(chat_history) > MAX_HISTORY:
            chat_history = chat_history[-MAX_HISTORY:]

        return {
            "answer": response,
            "sources": sources
        }

    except Exception as e:
        print("❌ Chat error:", e)
        return {
            "answer": "Something went wrong.",
            "sources": []
        }