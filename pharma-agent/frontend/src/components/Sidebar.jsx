import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
    MessageSquare,
    Upload,
    Pill,
    RefreshCw,
    Heart,
    ShoppingCart,
    AlertTriangle,
    Settings,
    ChevronLeft,
    ChevronRight,
    Shield
} from 'lucide-react';

/**
 * Sidebar - Collapsible Navigation Panel
 */
function Sidebar({ collapsed, onToggle, adminMode }) {
    const { t } = useTranslation();

    const navItems = [
        { path: '/', icon: MessageSquare, label: t('nav.chat') },
        { path: '/upload', icon: Upload, label: t('nav.upload') },
        { path: '/medicines', icon: Pill, label: t('nav.medicines') },
        { path: '/refills', icon: RefreshCw, label: t('nav.refills'), badge: 2 },
        { path: '/health', icon: Heart, label: t('nav.profile') },
        { path: '/orders', icon: ShoppingCart, label: t('nav.orders') },
        { path: '/alerts', icon: AlertTriangle, label: t('nav.safety') },
        { path: '/settings', icon: Settings, label: t('nav.settings') },
    ];

    return (
        <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
            {/* Toggle Button */}
            <button
                className="sidebar-toggle"
                onClick={onToggle}
                aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
                {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
            </button>

            {/* Navigation */}
            <nav className="sidebar-nav">
                <ul className="nav-list">
                    {navItems.map((item) => (
                        <li key={item.path} className="nav-item">
                            <NavLink
                                to={item.path}
                                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                                title={collapsed ? item.label : undefined}
                            >
                                <span className="nav-icon">
                                    <item.icon size={20} />
                                </span>
                                {!collapsed && (
                                    <>
                                        <span className="nav-label">{item.label}</span>
                                        {item.badge && <span className="nav-badge">{item.badge}</span>}
                                    </>
                                )}
                            </NavLink>
                        </li>
                    ))}

                    {/* Admin Dashboard - Only visible in Admin Mode */}
                    {adminMode && (
                        <li className="nav-item">
                            <NavLink
                                to="/admin"
                                className={({ isActive }) => `nav-link admin-nav ${isActive ? 'active' : ''}`}
                                title={collapsed ? 'Admin Dashboard' : undefined}
                            >
                                <span className="nav-icon">
                                    <Shield size={20} />
                                </span>
                                {!collapsed && (
                                    <span className="nav-label">Admin Dashboard</span>
                                )}
                            </NavLink>
                        </li>
                    )}
                </ul>
            </nav>

            {/* Footer - Compliance */}
            {!collapsed && (
                <div className="sidebar-footer">
                    <div className="compliance-indicator">
                        <span className="compliance-label">{t('status.regulated')}</span>
                        <span className="compliance-value">98%</span>
                    </div>
                    <div className="compliance-bar">
                        <div className="compliance-fill" style={{ width: '98%' }}></div>
                    </div>
                </div>
            )}
        </aside>
    );
}

export default Sidebar;
