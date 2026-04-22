import React, { useState, useEffect } from 'react';
import { Bell, AlertTriangle, Info, XCircle, RefreshCw, CheckCircle } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'https://pharmaagent.onrender.com';

function AlertsPanel() {
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('all');

    useEffect(() => {
        loadAlerts();
    }, []);

    const loadAlerts = async () => {
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE}/admin/alerts`);
            const data = await response.json();
            setAlerts(data.alerts || []);
        } catch (error) {
            console.error('Failed to load alerts:', error);
        } finally {
            setLoading(false);
        }
    };

    const dismissAlert = async (alertId) => {
        try {
            await fetch(`${API_BASE}/admin/alerts/${alertId}/dismiss`, {
                method: 'PATCH'
            });
            loadAlerts();
        } catch (error) {
            console.error('Failed to dismiss alert:', error);
        }
    };

    const getPriorityIcon = (priority) => {
        switch (priority) {
            case 'high': return <AlertTriangle className="priority-high" />;
            case 'medium': return <Bell className="priority-medium" />;
            default: return <Info className="priority-low" />;
        }
    };

    const getPriorityClass = (priority) => {
        switch (priority) {
            case 'high': return 'priority-high';
            case 'medium': return 'priority-medium';
            default: return 'priority-low';
        }
    };

    const filteredAlerts = alerts.filter(alert => {
        if (filter === 'all') return true;
        if (filter === 'active') return alert.status === 'pending';
        return alert.priority === filter;
    });

    return (
        <div className="alerts-panel">
            {/* Filter Bar */}
            <div className="panel-toolbar">
                <div className="filter-tabs">
                    <button
                        className={`filter-tab ${filter === 'all' ? 'active' : ''}`}
                        onClick={() => setFilter('all')}
                    >
                        All ({alerts.length})
                    </button>
                    <button
                        className={`filter-tab ${filter === 'active' ? 'active' : ''}`}
                        onClick={() => setFilter('active')}
                    >
                        Active ({alerts.filter(a => a.status === 'pending').length})
                    </button>
                    <button
                        className={`filter-tab high ${filter === 'high' ? 'active' : ''}`}
                        onClick={() => setFilter('high')}
                    >
                        High Priority
                    </button>
                </div>
                <button className="btn-secondary" onClick={loadAlerts}>
                    <RefreshCw size={16} />
                    Refresh
                </button>
            </div>

            {/* Alerts List */}
            <div className="alerts-list">
                {loading ? (
                    <div className="loading-state">Loading alerts...</div>
                ) : filteredAlerts.length === 0 ? (
                    <div className="empty-state">
                        <CheckCircle size={48} />
                        <h3>No Alerts</h3>
                        <p>All clear! No alerts match your filter.</p>
                    </div>
                ) : (
                    filteredAlerts.map(alert => (
                        <div
                            key={alert.id}
                            className={`alert-card ${getPriorityClass(alert.priority)} ${alert.status === 'dismissed' ? 'dismissed' : ''}`}
                        >
                            <div className="alert-icon">
                                {getPriorityIcon(alert.priority)}
                            </div>
                            <div className="alert-content">
                                <div className="alert-header">
                                    <span className={`alert-type ${alert.type}`}>{alert.type}</span>
                                    <span className="alert-time">
                                        {alert.created_at ? new Date(alert.created_at).toLocaleString() : 'Unknown'}
                                    </span>
                                </div>
                                <p className="alert-message">{alert.message}</p>
                                <div className="alert-meta">
                                    <span>Customer #{alert.customer_id}</span>
                                    <span className={`alert-status ${alert.status}`}>
                                        {alert.status}
                                    </span>
                                </div>
                            </div>
                            {alert.status !== 'dismissed' && (
                                <button
                                    className="alert-dismiss"
                                    onClick={() => dismissAlert(alert.id)}
                                    title="Dismiss"
                                >
                                    <XCircle size={20} />
                                </button>
                            )}
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}

export default AlertsPanel;
