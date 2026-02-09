import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { RefreshCw, Bell, Send, X } from 'lucide-react';
import { getAlerts, updateAlertStatus, triggerRefillCheck } from '../services/api';

function Refills() {
    const { t } = useTranslation();
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    useEffect(() => {
        loadAlerts();
    }, []);

    const loadAlerts = async () => {
        try {
            const data = await getAlerts();
            setAlerts(data);
        } catch (err) {
            console.error('Failed to load alerts:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleRunCheck = async () => {
        setRefreshing(true);
        try {
            await triggerRefillCheck();
            await loadAlerts();
        } catch (err) {
            console.error('Refill check failed:', err);
        }
        setRefreshing(false);
    };

    const handleSendReminder = async (alertId) => {
        try {
            await updateAlertStatus(alertId, 'sent');
            setAlerts(alerts.map(a => a.id === alertId ? { ...a, status: 'sent' } : a));
        } catch (err) {
            console.error('Failed to send reminder:', err);
        }
    };

    const handleDismiss = async (alertId) => {
        try {
            await updateAlertStatus(alertId, 'dismissed');
            setAlerts(alerts.filter(a => a.id !== alertId));
        } catch (err) {
            console.error('Failed to dismiss alert:', err);
        }
    };

    const pendingAlerts = alerts.filter(a => a.status === 'pending');
    const sentAlerts = alerts.filter(a => a.status === 'sent');

    return (
        <div className="page-container">
            <div className="page-header">
                <h1 className="page-title">🔄 {t('refills.title')}</h1>
                <p className="page-subtitle">{t('refills.subtitle')}</p>
            </div>

            <div style={{ marginBottom: '24px', display: 'flex', gap: '12px' }}>
                <button
                    className="btn btn-primary"
                    onClick={handleRunCheck}
                    disabled={refreshing}
                >
                    <RefreshCw size={18} className={refreshing ? 'spinning' : ''} />
                    {t('refills.run_check')}
                </button>
            </div>

            {loading ? (
                <div style={{ textAlign: 'center', padding: '60px' }}>
                    <RefreshCw size={32} style={{ animation: 'spin 1s linear infinite', color: 'var(--accent-primary)' }} />
                </div>
            ) : (
                <>
                    <h3 style={{ marginBottom: '16px', color: 'var(--text-secondary)' }}>
                        {t('refills.pending_reminders')} ({pendingAlerts.length})
                    </h3>

                    {pendingAlerts.length === 0 ? (
                        <div style={{
                            textAlign: 'center',
                            padding: '40px',
                            background: 'var(--bg-tertiary)',
                            borderRadius: '12px',
                            marginBottom: '24px'
                        }}>
                            <Bell size={48} style={{ color: 'var(--text-muted)', marginBottom: '16px' }} />
                            <p style={{ color: 'var(--text-muted)' }}>{t('refills.no_pending')}</p>
                        </div>
                    ) : (
                        <div className="table-container" style={{ marginBottom: '24px' }}>
                            <table>
                                <thead>
                                    <tr>
                                        <th>{t('refills.customer')}</th>
                                        <th>{t('refills.medicine')}</th>
                                        <th>{t('refills.refill_date')}</th>
                                        <th>{t('refills.actions')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {pendingAlerts.map((alert) => (
                                        <tr key={alert.id}>
                                            <td>
                                                <strong>{alert.customer_name}</strong>
                                                <br />
                                                <small style={{ color: 'var(--text-muted)' }}>{alert.customer_email}</small>
                                            </td>
                                            <td>{alert.medicine_name}</td>
                                            <td>{new Date(alert.expected_refill_date).toLocaleDateString()}</td>
                                            <td>
                                                <div style={{ display: 'flex', gap: '8px' }}>
                                                    <button
                                                        className="btn btn-primary"
                                                        style={{ padding: '6px 12px' }}
                                                        onClick={() => handleSendReminder(alert.id)}
                                                    >
                                                        <Send size={14} /> {t('common.send')}
                                                    </button>
                                                    <button
                                                        className="btn btn-secondary"
                                                        style={{ padding: '6px 12px' }}
                                                        onClick={() => handleDismiss(alert.id)}
                                                    >
                                                        <X size={14} />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {sentAlerts.length > 0 && (
                        <>
                            <h3 style={{ marginBottom: '16px', color: 'var(--text-secondary)' }}>
                                {t('refills.sent_reminders')} ({sentAlerts.length})
                            </h3>
                            <div className="table-container">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>{t('refills.customer')}</th>
                                            <th>{t('refills.medicine')}</th>
                                            <th>{t('orders.status')}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {sentAlerts.map((alert) => (
                                            <tr key={alert.id}>
                                                <td>{alert.customer_name}</td>
                                                <td>{alert.medicine_name}</td>
                                                <td><span className="badge badge-success">{t('refills.sent')}</span></td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </>
                    )}
                </>
            )}
        </div>
    );
}

export default Refills;
