import React from 'react';
import { useTranslation } from 'react-i18next';
import { AlertTriangle, CheckCircle, Clock, Shield } from 'lucide-react';

function SafetyAlerts() {
    const { t } = useTranslation();
    const recentChecks = [
        { id: 1, medicine: 'Paracetamol', result: 'safe', timestamp: new Date() },
        { id: 2, medicine: 'Ibuprofen', result: 'safe', timestamp: new Date(Date.now() - 3600000) },
    ];

    const interactionWarnings = [];

    return (
        <div className="page-container">
            <div className="page-header">
                <h1 className="page-title">⚠️ {t('safety.title')}</h1>
                <p className="page-subtitle">{t('safety.subtitle')}</p>
            </div>

            <div className="cards-grid" style={{ marginBottom: '24px' }}>
                <div className="medicine-card">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                        <div style={{
                            width: '48px',
                            height: '48px',
                            background: 'rgba(34, 197, 94, 0.15)',
                            borderRadius: '12px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                        }}>
                            <Shield size={24} style={{ color: 'var(--success)' }} />
                        </div>
                        <div>
                            <div style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--success)' }}>{t('safety.safe')}</div>
                            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{t('safety.current_status')}</div>
                        </div>
                    </div>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                        {t('safety.all_safe')}
                    </p>
                </div>

                <div className="medicine-card">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                        <div style={{
                            width: '48px',
                            height: '48px',
                            background: 'rgba(59, 130, 246, 0.15)',
                            borderRadius: '12px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                        }}>
                            <Clock size={24} style={{ color: 'var(--info)' }} />
                        </div>
                        <div>
                            <div style={{ fontSize: '1.5rem', fontWeight: '700' }}>{recentChecks.length}</div>
                            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{t('safety.checks_today')}</div>
                        </div>
                    </div>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                        {t('safety.all_safe_checks')}
                    </p>
                </div>
            </div>

            <h3 style={{ marginBottom: '16px', color: 'var(--text-secondary)' }}>
                {t('safety.active_alerts')}
            </h3>

            {interactionWarnings.length === 0 ? (
                <div style={{
                    textAlign: 'center',
                    padding: '40px',
                    background: 'var(--bg-tertiary)',
                    borderRadius: '12px',
                    marginBottom: '24px'
                }}>
                    <CheckCircle size={48} style={{ color: 'var(--success)', marginBottom: '16px' }} />
                    <p style={{ color: 'var(--success)', fontWeight: '500' }}>{t('safety.no_active_title')}</p>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '8px' }}>
                        {t('safety.no_active_desc')}
                    </p>
                </div>
            ) : (
                <div className="table-container" style={{ marginBottom: '24px' }}>
                    <table>
                        <thead>
                            <tr>
                                <th>{t('safety.warning')}</th>
                                <th>{t('safety.severity')}</th>
                                <th>{t('safety.medications')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {interactionWarnings.map((warning) => (
                                <tr key={warning.id}>
                                    <td>{warning.message}</td>
                                    <td><span className="badge badge-warning">{warning.severity}</span></td>
                                    <td>{warning.medications.join(', ')}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            <h3 style={{ marginBottom: '16px', color: 'var(--text-secondary)' }}>
                {t('safety.recent_checks')}
            </h3>

            <div className="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>{t('safety.medicine')}</th>
                            <th>{t('safety.result')}</th>
                            <th>{t('safety.time')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {recentChecks.map((check) => (
                            <tr key={check.id}>
                                <td><strong>{check.medicine}</strong></td>
                                <td>
                                    <span className="badge badge-success">
                                        <CheckCircle size={12} style={{ marginRight: '4px' }} />
                                        {t('safety.safe')}
                                    </span>
                                </td>
                                <td>{check.timestamp.toLocaleTimeString()}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

export default SafetyAlerts;
