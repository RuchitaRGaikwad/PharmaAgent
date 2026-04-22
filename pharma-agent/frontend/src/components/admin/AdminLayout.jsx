import React, { useState, useEffect } from 'react';
import {
    LayoutDashboard,
    Package,
    Bell,
    ShoppingCart,
    Activity,
    LogOut,
    User,
    ChevronLeft,
    Menu
} from 'lucide-react';
import './admin.css';

const API_BASE = import.meta.env.VITE_API_URL || 'https://pharmaagent.onrender.com';

// Admin Panel Components
import InventoryPanel from './InventoryPanel';
import AlertsPanel from './AlertsPanel';
import OrdersPanel from './OrdersPanel';
import TracesPanel from './TracesPanel';
import DashboardPanel from './DashboardPanel';
import NotificationBell from './NotificationBell';

function AdminLayout() {
    const [activePanel, setActivePanel] = useState('dashboard');
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [stats, setStats] = useState(null);
    const [adminUser, setAdminUser] = useState({ name: 'Admin User', email: 'admin@pharmaagent.com' });

    useEffect(() => {
        loadDashboardStats();
    }, []);

    const loadDashboardStats = async () => {
        try {
            const response = await fetch(`${API_BASE}/admin/dashboard-stats`);
            const data = await response.json();
            setStats(data);
        } catch (error) {
            console.error('Failed to load dashboard stats:', error);
        }
    };

    const menuItems = [
        { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
        { id: 'inventory', label: 'Inventory', icon: Package, badge: stats?.medicines?.low_stock },
        { id: 'alerts', label: 'Alerts', icon: Bell, badge: stats?.alerts?.active },
        { id: 'orders', label: 'Orders', icon: ShoppingCart, badge: stats?.orders?.pending },
        { id: 'traces', label: 'Agent Traces', icon: Activity },
    ];

    const renderPanel = () => {
        switch (activePanel) {
            case 'dashboard':
                return <DashboardPanel stats={stats} onNavigate={setActivePanel} />;
            case 'inventory':
                return <InventoryPanel onStatsChange={loadDashboardStats} />;
            case 'alerts':
                return <AlertsPanel />;
            case 'orders':
                return <OrdersPanel />;
            case 'traces':
                return <TracesPanel />;
            default:
                return <DashboardPanel stats={stats} onNavigate={setActivePanel} />;
        }
    };

    return (
        <div className="admin-layout">
            {/* Sidebar */}
            <aside className={`admin-sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
                <div className="admin-sidebar-header">
                    <div className="admin-logo">
                        <div className="admin-logo-icon">
                            <Package size={24} />
                        </div>
                        {!sidebarCollapsed && <span className="admin-logo-text">Admin Panel</span>}
                    </div>
                    <button
                        className="sidebar-collapse-btn"
                        onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                    >
                        {sidebarCollapsed ? <Menu size={18} /> : <ChevronLeft size={18} />}
                    </button>
                </div>

                <nav className="admin-nav">
                    {menuItems.map(item => (
                        <button
                            key={item.id}
                            className={`admin-nav-item ${activePanel === item.id ? 'active' : ''}`}
                            onClick={() => setActivePanel(item.id)}
                            title={sidebarCollapsed ? item.label : undefined}
                        >
                            <item.icon size={20} />
                            {!sidebarCollapsed && (
                                <>
                                    <span className="nav-label">{item.label}</span>
                                    {item.badge > 0 && (
                                        <span className="nav-badge">{item.badge}</span>
                                    )}
                                </>
                            )}
                        </button>
                    ))}
                </nav>

                <div className="admin-sidebar-footer">
                    {!sidebarCollapsed && (
                        <div className="admin-user-info">
                            <div className="admin-avatar">
                                <User size={16} />
                            </div>
                            <div className="admin-user-details">
                                <span className="admin-user-name">{adminUser.name}</span>
                                <span className="admin-user-role">Super Admin</span>
                            </div>
                        </div>
                    )}
                </div>
            </aside>

            {/* Main Content */}
            <main className="admin-main">
                {/* Top Header */}
                <header className="admin-header">
                    <div className="admin-header-left">
                        <h1 className="admin-page-title">
                            {menuItems.find(m => m.id === activePanel)?.label || 'Dashboard'}
                        </h1>
                    </div>
                    <div className="admin-header-right">
                        <NotificationBell />
                        <div className="admin-header-user">
                            <div className="admin-avatar small">
                                <User size={14} />
                            </div>
                            <span>{adminUser.name}</span>
                        </div>
                        <button className="admin-logout-btn" title="Logout">
                            <LogOut size={18} />
                        </button>
                    </div>
                </header>

                {/* Content Area */}
                <div className="admin-content">
                    {renderPanel()}
                </div>
            </main>
        </div>
    );
}

export default AdminLayout;
