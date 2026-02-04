import React from 'react';
import { AlertTriangle, CheckCircle, Clock, Shield } from 'lucide-react';

function SafetyAlerts() {
    // Mock safety data
    const recentChecks = [
        { id: 1, medicine: 'Paracetamol', result: 'safe', timestamp: new Date() },
        { id: 2, medicine: 'Ibuprofen', result: 'safe', timestamp: new Date(Date.now() - 3600000) },
    ];

    const interactionWarnings = [];

    return (
        <div className="page-container">
            <div className="page-header">
                <h1 className="page-title">⚠️ Safety Alerts</h1>
                <p className="page-subtitle">Drug interaction warnings and safety notifications</p>
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
                            <div style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--success)' }}>Safe</div>
                            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Current Status</div>
                        </div>
                    </div>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                        No drug interactions detected with your current medications.
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
                            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Checks Today</div>
                        </div>
                    </div>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                        All safety checks passed successfully.
                    </p>
                </div>
            </div>

            <h3 style={{ marginBottom: '16px', color: 'var(--text-secondary)' }}>
                Active Warnings
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
                    <p style={{ color: 'var(--success)', fontWeight: '500' }}>No active warnings</p>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '8px' }}>
                        Your medications have been verified for safety
                    </p>
                </div>
            ) : (
                <div className="table-container" style={{ marginBottom: '24px' }}>
                    <table>
                        <thead>
                            <tr>
                                <th>Warning</th>
                                <th>Severity</th>
                                <th>Medications</th>
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
                Recent Safety Checks
            </h3>

            <div className="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Medicine</th>
                            <th>Result</th>
                            <th>Time</th>
                        </tr>
                    </thead>
                    <tbody>
                        {recentChecks.map((check) => (
                            <tr key={check.id}>
                                <td><strong>{check.medicine}</strong></td>
                                <td>
                                    <span className="badge badge-success">
                                        <CheckCircle size={12} style={{ marginRight: '4px' }} />
                                        Safe
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
