import React from 'react';
import { useTranslation } from 'react-i18next';

const SystemStatusPanel = ({ status }) => {
    const { t } = useTranslation();

    return (
        <div className="status-panel">
            <div className="status-panel-header">
                <div className="status-indicator"></div>
                <h4 className="status-panel-title">{t('settings.system_status.title')}</h4>
            </div>

            <div className="status-list">
                <StatusItem
                    label={t('settings.system_status.ai_core')}
                    value={status.ai_core}
                    status={status.ai_core === 'online' ? 'online' : 'offline'}
                />
                <StatusItem
                    label={t('settings.system_status.database')}
                    value={status.database}
                    status={status.database === 'connected' ? 'online' : 'offline'}
                />
                <StatusItem
                    label={t('settings.system_status.security')}
                    value={status.security}
                    status={status.security === 'secure' ? 'online' : 'warning'}
                />
            </div>

            <div className="metric-section">
                <div className="metric-label">{t('settings.system_status.compliance')}</div>
                <div className="metric-card">
                    <div className={`metric-value ${status.compliance_percent >= 90 ? 'high' :
                        status.compliance_percent >= 70 ? 'medium' : 'low'
                        }`}>
                        {status.compliance_percent}%
                    </div>
                    <div className="metric-subtitle">{t('status.regulated')}</div>
                </div>
            </div>

            <div className="metric-section">
                <div className="metric-label">{t('settings.system_status.ai_confidence')}</div>
                <div className="metric-card">
                    <div className={`metric-value ${status.ai_confidence >= 90 ? 'high' :
                        status.ai_confidence >= 70 ? 'medium' : 'low'
                        }`}>
                        {status.ai_confidence}%
                    </div>
                    <div className="metric-subtitle">{t('common.high')}</div>
                </div>
            </div>

            <div className="metric-section">
                <div className="metric-label">{t('settings.system_status.recent_checks')}</div>
                <div className="recent-checks">
                    {status.recent_checks.length > 0 ? (
                        status.recent_checks.map((check, i) => (
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
    );
};

// Sub-component for individual status items
const StatusItem = ({ label, value, status }) => {
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
};

export default SystemStatusPanel;
