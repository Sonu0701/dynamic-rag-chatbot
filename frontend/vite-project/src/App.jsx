import { useState, useRef, useEffect } from "react";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL;

function App() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [file, setFile] = useState(null);
  const [currentFile, setCurrentFile] = useState("");
  const [darkMode, setDarkMode] = useState(true);
  const [uploading, setUploading] = useState(false);

  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const getTime = () => {
    return new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // 🗑 Clear chat
  const clearChat = () => {
    setMessages([]);
    setCurrentFile("");
    setFile(null);
    setQuery("");
  };

  // 📄 Upload PDF
  const uploadFile = async () => {
    if (!file) {
      alert("Please select a PDF first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setUploading(true);

    try {
      const res = await fetch(`${API_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      const text = await res.text();

      let data = {};
      try {
        data = text ? JSON.parse(text) : {};
      } catch {
        throw new Error(`Invalid server response (${res.status})`);
      }

      if (!res.ok) {
        throw new Error(
          data.detail || data.error || `Upload failed (${res.status})`
        );
      }

      setCurrentFile(data.current_file || file.name);

      setMessages([
        {
          type: "bot",
          text: `✅ PDF uploaded successfully: ${data.current_file || file.name}`,
          time: getTime(),
        },
      ]);

      setQuery("");

    } catch (err) {
      console.error("Upload error:", err);

      setMessages([
        {
          type: "bot",
          text: `❌ ${err.message}`,
          time: getTime(),
        },
      ]);
    } finally {
      setUploading(false);
    }
  };

  // 💬 Send message
  const sendMessage = async () => {
    if (!query.trim() || loading || !currentFile) return;

    const userMsg = {
      type: "user",
      text: query,
      time: getTime(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await fetch(
        `${API_URL}/chat?query=${encodeURIComponent(query)}`
      );

      const text = await res.text();

      let data = {};
      try {
        data = text ? JSON.parse(text) : {};
      } catch {
        throw new Error(`Invalid server response (${res.status})`);
      }

      if (!res.ok) {
        throw new Error(
          data.detail || data.error || `Chat failed (${res.status})`
        );
      }

      const botMsg = {
        type: "bot",
        text: data.answer || "No response received.",
        sources: data.sources || [],
        time: getTime(),
      };

      setMessages((prev) => [...prev, botMsg]);

    } catch (err) {
      console.error("Chat error:", err);

      setMessages((prev) => [
        ...prev,
        {
          type: "bot",
          text: `❌ ${err.message}`,
          time: getTime(),
        },
      ]);
    } finally {
      setLoading(false);
      setQuery("");
    }
  };

  return (
    <div className={darkMode ? "app dark" : "app"}>
      <div className="chat-container">

        {/* Header */}
        <div className="header">
          🧠 Dynamic RAG Assistant

          <div className="header-actions">
            <button onClick={clearChat}>🗑</button>
            <button onClick={() => setDarkMode(!darkMode)}>
              {darkMode ? "☀️" : "🌙"}
            </button>
          </div>
        </div>

        {/* Current File */}
        {currentFile && (
          <div className="current-file">
            📄 {currentFile}
          </div>
        )}

        {/* Upload */}
        <div className="upload">
          <input
            type="file"
            accept="application/pdf"
            onChange={(e) => setFile(e.target.files[0])}
          />
          <button onClick={uploadFile} disabled={uploading}>
            {uploading ? "Uploading..." : "Upload"}
          </button>
        </div>

        {/* Chat */}
        <div className="chat-box">

          {/* Empty State */}
          {messages.length === 0 && (
            <div className="empty">
              <p>📄 Upload a PDF and start asking questions</p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`bubble ${msg.type}`}>
              <p style={{ whiteSpace: "pre-line" }}>
                {msg.text}
              </p>

              <span className="time">{msg.time}</span>

              {msg.sources?.length > 0 && (
                <div className="sources">
                  <small>Sources:</small>
                  <ul>
                    {msg.sources.map((s, index) => (
                      <li key={index}>{s}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}

          {/* Typing animation */}
          {loading && (
            <div className="typing">
              <span></span>
              <span></span>
              <span></span>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Input */}
        <div className="input-area">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder={
              currentFile
                ? "Ask about your document..."
                : "Upload a PDF first..."
            }
            disabled={!currentFile}
          />
          <button
            onClick={sendMessage}
            disabled={!currentFile || loading}
          >
            Send
          </button>
        </div>

      </div>
    </div>
  );
}

export default App;