import { useState, useRef, useEffect } from "react";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const getTime = () => new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

function CopyBtn({ text }) {
  const [ok, setOk] = useState(false);
  return (
    <button className="copy-btn" onClick={() => { navigator.clipboard.writeText(text); setOk(true); setTimeout(() => setOk(false), 2000); }}>
      {ok ? "✓ Copied" : "Copy"}
    </button>
  );
}

function BotIcon() {
  return (
    <div className="av av-bot">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="16" height="16">
        <rect x="3" y="8" width="18" height="13" rx="3"/>
        <path d="M8 8V6a4 4 0 018 0v2"/>
        <circle cx="9" cy="14" r="1.3" fill="currentColor" stroke="none"/>
        <circle cx="15" cy="14" r="1.3" fill="currentColor" stroke="none"/>
        <path d="M10 17.5c.6.5 3.4.5 4 0" strokeLinecap="round"/>
      </svg>
    </div>
  );
}

function UserIcon() {
  return (
    <div className="av av-user">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="16" height="16">
        <circle cx="12" cy="8" r="4"/>
        <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" strokeLinecap="round"/>
      </svg>
    </div>
  );
}

function TypingDots() {
  return (
    <div className="msg-row">
      <BotIcon />
      <div className="dots"><span/><span/><span/></div>
    </div>
  );
}

function Msg({ m }) {
  const isBot = m.type === "bot";
  return (
    <div className={`msg-row ${isBot ? "" : "msg-user-row"}`}>
      {isBot && <BotIcon />}
      <div className={`msg-wrap ${isBot ? "msg-wrap-bot" : "msg-wrap-user"}`}>
        <div className={`bubble ${isBot ? "bubble-bot" : "bubble-user"}`}>
          <p style={{ whiteSpace: "pre-line", margin: 0 }}>{m.text}</p>
        </div>
        <div className={`msg-footer ${isBot ? "" : "msg-footer-right"}`}>
          <span className="ts">{m.time}</span>
          {isBot && m.text && !m.text.startsWith("❌") && <CopyBtn text={m.text} />}
        </div>
        {isBot && m.sources?.length > 0 && (
          <div className="src-row">
            <span className="src-label">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="10" height="10"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              Sources
            </span>
            {m.sources.map((s, i) => <span key={i} className="src-chip">{s}</span>)}
          </div>
        )}
      </div>
      {!isBot && <UserIcon />}
    </div>
  );
}

