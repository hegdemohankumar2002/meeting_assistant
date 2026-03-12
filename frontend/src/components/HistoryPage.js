import React, { useState, useEffect, useCallback } from "react";

const API = "http://localhost:8000";

function formatDuration(s) {
    if (!s) return "";
    const m = Math.floor(s / 60);
    return m > 0 ? `${m}m ${s % 60}s` : `${s}s`;
}

function formatDate(iso) {
    if (!iso) return "—";
    return new Date(iso).toLocaleString("en-US", {
        month: "short", day: "numeric", year: "numeric",
        hour: "2-digit", minute: "2-digit",
    });
}

function renderMarkdown(text) {
    if (!text) return null;
    return text.split("\n").map((line, i) => {
        if (line.startsWith("# "))  return <h1 key={i}>{line.slice(2)}</h1>;
        if (line.startsWith("## ")) return <h2 key={i}>{line.slice(3)}</h2>;
        if (line.startsWith("### "))return <h3 key={i}>{line.slice(4)}</h3>;
        if (line.match(/^[-*] /))   return <li key={i}>{line.slice(2)}</li>;
        if (!line.trim())            return <br key={i} />;
        return <p key={i}>{line}</p>;
    });
}

function renderItem(item) {
    if (typeof item === "string") return item;
    if (typeof item === "object" && item !== null) {
        if (item.Owner && item.Verb && item.Task) return `${item.Owner} to ${item.Verb} ${item.Task}`;
        return Object.values(item).filter(Boolean).join(" — ");
    }
    return String(item);
}

const TABS = ["Summary", "Transcript", "Speakers", "Roadmap", "Insights"];

