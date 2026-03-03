import React, { useState, useRef, useEffect } from "react";

const ChatTab = () => {
    const [chatQuery, setChatQuery] = useState("");
    const [chatHistory, setChatHistory] = useState([]);
    const [isChatLoading, setIsChatLoading] = useState(false);
    const chatEndRef = useRef(null);

    const API_BASE = "http://127.0.0.1:8000";

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [chatHistory]);

    const handleChatSubmit = async (e) => {
        e.preventDefault();
        if (!chatQuery.trim()) return;

        const userMsg = { role: 'user', content: chatQuery };
        setChatHistory(prev => [...prev, userMsg]);
        setChatQuery("");
        setIsChatLoading(true);

        try {
            const res = await fetch(`${API_BASE}/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: userMsg.content })
            });
            const data = await res.json();
            const aiMsg = { role: 'ai', content: data.response || "I couldn't find an answer." };
            setChatHistory(prev => [...prev, aiMsg]);
        } catch (err) {
            setChatHistory(prev => [...prev, { role: 'ai', content: "Error: " + err.message }]);
        } finally {
            setIsChatLoading(false);
        }
    };

    return (
        <div className="chat-container">
            <div className="chat-messages">
                {chatHistory.length === 0 && (
                    <div style={{ textAlign: 'center', marginTop: '20vh', color: 'var(--text-muted)' }}>
                        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🧠</div>
                        <h3>Ask your Meeting Memory</h3>
                        <p>Query past discussions, decisions, and action items.</p>
                    </div>
                )}
                {chatHistory.map((msg, i) => (
                    <div key={i} className={`message ${msg.role}`}>
                        <strong>{msg.role === 'ai' ? '🤖 AI' : '👤 You'}</strong>
                        <p style={{ marginTop: '0.4rem', margin: 0 }}>{msg.content}</p>
                    </div>
                ))}
                {isChatLoading && (
                    <div className="message ai" style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        <span>Thinking...</span>
                    </div>
                )}
                <div ref={chatEndRef} />
            </div>
            <form onSubmit={handleChatSubmit} className="chat-input-area">
                <input
                    className="chat-input"
                    type="text"
                    value={chatQuery}
                    onChange={(e) => setChatQuery(e.target.value)}
                    placeholder="Ex: What was discussed about the Q3 roadmap?"
                />
                <button type="submit" className="primary-btn">
                    Send
                </button>
            </form>
        </div>
    );
};

export default ChatTab;
