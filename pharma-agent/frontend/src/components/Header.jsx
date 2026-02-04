import React from 'react';
import { Heart, Check, User, PanelRightOpen, PanelRightClose } from 'lucide-react';

/**
 * Header - Top Status Bar
 */
function Header({
    adminMode,
    setAdminMode,
    elderlyMode,
    setElderlyMode,
    safetyPanelOpen,
    setSafetyPanelOpen
}) {
    return (
        <header className="app-header">
            <div className="header-left">
                <div className="logo">
                    <div className="logo-icon">
                        <Heart size={20} color="white" />
                    </div>
                    <span className="logo-text">
                        PharmaAgent
                        <span className="logo-pro">Pro</span>
                    </span>
                </div>
                <div className="verified-badge">
                    <Check size={12} />
                    Verified
                </div>
            </div>

            <div className="header-center">
                <div className="status-indicator">
                    <span className="status-dot green"></span>
                    AI Core
                </div>
                <div className="status-indicator">
                    <span className="status-dot green"></span>
                    Database
                </div>
                <div className="status-indicator">
                    <span className="status-dot green"></span>
                    Secure Link
                </div>
            </div>

            <div className="header-right">
                <div className="mode-toggle">
                    Admin Mode
                    <div
                        className={`toggle-switch ${adminMode ? 'active' : ''}`}
                        onClick={() => setAdminMode(!adminMode)}
                        role="switch"
                        aria-checked={adminMode}
                        tabIndex={0}
                    />
                </div>
                <div className="mode-toggle">
                    Elderly Mode
                    <div
                        className={`toggle-switch ${elderlyMode ? 'active' : ''}`}
                        onClick={() => setElderlyMode(!elderlyMode)}
                        role="switch"
                        aria-checked={elderlyMode}
                        tabIndex={0}
                    />
                </div>

                {/* Safety Panel Toggle */}
                <button
                    className="panel-toggle-btn"
                    onClick={() => setSafetyPanelOpen(!safetyPanelOpen)}
                    title={safetyPanelOpen ? 'Hide Safety Dashboard' : 'Show Safety Dashboard'}
                    aria-label={safetyPanelOpen ? 'Hide Safety Dashboard' : 'Show Safety Dashboard'}
                >
                    {safetyPanelOpen ? <PanelRightClose size={18} /> : <PanelRightOpen size={18} />}
                </button>

                <div className="user-profile">
                    <div className="user-avatar">
                        <User size={16} color="white" />
                    </div>
                    <div className="user-info">
                        <div className="user-name">Dr. A. Sharma</div>
                        <div className="user-role">Pharmacist</div>
                    </div>
                </div>
            </div>
        </header>
    );
}

export default Header;
