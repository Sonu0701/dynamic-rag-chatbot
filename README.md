# 🧠 Dynamic RAG Chatbot

Upload any PDF and chat with it using AI (Retrieval-Augmented Generation).

---

## 🚀 Features

- 📄 Upload any PDF and ask questions
- 🔄 Dynamic indexing (old document removed automatically)
- 🧠 Context-aware answers using RAG
- 💬 Chat history with memory
- 📚 Source tracking (see which PDF was used)
- 🌙 Dark mode UI

---

## 🛠 Tech Stack

### Backend
- FastAPI
- LangChain
- Pinecone (Vector Database)
- Mistral AI (LLM)

### Frontend
- React (Vite)
- CSS

---

## ⚙️ Setup

### 🔹 Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # mac/linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload


FRONTEND 

cd frontend
npm install
npm run dev