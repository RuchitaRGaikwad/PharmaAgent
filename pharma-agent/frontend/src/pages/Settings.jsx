import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { 
    Bell, Globe, Zap, Lock, RefreshCw, Check, AlertTriangle, 
    Shield, Cpu, Eye, Info, Search, Trash2 
} from 'lucide-react';
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
        adminMode: false,
        // New Fields
        security2fa: false,
        sessionTimeout: 30,
        aiResponseStyle: 'Detailed',
        aiVoiceSpeed: 1.0,
        accessibilityHighContrast: false,
        accessibilityFontSize: 'Medium'
    });

    // UI state
    const [loading, setLoading] = useState(true);
    const [updating, setUpdating] = useState({});
    const [toast, setToast] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [isTranslating, setIsTranslating] = useState(false);
    
    const [expandedCards, setExpandedCards] = useState({
        notifications: true,
        appearance: true,
        ai: false,
        security: false,
        privacy: false,
        accessibility: false
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

        // Poll system status every 15 seconds
        const interval = setInterval(loadSystemStatus, 15000);
        return () => clearInterval(interval);
    }, []);

    // Apply dark/light theme & high contrast
    useEffect(() => {
        document.documentElement.setAttribute('data-theme', settings.darkMode ? 'dark' : 'light');
        document.documentElement.classList.toggle('high-contrast', settings.accessibilityHighContrast);
        document.documentElement.setAttribute('data-font-size', settings.accessibilityFontSize.toLowerCase());
    }, [settings.darkMode, settings.accessibilityHighContrast, settings.accessibilityFontSize]);

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
            setSettings(prev => ({ ...prev, [key]: oldValue }));
            showToast(t('common.error'), 'error');
        } finally {
            setUpdating(prev => ({ ...prev, [key]: false }));
        }
    };

    const updateLanguage = async (lang) => {
        if (settings.language === lang) return;
        
        // Show loading overlay for a second
        setIsTranslating(true);
        const oldLang = settings.language;
        
        // Optimistic UI
        setSettings(prev => ({ ...prev, language: lang }));
        
        try {
            // Update backend
            const response = await fetch(
                `${API_BASE}/settings/${USER_ID}?key=language&value=${lang}`,
                { method: 'PATCH' }
            );

            if (response.ok) {
                // Actually change the language after a small delay to "feel" the change
                setTimeout(() => {
                    i18n.changeLanguage(lang);
                    setIsTranslating(false);
                    showToast(t('common.success'), 'success');
                }, 1000);
            } else {
                throw new Error('Language update failed');
            }
        } catch (error) {
            setSettings(prev => ({ ...prev, language: oldLang }));
            setIsTranslating(false);
            showToast(t('common.error'), 'error');
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
                    <RefreshCw size={32} className="animate-spin" />
                    <p style={{ marginTop: '16px' }}>{t('common.loading')}</p>
                </div>
            </div>
        );
    }

    const languages = [
        { code: 'en', label: 'English', flag: '🇺🇸' },
        { code: 'hi', label: 'हिन्दी', flag: '🇮🇳' },
        { code: 'mr', label: 'मराठी', flag: '🇮🇳' },
        { code: 'es', label: 'Español', flag: '🇪🇸' },
        { code: 'fr', label: 'Français', flag: '🇫🇷' },
        { code: 'de', label: 'Deutsch', flag: '🇩🇪' }
    ];

    return (
        <div className="settings-page">
            {/* Translation Loading Overlay */}
            {isTranslating && (
                <div className="translation-overlay">
                    <div className="translation-spinner">
                        <Globe size={48} className="animate-pulse" />
                        <h2>{t('common.loading')}</h2>
                    </div>
                </div>
            )}

            {/* Main Settings Column */}
            <div className="settings-main">
                <div className="settings-header">
                    <div className="header-text">
                        <h1>⚙️ {t('settings.title')}</h1>
                        <p>{t('settings.subtitle')}</p>
                    </div>
                    <div className="header-search">
                        <Search size={18} />
                        <input 
                            type="text" 
                            placeholder={t('medicines.search_placeholder')} 
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>
                </div>

                {/* Notifications Section */}
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
                </SettingsCard>

                {/* Regional & Appearance Section */}
                <SettingsCard
                    icon={Globe}
                    title={t('settings.appearance.title')}
                    type="appearance"
                    expanded={expandedCards.appearance}
                    onToggle={() => toggleCard('appearance')}
                >
                    <div className="setting-section">
                        <div className="section-header">
                            <span className="section-label">{t('settings.appearance.language')}</span>
                            <span className="section-desc">{t('settings.appearance.language_desc')}</span>
                        </div>
                        <div className="language-vertical-list">
                            {languages.map((lang) => (
                                <div 
                                    key={lang.code} 
                                    className={`language-list-item ${settings.language === lang.code ? 'active' : ''}`}
                                    onClick={() => updateLanguage(lang.code)}
                                >
                                    <div className="lang-info">
                                        <span className="lang-flag">{lang.flag}</span>
                                        <span className="lang-label">{lang.label}</span>
                                    </div>
                                    <div className={`lang-toggle ${settings.language === lang.code ? 'on' : 'off'}`}>
                                        <div className="toggle-thumb"></div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                    <SettingItem
                        label={t('settings.appearance.dark_mode')}
                        description={t('settings.appearance.dark_mode_desc')}
                        value={settings.darkMode}
                        loading={updating.darkMode}
                        onChange={() => updateSetting('darkMode', !settings.darkMode)}
                    />
                </SettingsCard>

                {/* AI Preferences Section */}
                <SettingsCard
                    icon={Cpu}
                    title={t('settings.ai.title')}
                    type="ai"
                    expanded={expandedCards.ai}
                    onToggle={() => toggleCard('ai')}
                >
                    <div className="setting-item">
                        <div className="setting-info">
                            <div className="setting-label">{t('settings.ai.response_style')}</div>
                        </div>
                        <select 
                            className="settings-select"
                            value={settings.aiResponseStyle}
                            onChange={(e) => updateSetting('aiResponseStyle', e.target.value)}
                        >
                            <option value="Concise">{t('settings.ai.styles.concise')}</option>
                            <option value="Detailed">{t('settings.ai.styles.detailed')}</option>
                            <option value="Clinical">{t('settings.ai.styles.clinical')}</option>
                        </select>
                    </div>
                    <SettingItem
                        label={t('settings.features.voice')}
                        description={t('settings.features.voice_desc')}
                        value={settings.voiceAssistant}
                        loading={updating.voiceAssistant}
                        onChange={() => updateSetting('voiceAssistant', !settings.voiceAssistant)}
                    />
                </SettingsCard>

                {/* Security Section */}
                <SettingsCard
                    icon={Shield}
                    title={t('settings.security.title')}
                    type="security"
                    expanded={expandedCards.security}
                    onToggle={() => toggleCard('security')}
                >
                    <SettingItem
                        label={t('settings.security.2fa')}
                        description={t('settings.security.2fa_desc')}
                        value={settings.security2fa}
                        loading={updating.security2fa}
                        onChange={() => updateSetting('security2fa', !settings.security2fa)}
                    />
                    <div className="setting-item">
                        <div className="setting-info">
                            <div className="setting-label">{t('settings.security.session_timeout')}</div>
                        </div>
                        <input 
                            type="range" 
                            min="5" 
                            max="120" 
                            step="5"
                            className="settings-slider"
                            value={settings.sessionTimeout}
                            onChange={(e) => updateSetting('sessionTimeout', parseInt(e.target.value))}
                        />
                        <span className="slider-value">{settings.sessionTimeout}m</span>
                    </div>
                </SettingsCard>

                {/* Accessibility Section */}
                <SettingsCard
                    icon={Eye}
                    title={t('settings.accessibility.title')}
                    type="accessibility"
                    expanded={expandedCards.accessibility}
                    onToggle={() => toggleCard('accessibility')}
                >
                    <SettingItem
                        label={t('settings.accessibility.high_contrast')}
                        value={settings.accessibilityHighContrast}
                        loading={updating.accessibilityHighContrast}
                        onChange={() => updateSetting('accessibilityHighContrast', !settings.accessibilityHighContrast)}
                    />
                    <div className="setting-item">
                        <div className="setting-info">
                            <div className="setting-label">{t('settings.accessibility.font_size')}</div>
                        </div>
                        <div className="font-size-toggle">
                            {['Small', 'Medium', 'Large'].map(size => (
                                <button 
                                    key={size}
                                    className={`size-btn ${settings.accessibilityFontSize === size ? 'active' : ''}`}
                                    onClick={() => updateSetting('accessibilityFontSize', size)}
                                >
                                    {t(`settings.accessibility.sizes.${size.toLowerCase()}`)}
                                </button>
                            ))}
                        </div>
                    </div>
                </SettingsCard>

                {/* Privacy & Danger Zone */}
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
                    <div className="danger-zone">
                        <button className="danger-btn">
                            <Trash2 size={16} />
                            {t('common.delete')} Conversation History
                        </button>
                    </div>
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
