import React, { useState, useEffect } from "react";

const API = "http://localhost:8000";

function formatDuration(seconds) {
    if (!seconds) return "";
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

function formatDate(iso) {
    if (!iso) return "—";
    return new Date(iso).toLocaleDateString("en-US", {
        month: "short", day: "numeric", year: "numeric"
    });
}

const STAT_CARDS = (stats) => [
    { icon: "🗂", label: "Total Meetings",   value: stats?.total_meetings ?? 0,         cls: "purple" },
    { icon: "⏱", label: "Hours Processed",  value: `${stats?.total_hours_processed ?? 0}h`, cls: "cyan"   },
    { icon: "✅", label: "Action Items",     value: stats?.total_action_items ?? 0,     cls: "green"  },
    { icon: "⚡", label: "Decisions Made",   value: stats?.total_decisions ?? 0,        cls: "amber"  },
];

const Dashboard = ({ setActiveTab }) => {
    const [stats, setStats] = useState(null);
    const [recent, setRecent] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.all([
            fetch(`${API}/stats`).then(r => r.json()),
            fetch(`${API}/meetings/`).then(r => r.json()),
        ])
            .then(([s, m]) => { setStats(s); setRecent(m.slice(0, 5)); })
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    return (
        <div className="section-enter">
            {/* Stats */}
            <div className="stats-grid stagger">
                {STAT_CARDS(stats).map((s) => (
                    <div key={s.label} className={`stat-card ${s.cls}`}>
                        <div className={`stat-icon-wrap ${s.cls}`}>{s.icon}</div>
                        <div className="stat-value">{loading ? "—" : s.value}</div>
                        <div className="stat-label">{s.label}</div>
                    </div>
                ))}
            </div>

            {/* Quick Actions */}
            <div className="card">
                <div className="card-header">
                    <div className="card-title">Quick Actions</div>
                </div>
                <div className="quick-actions">
                    <button className="primary-btn" onClick={() => setActiveTab("mic")}>
                        🎙&nbsp; Start Live Meeting
                    </button>
                    <button className="secondary-btn" onClick={() => setActiveTab("file")}>
                        ↑&nbsp; Upload Recording
                    </button>
                    <button className="secondary-btn" onClick={() => setActiveTab("history")}>
                        ◷&nbsp; Browse History
                    </button>
                    <button className="secondary-btn" onClick={() => setActiveTab("chat")}>
                        ◈&nbsp; Ask Memory
                    </button>
                </div>
            </div>

            {/* Recent Meetings */}
            <div className="card">
                <div className="card-header">
                    <div className="card-title">Recent Meetings</div>
                    <button
                        className="secondary-btn"
                        style={{ fontSize: "0.8rem", padding: "5px 12px" }}
                        onClick={() => setActiveTab("history")}
                    >
                        View All →
                    </button>
                </div>

                {loading ? (
                    <div className="page-spinner"><div className="ring-spinner" /></div>
                ) : recent.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-icon">🗂</div>
                        <h3>No meetings yet</h3>
                        <p>Start a live meeting or upload a recording to get insights.</p>
                    </div>
                ) : (
                    <div className="meeting-list stagger">
                        {recent.map((m, i) => (
                            <div
                                key={m.id}
                                className="meeting-list-item"
                                style={{ animationDelay: `${i * 0.05}s` }}
                                onClick={() => setActiveTab("history")}
                            >
                                <div className="meeting-item-icon">📋</div>
                                <div className="meeting-item-body">
                                    <div className="meeting-item-title">{m.title || "Untitled Meeting"}</div>
                                    <div className="meeting-item-meta">
                                        <span>{formatDate(m.created_at)}</span>
                                        {m.duration_seconds > 0 && <span>{formatDuration(m.duration_seconds)}</span>}
                                    </div>
                                    {(m.summary_preview || m.inferred_agenda) && (
                                        <div className="meeting-item-preview">
                                            {m.summary_preview || m.inferred_agenda}
                                        </div>
                                    )}
                                </div>
                                <span className="badge badge-purple" style={{ flexShrink: 0 }}>#{m.id}</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default Dashboard;
