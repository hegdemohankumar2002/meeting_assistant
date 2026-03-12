import React, { useState } from "react";
import Sidebar from "./components/Sidebar";
import ChatTab from "./components/ChatTab";
import MeetingTab from "./components/MeetingTab";
import Dashboard from "./components/Dashboard";
import HistoryPage from "./components/HistoryPage";

const PAGE_CONFIG = {
  dashboard: { title: "Dashboard",        subtitle: "AI meeting analytics overview" },
  mic:       { title: "Live Meeting",      subtitle: "Record and analyze in real-time" },
  file:      { title: "Upload Recording", subtitle: "Process an existing audio file" },
  history:   { title: "Meeting History",  subtitle: "Browse and revisit past analyses" },
  chat:      { title: "Ask Memory",       subtitle: "Query your meetings with natural language" },
};

function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const config = PAGE_CONFIG[activeTab] || PAGE_CONFIG.dashboard;

  const renderContent = () => {
    switch (activeTab) {
      case "dashboard": return <Dashboard setActiveTab={setActiveTab} />;
      case "chat":      return <ChatTab />;
      case "file":      return <MeetingTab mode="file" />;
      case "history":   return <HistoryPage />;
      case "mic":
      default:          return <MeetingTab mode="mic" />;
    }
  };

  return (
    <div className="app-root">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main className="app-main">
        {/* Top navigation bar */}
        <div className="page-topbar">
          <div className="page-breadcrumb">
            <h1 className="page-title">{config.title}</h1>
            <span className="page-subtitle">{config.subtitle}</span>
          </div>
          <div className="topbar-actions">
            <span className="badge badge-green" style={{ fontSize: "0.72rem", padding: "4px 10px" }}>
              ● Backend Connected
            </span>
          </div>
        </div>

        {/* Main scrollable content */}
        <div className="page-content section-enter">
          {renderContent()}
        </div>
      </main>
    </div>
  );
}

export default App;
