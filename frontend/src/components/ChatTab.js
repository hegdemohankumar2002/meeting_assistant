import React, { useState, useRef, useEffect } from "react";

const API = "http://localhost:8000";

const SUGGESTIONS = [
    "What decisions were made in the last meeting?",
    "List all action items from recent meetings.",
    "Who has open action items?",
    "What was the main agenda last time?",
    "Were there any conflicts or disagreements?",
];

/** Convert markdown text to React elements */
function parseMarkdown(text) {
    if (!text) return null;
    const lines = text.split("\n");
    const out = [];
    let listBuf = [];

    const flushList = () => {
        if (listBuf.length) {
            out.push(<ul key={`ul-${out.length}`}>{listBuf.map((t, i) => <li key={i}>{t}</li>)}</ul>);
            listBuf = [];
        }
    };

    lines.forEach((line, i) => {
        if (line.startsWith("### ")) { flushList(); out.push(<h3 key={i}>{line.slice(4)}</h3>); }
        else if (line.startsWith("## ")) { flushList(); out.push(<h2 key={i}>{line.slice(3)}</h2>); }
        else if (line.startsWith("# "))  { flushList(); out.push(<h1 key={i}>{line.slice(2)}</h1>); }
        else if (line.match(/^[-*] /))   { listBuf.push(line.slice(2)); }
        else if (!line.trim()) { flushList(); if (out.length) out.push(<br key={i} />); }
        else {
            flushList();
            const html = line.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
            out.push(<p key={i} dangerouslySetInnerHTML={{ __html: html }} />);
        }
    });
    flushList();
    return out;
}

/** SVG send icon */
const SendIcon = () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="22" y1="2" x2="11" y2="13" />
        <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
);

/** SVG brain icon for empty state */
const BrainIcon = () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ width: 32, height: 32, color: "#2563eb" }}>
        <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.44-5.18A2.5 2.5 0 0 1 9.5 2Z"/>
        <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.44-5.18A2.5 2.5 0 0 0 14.5 2Z"/>
    </svg>
);

const ChatTab = () => {
    const [query, setQuery] = useState("");
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(false);
    const endRef = useRef(null);

    useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [history, loading]);

    const submit = async (q) => {
        const text = (q || query).trim();
        if (!text) return;
        setHistory(h => [...h, { role: "user", content: text }]);
        setQuery("");
        setLoading(true);
        try {
            const res = await fetch(`${API}/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: text }),
            });
            const data = await res.json();
            setHistory(h => [...h, { role: "ai", content: data.response || "I couldn't find an answer." }]);
        } catch (err) {
            setHistory(h => [...h, { role: "ai", content: `⚠ Error: ${err.message}` }]);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = (e) => { e.preventDefault(); submit(); };

    return (
        <div className="chat-container">
            {/* Messages */}
            <div className="chat-messages">
                {history.length === 0 && (
                    <div className="chat-empty-state">
                        <div className="chat-empty-icon"><BrainIcon /></div>
                        <h3>Meeting Memory</h3>
                        <p>Ask anything about your past meetings — decisions, action items, summaries, and more.</p>
                        <div className="chat-suggestions" style={{ marginTop: 20 }}>
                            {SUGGESTIONS.map((s, i) => (
                                <button key={i} className="suggestion-chip" onClick={() => submit(s)}>{s}</button>
                            ))}
                        </div>
                    </div>
                )}

                {history.map((msg, i) => (
                    <div key={i} className={`message-row ${msg.role}`}>
                        <div className={`msg-avatar ${msg.role === "ai" ? "ai-avatar" : "user-avatar"}`}>
                            {msg.role === "ai" ? "AI" : "U"}
                        </div>
                        <div className={`message ${msg.role}`}>
                            {msg.role === "ai" ? (
                                <div className="markdown-body">{parseMarkdown(msg.content)}</div>
                            ) : (
                                <span>{msg.content}</span>
                            )}
                        </div>
                    </div>
                ))}

                {loading && (
                    <div className="message-row ai">
                        <div className="msg-avatar ai-avatar">AI</div>
                        <div className="message ai">
                            <div className="typing-dots"><span /><span /><span /></div>
                        </div>
                    </div>
                )}
                <div ref={endRef} />
            </div>

            {/* Input */}
            <form className="chat-input-area" onSubmit={handleSubmit}>
                <input
                    className="chat-input"
                    type="text"
                    value={query}
                    onChange={e => setQuery(e.target.value)}
                    placeholder="Ask about past meetings…"
                    disabled={loading}
                />
                <button className="chat-send-btn" type="submit" disabled={loading || !query.trim()}>
                    <SendIcon />
                </button>
            </form>
        </div>
    );
};

export default ChatTab;
