import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Bell, Globe, Zap, Lock, RefreshCw, Check, AlertTriangle } from 'lucide-react';
import './settings.css';

// Modular Components
import SettingsCard from '../components/settings/SettingsCard';
import SystemStatusPanel from '../components/settings/SystemStatusPanel';
import SettingItem from '../components/settings/SettingItem';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
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
        const currentLang = i18n.language || 'en';
        if (settings.language && settings.language !== currentLang && !loading) {
            i18n.changeLanguage(settings.language);
        }
    }, [settings.language, i18n, loading]);

    // Apply dark/light theme
    useEffect(() => {
        if (settings.darkMode) {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
        }
    }, [settings.darkMode]);

    const loadSettings = async () => {
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
            // Don't show toast for background polling failures
        }
    };

    const updateSetting = async (key, value) => {
        // Optimistic update
        const oldValue = settings[key];
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
                throw new Error('Update failed');
            }
        } catch (error) {
            // Revert on failure
            setSettings(prev => ({ ...prev, [key]: oldValue }));
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
                throw new Error('Language update failed');
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
                <SettingsCard
                    icon={Bell}
                    title={t('settings.notifications.title')}
                    type="notifications"
                    expanded={expandedCards.notifications}
                    onToggle={() => toggleCard('notifications')}
                >
                    <SettingItem
                        label={t('settings.notifications.push')}
                        description={t('settings.notifications.push_desc')}
                        value={settings.notifications}
                        loading={updating.notifications}
                        onChange={() => updateSetting('notifications', !settings.notifications)}
                    />
                    {/* Fixed Logic: Email Alerts */}
                    <SettingItem
                        label={t('settings.notifications.email')}
                        description={t('settings.notifications.email_desc')}
                        value={settings.emailAlerts}
                        loading={updating.emailAlerts}
                        onChange={() => updateSetting('emailAlerts', !settings.emailAlerts)}
                    />
                    {/* Fixed Logic: SMS Alerts */}
                    <SettingItem
                        label={t('settings.notifications.sms')}
                        description={t('settings.notifications.sms_desc')}
                        value={settings.smsAlerts}
                        loading={updating.smsAlerts}
                        onChange={() => updateSetting('smsAlerts', !settings.smsAlerts)}
                    />
                </SettingsCard>

                {/* Language & Appearance Card */}
                <SettingsCard
                    icon={Globe}
                    title={t('settings.appearance.title')}
                    type="appearance"
                    expanded={expandedCards.appearance}
                    onToggle={() => toggleCard('appearance')}
                >
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
                </SettingsCard>

                {/* Features Card */}
                <SettingsCard
                    icon={Zap}
                    title={t('settings.features.title')}
                    type="features"
                    expanded={expandedCards.features}
                    onToggle={() => toggleCard('features')}
                >
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
                </SettingsCard>

                {/* Privacy Card */}
                <SettingsCard
                    icon={Lock}
                    title={t('settings.privacy.title')}
                    type="privacy"
                    expanded={expandedCards.privacy}
                    onToggle={() => toggleCard('privacy')}
                >
                    <SettingItem
                        label={t('settings.privacy.data_sharing')}
                        description={t('settings.privacy.data_sharing_desc')}
                        value={settings.dataSharing}
                        loading={updating.dataSharing}
                        onChange={() => updateSetting('dataSharing', !settings.dataSharing)}
                    />
                </SettingsCard>
            </div>

            {/* System Status Sidebar */}
            <div className="settings-sidebar">
                <SystemStatusPanel status={systemStatus} />
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

export default SettingsPage;
