import React from "react";

/* ── SVG icon primitives ─────────────────────────────────────── */
const Icon = {
  dashboard: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
      <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
    </svg>
  ),
  mic: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
      <path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/>
      <line x1="8" y1="23" x2="16" y2="23"/>
    </svg>
  ),
  upload: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
    </svg>
  ),
  history: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15 15"/>
    </svg>
  ),
  chat: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      <circle cx="9" cy="11" r="1" fill="currentColor" stroke="none"/>
      <circle cx="12" cy="11" r="1" fill="currentColor" stroke="none"/>
      <circle cx="15" cy="11" r="1" fill="currentColor" stroke="none"/>
    </svg>
  ),
  logoMark: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" fill="white" stroke="white"/>
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" stroke="rgba(255,255,255,0.75)"/>
    </svg>
  ),
};

const NAV_ITEMS = [
  { section: "MAIN" },
  { id: "dashboard", label: "Dashboard",       icon: Icon.dashboard },
  { section: "RECORD" },
  { id: "mic",       label: "Live Meeting",    icon: Icon.mic },
  { id: "file",      label: "Upload File",     icon: Icon.upload },
  { section: "EXPLORE" },
  { id: "history",   label: "Meeting History", icon: Icon.history },
  { id: "chat",      label: "Ask Memory",      icon: Icon.chat },
];

const Sidebar = ({ activeTab, setActiveTab }) => (
  <aside className="sidebar">
    {/* Branding */}
    <div className="sidebar-header">
      <div className="logo-icon">{Icon.logoMark}</div>
      <div className="logo-text">
        <strong>Meeting Assistant</strong>
        <span>AI-powered · Local</span>
      </div>
    </div>

    {/* Nav */}
    <nav className="sidebar-nav">
      {NAV_ITEMS.map((item, idx) =>
        item.section ? (
          <div key={idx} className="nav-section-label">{item.section}</div>
        ) : (
          <button
            key={item.id}
            className={`nav-item ${activeTab === item.id ? "active" : ""}`}
            onClick={() => setActiveTab(item.id)}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </button>
        )
      )}
    </nav>

    {/* User footer */}
    <div className="sidebar-footer">
      <div className="user-profile">
        <div className="avatar">U</div>
        <div className="user-info">
          <div className="user-name">Local User</div>
          <div className="user-status">
            <span className="status-dot" />
            AI Active
          </div>
        </div>
      </div>
    </div>
  </aside>
);

export default Sidebar;
