from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid

from rag_pipeline import create_vectorstore, get_chain

app = FastAPI()

# CORS (for React / Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Later restrict to your Vercel domain
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
        # 🔥 Validate file type
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are allowed."
            )

        # unique filename (avoid overwrite)
        unique_name = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, unique_name)

        # save uploaded file
        with open(file_path, "wb") as f:
            f.write(await file.read())

        print(f"📄 File saved successfully: {file_path}")

        # 🔥 RESET SYSTEM
        chat_history = []
        vectorstore = None
        retriever = None
        model = None

        # track file for UI
        current_file = file.filename

        # 🔥 VECTORSTORE CREATION
        print("⚡ Creating vectorstore...")
        vectorstore = create_vectorstore(file_path)

        if vectorstore is None:
            raise Exception("Vectorstore creation failed.")

        print("✅ Vectorstore created")

        # 🔥 CHAIN SETUP
        retriever, model = get_chain(vectorstore)

        if retriever is None or model is None:
            raise Exception("Retriever or model initialization failed.")

        print("✅ Retriever and model initialized")

        return {
            "message": f"{file.filename} uploaded and indexed ✅",
            "current_file": current_file
        }

    except HTTPException as http_error:
        # Pass FastAPI HTTP errors directly
        print("❌ Upload HTTP error:", http_error.detail)
        raise http_error

    except Exception as e:
        # 🔥 REAL ERROR RETURN
        error_message = str(e)

        print("❌ Upload error:", error_message)

        raise HTTPException(
            status_code=500,
            detail=error_message
        )


# 🚀 Chat API
@app.get("/chat")
def chat(query: str = Query(..., min_length=1)):
    global retriever, model, chat_history

    try:
        # 🔥 Check if PDF uploaded
        if retriever is None or model is None:
            return {
                "answer": "Please upload a PDF first.",
                "sources": []
            }

        query = query.strip()

        # 🔥 Greeting filter
        if query.lower() in ["hi", "hello", "hii", "hey"]:
            return {
                "answer": "👋 Hi! Please ask something from your uploaded document.",
                "sources": []
            }

        # 🔥 Short query filter
        if len(query.split()) < 2:
            return {
                "answer": "Please ask a more detailed question.",
                "sources": []
            }

        # 🔥 Memory context
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

        # 🔥 Retrieve relevant docs
        docs = retriever.invoke(enhanced_query)

        if not docs:
            return {
                "answer": "I don't know based on the document.",
                "sources": []
            }

        # 🔥 Build context
        context = "\n\n".join(
            [doc.page_content for doc in docs[:5]]
        )

        # 🔥 Prompt
        prompt = f"""
You are a helpful AI assistant.

Your job is to answer clearly and in a structured way.

Formatting rules:
- Use simple headings (no markdown)
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

        # 🔥 LLM Call
        result = model.invoke(prompt)
        response = result.content.strip()

        if not response:
            response = "I don't know based on the document."

        # 🔥 Sources
        sources = list(
            set(
                [
                    os.path.basename(
                        doc.metadata.get("source", "unknown")
                    )
                    for doc in docs
                ]
            )
        )

        # 🔥 Save memory
        chat_history.append(f"User: {query}")
        chat_history.append(f"Bot: {response}")

        if len(chat_history) > MAX_HISTORY:
            chat_history = chat_history[-MAX_HISTORY:]

        return {
            "answer": response,
            "sources": sources
        }

    except Exception as e:
        error_message = str(e)

        print("❌ Chat error:", error_message)

        return {
            "answer": f"Something went wrong: {error_message}",
            "sources": []
        }