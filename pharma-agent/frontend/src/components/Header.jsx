import React from 'react';
import { useTranslation } from 'react-i18next';
import { Heart, Check, User, PanelRightOpen, PanelRightClose } from 'lucide-react';

/**
 * Header - Top Status Bar
 */
function Header({
    adminMode,
    setAdminMode,
    safetyPanelOpen,
    setSafetyPanelOpen
}) {
    const { t } = useTranslation();

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
                    {t('status.verified')}
                </div>
            </div>

            <div className="header-center">
                <div className="status-indicator">
                    <span className="status-dot green"></span>
                    {t('status.ai_core')}
                </div>
                <div className="status-indicator">
                    <span className="status-dot green"></span>
                    {t('status.database')}
                </div>
                <div className="status-indicator">
                    <span className="status-dot green"></span>
                    {t('status.secure')}
                </div>
            </div>

            <div className="header-right">

                <div className="mode-toggle">
                    {t('settings.admin_mode')}
                    <div
                        className={`toggle-switch ${adminMode ? 'active' : ''}`}
                        onClick={() => {
                            const newState = !adminMode;
                            setAdminMode(newState);
                            // Log admin toggle
                            const apiBase = import.meta.env.VITE_API_URL || 'https://pharmaagent.onrender.com';
                            fetch(`${apiBase}/admin/toggle-log`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ enabled: newState })
                            }).catch(() => { });
                        }}
                        role="switch"
                        aria-checked={adminMode}
                        tabIndex={0}
                    >
                        <span className="toggle-knob"></span>
                    </div>
                    {adminMode && (
                        <span className="admin-badge">{t('common.admin_active') || 'Admin Active'}</span>
                    )}
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
                </div>
            </div>
        </header>
    );
}

export default Header;
