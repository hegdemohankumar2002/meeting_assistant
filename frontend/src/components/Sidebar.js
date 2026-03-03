import React from 'react';

const Sidebar = ({ activeTab, setActiveTab }) => {
    const menuItems = [
        { id: 'mic', label: 'Live Meeting', icon: '🎙️' },
        { id: 'file', label: 'Upload File', icon: '📁' },
        { id: 'chat', label: 'Ask Memory', icon: '🧠' },
    ];

    return (
        <aside className="sidebar">
            <div className="sidebar-header">
                <div className="logo-icon">M</div>
                <h2>Meeting<br />Assistant</h2>
            </div>

            <nav className="sidebar-nav">
                {menuItems.map((item) => (
                    <button
                        key={item.id}
                        className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
                        onClick={() => setActiveTab(item.id)}
                    >
                        <span className="nav-icon">{item.icon}</span>
                        <span className="nav-label">{item.label}</span>
                        {activeTab === item.id && <div className="active-indicator" />}
                    </button>
                ))}
            </nav>

            <div className="sidebar-footer">
                <div className="user-profile">
                    <div className="avatar">U</div>
                    <div className="user-info">
                        <span className="name">User</span>
                        <span className="status">Online</span>
                    </div>
                </div>
            </div>
        </aside>
    );
};

export default Sidebar;
