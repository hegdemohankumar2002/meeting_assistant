import React, { useState } from "react";
import Sidebar from "./components/Sidebar";
import ChatTab from "./components/ChatTab";
import MeetingTab from "./components/MeetingTab";

function App() {
  const [activeTab, setActiveTab] = useState("mic"); // 'mic' | 'file' | 'chat'

  const renderContent = () => {
    switch (activeTab) {
      case 'chat':
        return (
          <>
            <header className="page-header">
              <h1 className="page-title">Memory Chat</h1>
              <p className="page-subtitle">Interact with the knowledge base from your past meetings.</p>
            </header>
            <ChatTab />
          </>
        );
      case 'file':
        return (
          <>
            <header className="page-header">
              <h1 className="page-title">Upload Recording</h1>
              <p className="page-subtitle">Process audio files to extract insights and summaries.</p>
            </header>
            <MeetingTab mode="file" />
          </>
        );
      case 'mic':
      default:
        return (
          <>
            <header className="page-header">
              <h1 className="page-title">Live Meeting</h1>
              <p className="page-subtitle">Real-time transcription and analysis.</p>
            </header>
            <MeetingTab mode="mic" />
          </>
        );
    }
  };

  return (
    <div className="app-root">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main className="app-main">
        {renderContent()}
      </main>
    </div>
  );
}

export default App;