/* ── Meeting detail pane ─────────────────────────────────────── */
const MeetingDetail = ({ meeting, onClose }) => {
    const [tab, setTab] = useState("Summary");
    const [exporting, setExporting] = useState(false);

    const exportMeeting = async (fmt) => {
        setExporting(true);
        try {
            const res   = await fetch(`${API}/meetings/${meeting.id}/export?fmt=${fmt}`);
            const blob  = await res.blob();
            const url   = URL.createObjectURL(blob);
            const a     = document.createElement("a");
            a.href = url; a.download = `meeting_${meeting.id}.${fmt === "json" ? "json" : "md"}`;
            a.click(); URL.revokeObjectURL(url);
        } catch (e) { alert("Export failed: " + e.message); }
        finally    { setExporting(false); }
    };

    const { decisions=[], agreements=[], conflicts=[] } = meeting.insights || {};

    return (
        <div className="card section-enter" style={{ marginTop: 4 }}>
            {/* Header */}
            <div className="flex-between" style={{ marginBottom: 16 }}>
                <div style={{ minWidth: 0, flex: 1 }}>
                    <h2 style={{ fontSize: "1.05rem", fontWeight: 800, color: "var(--text-1)", marginBottom: 4, letterSpacing: "-0.02em" }}>
                        {meeting.title || "Untitled Meeting"}
                    </h2>
                    <div style={{ display: "flex", gap: 12, fontSize: "0.78rem", color: "var(--text-3)", flexWrap: "wrap" }}>
                        <span>📅 {formatDate(meeting.created_at)}</span>
                        {meeting.duration_seconds > 0 && <span>⏱ {formatDuration(meeting.duration_seconds)}</span>}
                        {meeting.inferred_agenda && (
                            <span className="badge badge-blue">🎯 {meeting.inferred_agenda}</span>
                        )}
                    </div>
                </div>
                <div style={{ display: "flex", gap: 8, flexShrink: 0, marginLeft: 12 }}>
                    <button className="secondary-btn" style={{ fontSize: "0.78rem", padding: "5px 10px" }} onClick={() => exportMeeting("markdown")} disabled={exporting}>⬇ MD</button>
                    <button className="secondary-btn" style={{ fontSize: "0.78rem", padding: "5px 10px" }} onClick={() => exportMeeting("json")} disabled={exporting}>⬇ JSON</button>
                    <button className="icon-btn" onClick={onClose}>✕</button>
                </div>
            </div>

            {/* Tabs */}
            <div className="tabs-header">
                {TABS.map(t => (
                    <button key={t} className={`tab-btn ${tab === t ? "active" : ""}`} onClick={() => setTab(t)}>{t}</button>
                ))}
            </div>

            <div className="tab-content">
                {/* Summary */}
                {tab === "Summary" && (
                    <div>
                        <div className="card" style={{ marginBottom: 14 }}>
                            <div className="result-card-header"><div className="result-title">📝 Executive Brief</div></div>
                            <p style={{ color: "var(--text-2)", lineHeight: 1.75, fontSize: "0.9rem" }}>{meeting.summary || "No summary available."}</p>
                        </div>
                        <div className="results-grid">
                            <div className="card">
                                <div className="result-card-header"><div className="result-title">🔑 Key Points</div></div>
                                <ul className="result-list">{(meeting.key_points || []).map((k, i) => <li key={i}>{renderItem(k)}</li>)}</ul>
                            </div>
                            <div className="card">
                                <div className="result-card-header"><div className="result-title" style={{ color: "var(--amber)" }}>⚡ Action Items</div></div>
                                <ul className="result-list">{(meeting.action_items || []).map((a, i) => <li key={i}>{renderItem(a)}</li>)}</ul>
                            </div>
                            {(meeting.role_summaries?.executive || meeting.role_summaries?.technical) && (<>
                                <div className="card">
                                    <div className="result-card-header"><div className="result-title">👔 Executive View</div></div>
                                    <p style={{ fontSize: "0.875rem", color: "var(--text-2)" }}>{meeting.role_summaries.executive}</p>
                                </div>
                                <div className="card">
                                    <div className="result-card-header"><div className="result-title">🔧 Technical View</div></div>
                                    <p style={{ fontSize: "0.875rem", color: "var(--text-2)" }}>{meeting.role_summaries.technical}</p>
                                </div>
                            </>)}
                        </div>
                    </div>
                )}

                {/* Transcript */}
                {tab === "Transcript" && (
                    <div className="card" style={{ maxHeight: 480, overflowY: "auto", padding: "4px 0" }}>
                        {(meeting.segments || []).length > 0 ? meeting.segments.map((seg, i) => {
                            const sp = (meeting.speakers || []).find(s => s.id === seg.speaker_id);
                            const color = sp?.color || "#6366f1";
                            return (
                                <div key={i} className="segment-item">
                                    <div className="segment-speaker-dot" style={{ background: color }}>{(sp?.label || "?")[0]}</div>
                                    <div className="segment-body">
                                        <div className="segment-header">
                                            <span className="segment-speaker-name" style={{ color }}>{sp?.label || seg.speaker_id || "Unknown"}</span>
                                            <span className="segment-time">{seg.start?.toFixed ? `${seg.start.toFixed(1)}s` : ""}</span>
                                        </div>
                                        <div className="segment-text">{seg.text}</div>
                                    </div>
                                </div>
                            );
                        }) : (
                            <pre style={{ padding: "1rem", color: "var(--text-2)", fontSize: "0.85rem", whiteSpace: "pre-wrap", lineHeight: 1.7 }}>{meeting.transcript || "No transcript available."}</pre>
                        )}
                    </div>
                )}

                {/* Speakers */}
                {tab === "Speakers" && (
                    (meeting.speakers || []).length > 0 ? (
                        <div className="speakers-grid">
                            {meeting.speakers.map((s, i) => (
                                <div key={i} className="speaker-chip">
                                    <div className="speaker-color-dot" style={{ background: s.color }} />
                                    <span>{s.label}</span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="empty-state"><div className="empty-icon">👥</div><h3>No speaker data</h3><p>Diarization may not have run.</p></div>
                    )
                )}

                {/* Roadmap */}
                {tab === "Roadmap" && (
                    <div className="card markdown-body" style={{ maxHeight: 480, overflowY: "auto" }}>
                        {meeting.roadmap ? renderMarkdown(meeting.roadmap) : (
                            <div className="empty-state"><div className="empty-icon">🗺</div><h3>No roadmap generated</h3></div>
                        )}
                    </div>
                )}

                {/* Insights */}
                {tab === "Insights" && (
                    <div className="results-grid">
                        <div className="card">
                            <div className="result-card-header"><div className="result-title" style={{ color: "var(--green)" }}>✅ Decisions</div></div>
                            {decisions.length > 0 ? <ul className="result-list">{decisions.map((d,i) => <li key={i}>{renderItem(d)}</li>)}</ul> : <p style={{ color: "var(--text-4)", fontSize: "0.85rem" }}>None extracted.</p>}
                        </div>
                        <div className="card">
                            <div className="result-card-header"><div className="result-title" style={{ color: "var(--sky)" }}>🤝 Agreements</div></div>
                            {agreements.length > 0 ? <ul className="result-list">{agreements.map((a,i) => <li key={i}>{renderItem(a)}</li>)}</ul> : <p style={{ color: "var(--text-4)", fontSize: "0.85rem" }}>None extracted.</p>}
                        </div>
                        <div className="card">
                            <div className="result-card-header"><div className="result-title" style={{ color: "var(--red)" }}>⚠ Conflicts</div></div>
                            {conflicts.length > 0 ? <ul className="result-list">{conflicts.map((c,i) => <li key={i}>{renderItem(c)}</li>)}</ul> : <p style={{ color: "var(--text-4)", fontSize: "0.85rem" }}>None detected.</p>}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

/* ── HistoryPage ─────────────────────────────────────────────── */
const HistoryPage = () => {
    const [meetings,       setMeetings]       = useState([]);
    const [loading,        setLoading]        = useState(true);
    const [searchQ,        setSearchQ]        = useState("");
    const [searching,      setSearching]      = useState(false);
    const [selectedMeeting,setSelectedMeeting]= useState(null);
    const [detailLoading,  setDetailLoading]  = useState(false);
    const [error,          setError]          = useState("");

    const fetchAll = useCallback(async () => {
        setLoading(true); setError("");
        try {
            const data = await fetch(`${API}/meetings/`).then(r => r.json());
            setMeetings(data);
        } catch { setError("Failed to load meetings. Is the backend running?"); }
        finally   { setLoading(false); }
    }, []);

    useEffect(() => { fetchAll(); }, [fetchAll]);

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!searchQ.trim()) { fetchAll(); return; }
        setSearching(true); setError("");
        try {
            const data = await fetch(`${API}/meetings/search?q=${encodeURIComponent(searchQ)}`).then(r => r.json());
            setMeetings(data);
        } catch { setError("Search failed."); }
        finally   { setSearching(false); }
    };

    const handleSelect = async (id) => {
        if (selectedMeeting?.id === id) { setSelectedMeeting(null); return; }
        setDetailLoading(true);
        try {
            const data = await fetch(`${API}/meetings/${id}`).then(r => r.json());
            setSelectedMeeting(data);
        } catch { setError("Failed to load meeting details."); }
        finally  { setDetailLoading(false); }
    };

    const handleDelete = async (e, id) => {
        e.stopPropagation();
        if (!window.confirm("Delete this meeting permanently?")) return;
        try {
            await fetch(`${API}/meetings/${id}`, { method: "DELETE" });
            setMeetings(p => p.filter(m => m.id !== id));
            if (selectedMeeting?.id === id) setSelectedMeeting(null);
        } catch { setError("Delete failed."); }
    };

    const handleExport = async (e, id, fmt) => {
        e.stopPropagation();
        const res  = await fetch(`${API}/meetings/${id}/export?fmt=${fmt}`);
        const blob = await res.blob();
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement("a");
        a.href = url; a.download = `meeting_${id}.${fmt === "json" ? "json" : "md"}`; a.click();
        URL.revokeObjectURL(url);
    };

    return (
        <div className="section-enter">
            {/* Search */}
            <div className="search-bar">
                <div className="search-input-wrap">
                    <span className="search-input-icon">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                        </svg>
                    </span>
                    <input
                        className="search-input"
                        placeholder="Search transcripts, summaries, titles…"
                        value={searchQ}
                        onChange={e => setSearchQ(e.target.value)}
                        onKeyDown={e => e.key === "Enter" && handleSearch(e)}
                    />
                </div>
                <button className="primary-btn" onClick={handleSearch} disabled={searching}>
                    {searching ? "Searching…" : "Search"}
                </button>
                {searchQ && (
                    <button className="secondary-btn" onClick={() => { setSearchQ(""); fetchAll(); }}>Clear</button>
                )}
            </div>

            {error && <div className="alert alert-error">⚠ {error}</div>}

            {/* Meeting list */}
            {loading ? (
                <div className="page-spinner"><div className="ring-spinner" /></div>
            ) : meetings.length === 0 ? (
                <div className="empty-state">
                    <div className="empty-icon">🗂</div>
                    <h3>No meetings found</h3>
                    <p>{searchQ ? "Try a different search term." : "Process a meeting to see it here."}</p>
                </div>
            ) : (
                <div className="meeting-list stagger" style={{ marginBottom: 20 }}>
                    {meetings.map((m, i) => (
                        <div
                            key={m.id}
                            className={`meeting-list-item ${selectedMeeting?.id === m.id ? "selected" : ""}`}
                            style={{ animationDelay: `${i * 0.04}s` }}
                            onClick={() => handleSelect(m.id)}
                        >
                            <div className="meeting-item-icon">📋</div>
                            <div className="meeting-item-body">
                                <div className="meeting-item-title">{m.title || "Untitled Meeting"}</div>
                                <div className="meeting-item-meta">
                                    <span>📅 {new Date(m.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}</span>
                                    {m.duration_seconds > 0 && <span>⏱ {formatDuration(m.duration_seconds)}</span>}
                                    {m.inferred_agenda && <span className="truncate" style={{ maxWidth: 180 }}>🎯 {m.inferred_agenda}</span>}
                                </div>
                                {m.summary_preview && <div className="meeting-item-preview">{m.summary_preview}</div>}
                            </div>
                            <div className="meeting-item-actions">
                                <button className="icon-btn" title="Export Markdown" onClick={e => handleExport(e, m.id, "markdown")}>⬇</button>
                                <button className="icon-btn danger" title="Delete" onClick={e => handleDelete(e, m.id)}>🗑</button>
                            </div>
                            <span className="badge badge-purple" style={{ flexShrink: 0 }}>#{m.id}</span>
                        </div>
                    ))}
                </div>
            )}

            {/* Detail panel */}
            {detailLoading && <div className="page-spinner"><div className="ring-spinner" /></div>}
            {selectedMeeting && !detailLoading && (
                <MeetingDetail meeting={selectedMeeting} onClose={() => setSelectedMeeting(null)} />
            )}
        </div>
    );
};

export default HistoryPage;
