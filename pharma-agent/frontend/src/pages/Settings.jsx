import React, { useState } from 'react';
import { Bell, Moon, Globe, Shield, Volume2, Database } from 'lucide-react';

function SettingsPage() {
    const [settings, setSettings] = useState({
        notifications: true,
        emailAlerts: true,
        smsAlerts: false,
        darkMode: true,
        language: 'en',
        autoRefill: true,
        voiceAssistant: true,
        dataSharing: false
    });

    const toggleSetting = (key) => {
        setSettings(prev => ({ ...prev, [key]: !prev[key] }));
    };

    const SettingToggle = ({ label, description, settingKey, icon: Icon }) => (
        <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px 0',
            borderBottom: '1px solid var(--border-color)'
        }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                    width: '40px',
                    height: '40px',
                    background: 'var(--bg-tertiary)',
                    borderRadius: '10px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                }}>
                    <Icon size={18} style={{ color: 'var(--accent-primary)' }} />
                </div>
                <div>
                    <div style={{ fontWeight: '500' }}>{label}</div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{description}</div>
                </div>
            </div>
            <div
                className={`toggle-switch ${settings[settingKey] ? 'active' : ''}`}
                onClick={() => toggleSetting(settingKey)}
            />
        </div>
    );

    return (
        <div className="page-container">
            <div className="page-header">
                <h1 className="page-title">⚙️ Settings</h1>
                <p className="page-subtitle">Manage your preferences and account settings</p>
            </div>

            <div className="medicine-card" style={{ marginBottom: '24px' }}>
                <h3 style={{ marginBottom: '8px' }}>Notifications</h3>

                <SettingToggle
                    label="Push Notifications"
                    description="Receive alerts for refills and orders"
                    settingKey="notifications"
                    icon={Bell}
                />

                <SettingToggle
                    label="Email Alerts"
                    description="Get order confirmations via email"
                    settingKey="emailAlerts"
                    icon={Bell}
                />

                <SettingToggle
                    label="SMS Alerts"
                    description="Receive text message reminders"
                    settingKey="smsAlerts"
                    icon={Bell}
                />
            </div>

            <div className="medicine-card" style={{ marginBottom: '24px' }}>
                <h3 style={{ marginBottom: '8px' }}>Accessibility</h3>

                <SettingToggle
                    label="Dark Mode"
                    description="Use dark theme for better visibility"
                    settingKey="darkMode"
                    icon={Moon}
                />

                <SettingToggle
                    label="Voice Assistant"
                    description="Enable voice commands and responses"
                    settingKey="voiceAssistant"
                    icon={Volume2}
                />

                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '16px 0',
                    borderBottom: '1px solid var(--border-color)'
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div style={{
                            width: '40px',
                            height: '40px',
                            background: 'var(--bg-tertiary)',
                            borderRadius: '10px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                        }}>
                            <Globe size={18} style={{ color: 'var(--accent-primary)' }} />
                        </div>
                        <div>
                            <div style={{ fontWeight: '500' }}>Language</div>
                            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Select your preferred language</div>
                        </div>
                    </div>
                    <select
                        className="filter-select"
                        value={settings.language}
                        onChange={(e) => setSettings(prev => ({ ...prev, language: e.target.value }))}
                        style={{ width: '120px' }}
                    >
                        <option value="en">English</option>
                        <option value="es">Español</option>
                        <option value="fr">Français</option>
                        <option value="hi">हिंदी</option>
                    </select>
                </div>
            </div>

            <div className="medicine-card">
                <h3 style={{ marginBottom: '8px' }}>Privacy & Data</h3>

                <SettingToggle
                    label="Auto-Refill"
                    description="Automatically notify when refills are due"
                    settingKey="autoRefill"
                    icon={Database}
                />

                <SettingToggle
                    label="Data Sharing"
                    description="Share anonymized data to improve AI"
                    settingKey="dataSharing"
                    icon={Shield}
                />
            </div>
        </div>
    );
}

export default SettingsPage;
