# 🤖 Dynamic RAG Chatbot

> Upload any PDF and chat with it using AI — powered by Retrieval-Augmented Generation (RAG)

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?style=flat-square&logo=fastapi)
![React](https://img.shields.io/badge/React-Vite-61DAFB?style=flat-square&logo=react)
![LangChain](https://img.shields.io/badge/LangChain-RAG-orange?style=flat-square)
![Pinecone](https://img.shields.io/badge/Pinecone-VectorDB-purple?style=flat-square)
![Mistral AI](https://img.shields.io/badge/Mistral-AI-red?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=flat-square&logo=docker)

---

## 📌 What is this?

Most RAG chatbots just keep adding documents to the vector database forever — leading to stale, mixed-up answers.

**This chatbot is different.**

Every time you upload a new PDF, the old document is **automatically deleted** from Pinecone before the new one is indexed. You always get clean, accurate answers from your current document — no manual cleanup, no stale data.

---

## 🚀 Advanced Features

| Feature | Description |
|---|---|
| 📄 Dynamic PDF Upload & Re-indexing | Upload any PDF — old vectors auto-deleted, new ones indexed instantly |
| 🧠 Context-Aware RAG Responses | Top-5 most relevant chunks retrieved per query for grounded answers |
| 💬 Chat Memory | Full conversation history maintained across turns |
| 📚 Source Tracking | Every answer shows exactly which PDF it came from |
| 🌙 Dark Mode UI | Clean, modern dark mode interface built with React + Vite |
| 🐳 Dockerized Frontend & Backend | Fully containerized — run anywhere with one command |

---

## 🏗️ Architecture

```
User uploads PDF
      │
      ▼
FastAPI Backend
      │
      ├── 1. Delete old vectors from Pinecone (NAMESPACE: current-doc)
      ├── 2. Load & parse PDF (LangChain PDF Loader)
      ├── 3. Split into chunks (RecursiveCharacterTextSplitter)
      ├── 4. Embed chunks (Embedding Model)
      └── 5. Store in Pinecone Vector DB
                    │
User asks a question
                    │
                    ▼
              FastAPI /chat
                    │
      ├── Embed the question
      ├── Retrieve top-5 similar chunks from Pinecone
      ├── Build prompt with context + chat history
      └── Mistral AI generates the answer
                    │
                    ▼
         Answer + Source returned to React UI
```

---

## 🛠️ Tech Stack

### Backend
- **[FastAPI](https://fastapi.tiangolo.com/)** — High-performance async Python API
- **[LangChain](https://www.langchain.com/)** — RAG pipeline, document loading, chunking
- **[Pinecone](https://www.pinecone.io/)** — Managed vector database for semantic search
- **[Mistral AI](https://mistral.ai/)** — `mistral-small` LLM for answer generation

### Frontend
- **[React](https://react.dev/)** (with **Vite**) — Fast, modern UI
- **CSS** — Custom dark mode styling

### DevOps
- **[Docker](https://www.docker.com/)** — Containerized backend & frontend for easy deployment

---

## 📁 Project Structure

```
dynamic-rag-chatbot/
│
├── backend/
│   ├── app.py              # FastAPI routes (/upload, /chat)
│   ├── rag_pipeline.py     # Vectorstore creation & retriever setup
│   ├── helper.py           # PDF loading, chunking, embeddings
│   ├── uploads/            # Temporary PDF storage
│   ├── Dockerfile          # Backend Docker config
│   ├── requirements.txt
│   └── .env                # API keys (not committed)
│
├── frontend/
│   └── vite-project/
│       ├── src/
│       │   ├── App.jsx     # Main chat interface
│       │   └── ...
│       ├── Dockerfile      # Frontend Docker config
│       ├── package.json
│       └── vite.config.js
│
└── README.md
```

---

## ⚙️ Setup & Installation

Choose your preferred setup method:

---

### 🐳 Option 1 — Docker Setup (Recommended)

> No Python or Node.js installation needed. Just Docker.

**Backend:**
```bash
cd backend
docker build -t dynamic-rag-backend .
docker run --env-file .env -p 8000:8000 dynamic-rag-backend
```

**Frontend:**
```bash
cd frontend/vite-project
docker build -t dynamic-rag-frontend .
docker run -p 3000:80 dynamic-rag-frontend
```

- Backend runs at: `http://localhost:8000`
- Frontend runs at: `http://localhost:3000`

---

### 🔹 Option 2 — Local Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Pinecone account ([free tier works](https://www.pinecone.io/))
- Mistral AI API key ([get one here](https://console.mistral.ai/))

**Backend:**
```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file and add your keys (see below)
touch .env

# Start the server
uvicorn app:app --reload
```

**Frontend:**
```bash
cd frontend/vite-project
npm install
npm run dev
```

- Backend runs at: `http://localhost:8000`
- Frontend runs at: `http://localhost:5173`

---

## 🔑 Environment Variables

Create a `.env` file inside the `backend/` folder:

```env
PINECONE_API_KEY=your_pinecone_api_key_here
MISTRAL_API_KEY=your_mistral_api_key_here
```

| Variable | Description | Where to get it |
|---|---|---|
| `PINECONE_API_KEY` | Pinecone API key | [pinecone.io](https://www.pinecone.io/) |
| `MISTRAL_API_KEY` | Mistral AI API key | [console.mistral.ai](https://console.mistral.ai/) |

> ⚠️ Never commit your `.env` file. It is already in `.gitignore`.

---

## 🚀 How It Works — Step by Step

1. **Upload a PDF** via the React UI
2. Backend receives the file and saves it temporarily in `uploads/`
3. **Old vectors are deleted** from Pinecone (`NAMESPACE: current-doc`) — this is what makes it *dynamic*
4. The PDF is loaded and split into overlapping chunks using LangChain
5. Each chunk is embedded and stored in Pinecone
6. When you ask a question, it is embedded and the **top 5 most similar chunks** are retrieved
7. A structured prompt is built with those chunks + your chat history
8. **Mistral AI** generates a clean, formatted answer
9. The answer and source file name are returned to the UI

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `POST` | `/upload` | Upload and index a PDF |
| `GET` | `/chat?query=your question` | Ask a question about the PDF |

### Example: Upload
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@your_document.pdf"
```

### Example: Chat
```bash
curl "http://localhost:8000/chat?query=What is this document about?"
```

### Example Response
```json
{
  "answer": "This document is about...",
  "sources": ["your_document.pdf"]
}
```

---

## 🧠 Key Design Decisions

**Why dynamic deletion?**
Standard RAG apps accumulate vectors from every uploaded document. This causes the retriever to mix answers from unrelated documents. By deleting all vectors in the namespace before each new upload, this app ensures 100% clean context every time.

**Why Mistral AI over OpenAI?**
Mistral's `mistral-small` model is cost-efficient and performs well on document Q&A tasks. The API interface is nearly identical to OpenAI, making it easy to swap if needed.

**Why a fixed namespace in Pinecone?**
Using a fixed namespace (`current-doc`) makes it trivial to `delete_all` the previous document's vectors without needing to track individual vector IDs.

**Why Docker?**
Docker removes environment setup friction entirely. Anyone can clone the repo and run the full stack with two commands — no Python version conflicts, no Node.js issues.

---

## 🔮 Future Improvements

- [ ] Support multiple PDFs simultaneously (per-user namespaces)
- [ ] Re-ranking with a cross-encoder for better retrieval quality
- [ ] Streaming responses for faster perceived performance
- [ ] User authentication and personal document spaces
- [ ] Persistent chat history with PostgreSQL
- [ ] Docker Compose for single-command full-stack startup

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

---

## 📄 License

[MIT](LICENSE)

---

## 👨‍💻 Author

Built with ❤️ by [SONU KUMAR](https://github.com/Sonu0701)

⭐ If you found this useful, give it a star!