export default function App() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [file, setFile] = useState(null);
  const [currentFile, setCurrentFile] = useState("");
  const [uploading, setUploading] = useState(false);
  const [drag, setDrag] = useState(false);
  const [sideOpen, setSideOpen] = useState(true);
  const fileRef = useRef(null);
  const bottomRef = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

  const pickFile = (f) => { if (f?.type === "application/pdf") setFile(f); };

  const upload = async () => {
    if (!file) return;
    const fd = new FormData(); fd.append("file", file);
    setUploading(true);
    try {
      const res = await fetch(`${API_URL}/upload`, { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload failed");
      setCurrentFile(data.current_file || file.name);
      setMessages([{ type: "bot", text: `✅ Ready! "${data.current_file || file.name}" is indexed. Ask me anything about it.`, time: getTime() }]);
    } catch (e) {
      setMessages([{ type: "bot", text: `❌ ${e.message}`, time: getTime() }]);
    } finally { setUploading(false); }
  };

  const send = async () => {
    if (!query.trim() || loading || !currentFile) return;
    const q = query; setQuery("");
    setMessages(p => [...p, { type: "user", text: q, time: getTime() }]);
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/chat?query=${encodeURIComponent(q)}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Error");
      setMessages(p => [...p, { type: "bot", text: data.answer || "No response.", sources: data.sources || [], time: getTime() }]);
    } catch (e) {
      setMessages(p => [...p, { type: "bot", text: `❌ ${e.message}`, time: getTime() }]);
    } finally { setLoading(false); }
  };

  const qCount = messages.filter(m => m.type === "user").length;

  return (
    <div className="root">
      {/* BG mesh */}
      <div className="mesh" />
      <div className="glow g1" /><div className="glow g2" /><div className="glow g3" />

      <div className={`layout ${sideOpen ? "" : "side-hidden"}`}>

        {/* ── SIDEBAR ── */}
        <aside className="side">
          <div className="side-top">
            {/* Logo */}
            <div className="logo">
              <div className="logo-mark">
                <svg viewBox="0 0 28 28" fill="none" width="18" height="18">
                  <rect x="2" y="8" width="24" height="16" rx="4" fill="url(#lgrad)"/>
                  <path d="M9 8V6.5a5 5 0 0110 0V8" stroke="white" strokeWidth="2" strokeLinecap="round"/>
                  <circle cx="10.5" cy="16" r="2" fill="white"/>
                  <circle cx="17.5" cy="16" r="2" fill="white"/>
                  <path d="M11.5 20c.7.6 4.3.6 5 0" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
                  <defs>
                    <linearGradient id="lgrad" x1="0" y1="0" x2="28" y2="28" gradientUnits="userSpaceOnUse">
                      <stop stopColor="#8b5cf6"/><stop offset="1" stopColor="#3b82f6"/>
                    </linearGradient>
                  </defs>
                </svg>
              </div>
              <div>
                <div className="logo-name">RAGmind</div>
                <div className="logo-tag">Dynamic PDF Chat</div>
              </div>
            </div>

            <div className="divider"/>

            {/* Stats strip */}
            <div className="stats">
              <div className="stat">
                <span className="stat-val">{qCount}</span>
                <span className="stat-key">Questions</span>
              </div>
              <div className="stat-sep"/>
              <div className="stat">
                <span className="stat-val">{currentFile ? "1" : "0"}</span>
                <span className="stat-key">Document</span>
              </div>
              <div className="stat-sep"/>
              <div className={`stat-badge ${currentFile ? "live" : ""}`}>
                {currentFile ? "● LIVE" : "○ IDLE"}
              </div>
            </div>

            <div className="divider"/>

            {/* Drop zone */}
            <div className="dz-label">Upload Document</div>
            <div
              className={`dz ${drag ? "dz-over" : ""} ${file ? "dz-ready" : ""}`}
              onDragOver={e => { e.preventDefault(); setDrag(true); }}
              onDragLeave={() => setDrag(false)}
              onDrop={e => { e.preventDefault(); setDrag(false); pickFile(e.dataTransfer.files[0]); }}
              onClick={() => fileRef.current?.click()}
            >
              <input ref={fileRef} type="file" accept="application/pdf" style={{ display: "none" }} onChange={e => pickFile(e.target.files[0])} />
              {file ? (
                <>
                  <div className="dz-icon-wrap dz-ok">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="20" height="20">
                      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                      <polyline points="14 2 14 8 20 8"/>
                      <polyline points="9 15 11 17 15 13"/>
                    </svg>
                  </div>
                  <p className="dz-fname">{file.name.length > 26 ? file.name.slice(0,26)+"…" : file.name}</p>
                  <p className="dz-sub">Tap to change</p>
                </>
              ) : (
                <>
                  <div className="dz-icon-wrap">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="20" height="20">
                      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                      <polyline points="17 8 12 3 7 8"/>
                      <line x1="12" y1="3" x2="12" y2="15"/>
                    </svg>
                  </div>
                  <p className="dz-fname">Drop PDF here</p>
                  <p className="dz-sub">or click to browse</p>
                </>
              )}
            </div>

            <button className="upload-btn" onClick={upload} disabled={!file || uploading}>
              {uploading
                ? <><span className="spin"/>Indexing vectors…</>
                : <><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" width="14" height="14"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>Upload & Index</>
              }
            </button>

            {currentFile && (
              <div className="active-doc">
                <div className="active-dot"/>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="12" height="12"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                <span>{currentFile.length > 22 ? currentFile.slice(0,22)+"…" : currentFile}</span>
              </div>
            )}
          </div>

          <div className="side-bot">
            <button className="clear-btn" onClick={() => { setMessages([]); setCurrentFile(""); setFile(null); }}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="13" height="13"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"/></svg>
              Clear session
            </button>
          </div>
        </aside>

        {/* ── MAIN ── */}
        <main className="main">

          {/* Topbar */}
          <header className="topbar">
            <button className="toggle-btn" onClick={() => setSideOpen(s => !s)} title="Toggle sidebar">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
                <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
              </svg>
            </button>
            <div className="topbar-info">
              <div className={`pulse ${currentFile ? "pulse-on" : ""}`}/>
              <span className="topbar-file">{currentFile || "No document loaded"}</span>
            </div>
            <div className="topbar-right">
              <span className="pill">{qCount} Q&A</span>
              <span className="pill pill-model">open-mistral-nemo</span>
            </div>
          </header>

          {/* Feed */}
          <div className="feed">
            {messages.length === 0 && (
              <div className="empty">
                <div className="empty-gfx">
                  <svg viewBox="0 0 80 80" fill="none" width="72" height="72">
                    <circle cx="40" cy="40" r="36" stroke="url(#eg)" strokeWidth="1"/>
                    <rect x="20" y="26" width="40" height="28" rx="6" fill="url(#eg)" opacity=".12"/>
                    <rect x="20" y="26" width="40" height="28" rx="6" stroke="url(#eg)" strokeWidth="1.2"/>
                    <line x1="28" y1="36" x2="52" y2="36" stroke="url(#eg)" strokeWidth="2" strokeLinecap="round"/>
                    <line x1="28" y1="42" x2="44" y2="42" stroke="url(#eg)" strokeWidth="2" strokeLinecap="round"/>
                    <circle cx="58" cy="22" r="10" fill="url(#eg2)"/>
                    <path d="M55 22l2 2 4-4" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <defs>
                      <linearGradient id="eg" x1="4" y1="4" x2="76" y2="76" gradientUnits="userSpaceOnUse"><stop stopColor="#8b5cf6"/><stop offset="1" stopColor="#3b82f6"/></linearGradient>
                      <linearGradient id="eg2" x1="48" y1="12" x2="68" y2="32" gradientUnits="userSpaceOnUse"><stop stopColor="#8b5cf6"/><stop offset="1" stopColor="#3b82f6"/></linearGradient>
                    </defs>
                  </svg>
                </div>
                <h2 className="empty-h">Ask your document anything</h2>
                <p className="empty-p">Upload a PDF from the sidebar. RAGmind uses vector search to find precise answers — it will never hallucinate outside your document.</p>
                <div className="hint-row">
                  {["What is the main topic?", "Summarize key points", "Explain the first concept", "List all examples"].map((h,i) => (
                    <button key={i} className="hint" onClick={() => currentFile && setQuery(h)}>{h}</button>
                  ))}
                </div>

                {/* How it works strip */}
                <div className="how-strip">
                  {[
                    { icon: "📄", step: "1. Upload", desc: "Drop any PDF" },
                    { icon: "🔍", step: "2. Index", desc: "Vectors created" },
                    { icon: "💬", step: "3. Ask", desc: "Get precise answers" },
                  ].map((s,i) => (
                    <div key={i} className="how-card">
                      <span className="how-icon">{s.icon}</span>
                      <span className="how-step">{s.step}</span>
                      <span className="how-desc">{s.desc}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {messages.map((m, i) => <Msg key={i} m={m} />)}
            {loading && <TypingDots />}
            <div ref={bottomRef}/>
          </div>

          {/* Input */}
          <div className="input-zone">
            <div className={`input-shell ${!currentFile ? "input-off" : ""}`}>
              <div className="input-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" width="16" height="16">
                  <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
              </div>
              <input
                className="input-field"
                value={query}
                onChange={e => setQuery(e.target.value)}
                onKeyDown={e => e.key === "Enter" && !e.shiftKey && send()}
                placeholder={currentFile ? "Ask anything about your document…" : "Upload a PDF to start chatting…"}
                disabled={!currentFile || loading}
              />
              <button className="send" onClick={send} disabled={!currentFile || loading || !query.trim()}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" width="16" height="16">
                  <line x1="22" y1="2" x2="11" y2="13"/>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                </svg>
              </button>
            </div>
            <p className="input-note">RAGmind answers only from your uploaded document · Powered by Mistral + Pinecone</p>
          </div>
        </main>
      </div>
    </div>
  );
}
