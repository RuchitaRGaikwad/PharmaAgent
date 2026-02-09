import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Bell, Globe, Zap, Lock, ChevronDown, RefreshCw, Check, AlertTriangle } from 'lucide-react';
import './settings.css';

const API_BASE = 'http://localhost:8000';
const USER_ID = 1; // Default user ID

function SettingsPage() {
    const { t, i18n } = useTranslation();

    // Settings state
    const [settings, setSettings] = useState({
        language: 'en',
        darkMode: true,
        notifications: true,
        emailAlerts: true,
        smsAlerts: false,
        autoRefill: true,
        voiceAssistant: true,
        dataSharing: false,
        adminMode: false
    });

    // UI state
    const [loading, setLoading] = useState(true);
    const [updating, setUpdating] = useState({});
    const [toast, setToast] = useState(null);
    const [expandedCards, setExpandedCards] = useState({
        notifications: true,
        appearance: true,
        features: true,
        privacy: false
    });

    // System status state
    const [systemStatus, setSystemStatus] = useState({
        ai_core: 'online',
        database: 'connected',
        security: 'secure',
        compliance_percent: 98,
        ai_confidence: 95,
        recent_checks: []
    });

    // Load settings on mount
    useEffect(() => {
        loadSettings();
        loadSystemStatus();

        // Poll system status every 10 seconds
        const interval = setInterval(loadSystemStatus, 10000);
        return () => clearInterval(interval);
    }, []);

    // Sync i18n language when settings load
    useEffect(() => {
        if (settings.language && settings.language !== i18n.language) {
            i18n.changeLanguage(settings.language);
        }
    }, [settings.language, i18n]);

    // Apply dark/light theme
    useEffect(() => {
        if (settings.darkMode) {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
        }
    }, [settings.darkMode]);

    const loadSettings = async () => {
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE}/settings/${USER_ID}`);
            if (response.ok) {
                const data = await response.json();
                setSettings(data.settings);
            }
        } catch (error) {
            console.error('Failed to load settings:', error);
            showToast(t('common.error'), 'error');
        } finally {
            setLoading(false);
        }
    };

    const loadSystemStatus = async () => {
        try {
            const response = await fetch(`${API_BASE}/settings/system/status`);
            if (response.ok) {
                const data = await response.json();
                setSystemStatus(data);
            }
        } catch (error) {
            console.error('Failed to load system status:', error);
        }
    };

    const updateSetting = async (key, value) => {
        // Optimistic update
        setSettings(prev => ({ ...prev, [key]: value }));
        setUpdating(prev => ({ ...prev, [key]: true }));

        try {
            const response = await fetch(
                `${API_BASE}/settings/${USER_ID}?key=${key}&value=${value}`,
                { method: 'PATCH' }
            );

            if (response.ok) {
                showToast(t('common.success'), 'success');
            } else {
                // Revert on failure
                setSettings(prev => ({ ...prev, [key]: !value }));
                showToast(t('common.error'), 'error');
            }
        } catch (error) {
            // Revert on failure
            setSettings(prev => ({ ...prev, [key]: !value }));
            showToast(t('common.error'), 'error');
        } finally {
            setUpdating(prev => ({ ...prev, [key]: false }));
        }
    };

    const updateLanguage = async (lang) => {
        const oldLang = settings.language;
        setSettings(prev => ({ ...prev, language: lang }));
        setUpdating(prev => ({ ...prev, language: true }));

        // Change app language immediately
        i18n.changeLanguage(lang);

        try {
            const response = await fetch(
                `${API_BASE}/settings/${USER_ID}?key=language&value=${lang}`,
                { method: 'PATCH' }
            );

            if (response.ok) {
                showToast(t('common.success'), 'success');
            } else {
                // Revert on failure
                setSettings(prev => ({ ...prev, language: oldLang }));
                i18n.changeLanguage(oldLang);
                showToast(t('common.error'), 'error');
            }
        } catch (error) {
            // Revert on failure
            setSettings(prev => ({ ...prev, language: oldLang }));
            i18n.changeLanguage(oldLang);
            showToast(t('common.error'), 'error');
        } finally {
            setUpdating(prev => ({ ...prev, language: false }));
        }
    };

    const showToast = (message, type) => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 3000);
    };

    const toggleCard = (card) => {
        setExpandedCards(prev => ({ ...prev, [card]: !prev[card] }));
    };

    if (loading) {
        return (
            <div className="settings-page">
                <div className="settings-loading">
                    <RefreshCw size={32} />
                    <p style={{ marginTop: '16px' }}>{t('common.loading')}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="settings-page">
            {/* Main Settings Column */}
            <div className="settings-main">
                <div className="settings-header">
                    <h1>⚙️ {t('settings.title')}</h1>
                    <p>{t('settings.subtitle')}</p>
                </div>

                {/* Notifications Card */}
                <div className="settings-card">
                    <div className="settings-card-header" onClick={() => toggleCard('notifications')}>
                        <div className="settings-card-header-left">
                            <div className="settings-card-icon notifications">
                                <Bell size={20} />
                            </div>
                            <h3 className="settings-card-title">{t('settings.notifications.title')}</h3>
                        </div>
                        <ChevronDown
                            size={20}
                            className={`settings-card-chevron ${expandedCards.notifications ? 'open' : ''}`}
                        />
                    </div>
                    <div className={`settings-card-content ${expandedCards.notifications ? 'open' : ''}`}>
                        <div className="settings-card-body">
                            <SettingItem
                                label={t('settings.notifications.push')}
                                description={t('settings.notifications.push_desc')}
                                value={settings.notifications}
                                loading={updating.notifications}
                                onChange={() => updateSetting('notifications', !settings.notifications)}
                            />
                            <SettingItem
                                label={t('settings.notifications.email')}
                                description={t('settings.notifications.email_desc')}
                                value={settings.emailAlerts}
                                loading={updating.emailAlerts}
                                onChange={() => updateSetting('emailAlerts', !settings.emailAlerts)}
                            />
                            <SettingItem
                                label={t('settings.notifications.sms')}
                                description={t('settings.notifications.sms_desc')}
                                value={settings.smsAlerts}
                                loading={updating.smsAlerts}
                                onChange={() => updateSetting('smsAlerts', !settings.smsAlerts)}
                            />
                        </div>
                    </div>
                </div>

                {/* Language & Appearance Card */}
                <div className="settings-card">
                    <div className="settings-card-header" onClick={() => toggleCard('appearance')}>
                        <div className="settings-card-header-left">
                            <div className="settings-card-icon appearance">
                                <Globe size={20} />
                            </div>
                            <h3 className="settings-card-title">{t('settings.appearance.title')}</h3>
                        </div>
                        <ChevronDown
                            size={20}
                            className={`settings-card-chevron ${expandedCards.appearance ? 'open' : ''}`}
                        />
                    </div>
                    <div className={`settings-card-content ${expandedCards.appearance ? 'open' : ''}`}>
                        <div className="settings-card-body">
                            <div className="setting-item">
                                <div className="setting-info">
                                    <div className="setting-label">{t('settings.appearance.language')}</div>
                                    <div className="setting-description">{t('settings.appearance.language_desc')}</div>
                                </div>
                                <select
                                    className="settings-select"
                                    value={settings.language}
                                    onChange={(e) => updateLanguage(e.target.value)}
                                    disabled={updating.language}
                                >
                                    <option value="en">🇺🇸 English</option>
                                    <option value="hi">🇮🇳 हिंदी</option>
                                    <option value="mr">🇮🇳 मराठी</option>
                                    <option value="es">🇪🇸 Español</option>
                                    <option value="fr">🇫🇷 Français</option>
                                    <option value="de">🇩🇪 Deutsch</option>
                                </select>
                            </div>
                            <SettingItem
                                label={t('settings.appearance.dark_mode')}
                                description={t('settings.appearance.dark_mode_desc')}
                                value={settings.darkMode}
                                loading={updating.darkMode}
                                onChange={() => updateSetting('darkMode', !settings.darkMode)}
                            />
                        </div>
                    </div>
                </div>

                {/* Features Card */}
                <div className="settings-card">
                    <div className="settings-card-header" onClick={() => toggleCard('features')}>
                        <div className="settings-card-header-left">
                            <div className="settings-card-icon features">
                                <Zap size={20} />
                            </div>
                            <h3 className="settings-card-title">{t('settings.features.title')}</h3>
                        </div>
                        <ChevronDown
                            size={20}
                            className={`settings-card-chevron ${expandedCards.features ? 'open' : ''}`}
                        />
                    </div>
                    <div className={`settings-card-content ${expandedCards.features ? 'open' : ''}`}>
                        <div className="settings-card-body">
                            <SettingItem
                                label={t('settings.features.auto_refill')}
                                description={t('settings.features.auto_refill_desc')}
                                value={settings.autoRefill}
                                loading={updating.autoRefill}
                                onChange={() => updateSetting('autoRefill', !settings.autoRefill)}
                            />
                            <SettingItem
                                label={t('settings.features.voice')}
                                description={t('settings.features.voice_desc')}
                                value={settings.voiceAssistant}
                                loading={updating.voiceAssistant}
                                onChange={() => updateSetting('voiceAssistant', !settings.voiceAssistant)}
                            />
                            <SettingItem
                                label={t('settings.features.admin')}
                                description={t('settings.features.admin_desc')}
                                value={settings.adminMode}
                                loading={updating.adminMode}
                                onChange={() => updateSetting('adminMode', !settings.adminMode)}
                            />
                        </div>
                    </div>
                </div>

                {/* Privacy Card */}
                <div className="settings-card">
                    <div className="settings-card-header" onClick={() => toggleCard('privacy')}>
                        <div className="settings-card-header-left">
                            <div className="settings-card-icon privacy">
                                <Lock size={20} />
                            </div>
                            <h3 className="settings-card-title">{t('settings.privacy.title')}</h3>
                        </div>
                        <ChevronDown
                            size={20}
                            className={`settings-card-chevron ${expandedCards.privacy ? 'open' : ''}`}
                        />
                    </div>
                    <div className={`settings-card-content ${expandedCards.privacy ? 'open' : ''}`}>
                        <div className="settings-card-body">
                            <SettingItem
                                label={t('settings.privacy.data_sharing')}
                                description={t('settings.privacy.data_sharing_desc')}
                                value={settings.dataSharing}
                                loading={updating.dataSharing}
                                onChange={() => updateSetting('dataSharing', !settings.dataSharing)}
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* System Status Sidebar */}
            <div className="settings-sidebar">
                <div className="status-panel">
                    <div className="status-panel-header">
                        <div className="status-indicator"></div>
                        <h4 className="status-panel-title">{t('settings.system_status.title')}</h4>
                    </div>

                    <div className="status-list">
                        <StatusItem
                            label={t('settings.system_status.ai_core')}
                            value={systemStatus.ai_core}
                            status={systemStatus.ai_core === 'online' ? 'online' : 'offline'}
                        />
                        <StatusItem
                            label={t('settings.system_status.database')}
                            value={systemStatus.database}
                            status={systemStatus.database === 'connected' ? 'online' : 'offline'}
                        />
                        <StatusItem
                            label={t('settings.system_status.security')}
                            value={systemStatus.security}
                            status={systemStatus.security === 'secure' ? 'online' : 'warning'}
                        />
                    </div>

                    <div className="metric-section">
                        <div className="metric-label">{t('settings.system_status.compliance')}</div>
                        <div className="metric-card">
                            <div className={`metric-value ${systemStatus.compliance_percent >= 90 ? 'high' :
                                systemStatus.compliance_percent >= 70 ? 'medium' : 'low'
                                }`}>
                                {systemStatus.compliance_percent}%
                            </div>
                            <div className="metric-subtitle">{t('status.regulated')}</div>
                        </div>
                    </div>

                    <div className="metric-section">
                        <div className="metric-label">{t('settings.system_status.ai_confidence')}</div>
                        <div className="metric-card">
                            <div className={`metric-value ${systemStatus.ai_confidence >= 90 ? 'high' :
                                systemStatus.ai_confidence >= 70 ? 'medium' : 'low'
                                }`}>
                                {systemStatus.ai_confidence}%
                            </div>
                            <div className="metric-subtitle">{t('common.high')}</div>
                        </div>
                    </div>

                    <div className="metric-section">
                        <div className="metric-label">{t('settings.system_status.recent_checks')}</div>
                        <div className="recent-checks">
                            {systemStatus.recent_checks.length > 0 ? (
                                systemStatus.recent_checks.map((check, i) => (
                                    <div key={i} className="check-item">
                                        <span className={`check-icon ${check.icon === '✓' ? 'success' : 'warning'}`}>
                                            {check.icon}
                                        </span>
                                        <span>{check.message}</span>
                                    </div>
                                ))
                            ) : (
                                <>
                                    <div className="check-item">
                                        <span className="check-icon success">✓</span>
                                        <span>{t('settings.system_status.system_init')}</span>
                                    </div>
                                    <div className="check-item">
                                        <span className="check-icon success">✓</span>
                                        <span>{t('settings.system_status.db_connected')}</span>
                                    </div>
                                    <div className="check-item">
                                        <span className="check-icon success">✓</span>
                                        <span>{t('settings.system_status.ai_ready')}</span>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Toast Notification */}
            {toast && (
                <div className={`settings-toast ${toast.type}`}>
                    {toast.type === 'success' ? <Check size={16} /> : <AlertTriangle size={16} />}
                    {toast.message}
                </div>
            )}
        </div>
    );
}

// Toggle Setting Item Component
function SettingItem({ label, description, value, loading, onChange }) {
    return (
        <div className="setting-item">
            <div className="setting-info">
                <div className="setting-label">{label}</div>
                <div className="setting-description">{description}</div>
            </div>
            <button
                className={`toggle-switch ${value ? 'active' : ''} ${loading ? 'loading' : ''}`}
                onClick={onChange}
                disabled={loading}
            >
                <span className="toggle-knob"></span>
            </button>
        </div>
    );
}

// Status Item Component
function StatusItem({ label, value, status }) {
    return (
        <div className="status-item">
            <div className="status-item-left">
                <div className={`status-dot ${status}`}></div>
                <span className="status-item-label">{label}</span>
            </div>
            <span className={`status-item-value ${status === 'warning' ? 'warning' : status === 'offline' ? 'danger' : ''}`}>
                {value}
            </span>
        </div>
    );
}

export default SettingsPage;
