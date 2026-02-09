import React from 'react';
import { Package, Bell, ShoppingCart, Activity, TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react';

function DashboardPanel({ stats, onNavigate }) {
    const statCards = [
        {
            id: 'inventory',
            title: 'Medicines',
            value: stats?.medicines?.total || 0,
            subtitle: `${stats?.medicines?.low_stock || 0} low stock`,
            icon: Package,
            color: 'blue',
            trend: stats?.medicines?.low_stock > 0 ? 'warning' : 'up'
        },
        {
            id: 'alerts',
            title: 'Active Alerts',
            value: stats?.alerts?.active || 0,
            subtitle: `${stats?.alerts?.total || 0} total`,
            icon: Bell,
            color: 'orange',
            trend: stats?.alerts?.active > 0 ? 'warning' : 'up'
        },
        {
            id: 'orders',
            title: 'Pending Orders',
            value: stats?.orders?.pending || 0,
            subtitle: `${stats?.orders?.total || 0} total`,
            icon: ShoppingCart,
            color: 'green',
            trend: 'up'
        },
        {
            id: 'traces',
            title: 'Agent Traces',
            value: stats?.traces?.total || 0,
            subtitle: 'All time',
            icon: Activity,
            color: 'purple',
            trend: 'up'
        }
    ];

    return (
        <div className="dashboard-panel">
            {/* Stats Grid */}
            <div className="stats-grid">
                {statCards.map(card => (
                    <div
                        key={card.id}
                        className={`stat-card ${card.color}`}
                        onClick={() => onNavigate(card.id)}
                    >
                        <div className="stat-card-header">
                            <div className={`stat-icon ${card.color}`}>
                                <card.icon size={24} />
                            </div>
                            {card.trend === 'warning' ? (
                                <AlertTriangle size={16} className="trend-warning" />
                            ) : card.trend === 'up' ? (
                                <TrendingUp size={16} className="trend-up" />
                            ) : (
                                <TrendingDown size={16} className="trend-down" />
                            )}
                        </div>
                        <div className="stat-value">{card.value}</div>
                        <div className="stat-title">{card.title}</div>
                        <div className="stat-subtitle">{card.subtitle}</div>
                    </div>
                ))}
            </div>

            {/* Quick Actions */}
            <div className="dashboard-section">
                <h3 className="section-title">Quick Actions</h3>
                <div className="quick-actions">
                    <button className="quick-action-btn" onClick={() => onNavigate('inventory')}>
                        <Package size={20} />
                        <span>Manage Inventory</span>
                    </button>
                    <button className="quick-action-btn" onClick={() => onNavigate('orders')}>
                        <ShoppingCart size={20} />
                        <span>View Orders</span>
                    </button>
                    <button className="quick-action-btn" onClick={() => onNavigate('alerts')}>
                        <Bell size={20} />
                        <span>Check Alerts</span>
                    </button>
                    <button className="quick-action-btn" onClick={() => onNavigate('traces')}>
                        <Activity size={20} />
                        <span>Agent Logs</span>
                    </button>
                </div>
            </div>

            {/* System Status */}
            <div className="dashboard-section">
                <h3 className="section-title">System Status</h3>
                <div className="status-cards">
                    <div className="status-card online">
                        <div className="status-dot"></div>
                        <span>AI Core</span>
                        <span className="status-label">Online</span>
                    </div>
                    <div className="status-card online">
                        <div className="status-dot"></div>
                        <span>Database</span>
                        <span className="status-label">Connected</span>
                    </div>
                    <div className="status-card online">
                        <div className="status-dot"></div>
                        <span>Safety Agent</span>
                        <span className="status-label">Active</span>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default DashboardPanel;
