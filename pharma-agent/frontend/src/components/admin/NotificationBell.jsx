import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Bell, Package, AlertTriangle, X, Check, ChevronDown } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function NotificationBell() {
    const [notifications, setNotifications] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const dropdownRef = useRef(null);
    const wsRef = useRef(null);

    // Load notifications on mount
    useEffect(() => {
        loadNotifications();
        loadUnreadCount();
        setupWebSocket();

        // Poll for new notifications every 30 seconds as fallback
        const pollInterval = setInterval(loadUnreadCount, 30000);

        return () => {
            clearInterval(pollInterval);
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, []);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const setupWebSocket = () => {
        try {
            const wsUrl = API_BASE.replace(/^http/, 'ws');
            const ws = new WebSocket(`${wsUrl}/notifications/ws`);

            ws.onopen = () => {
                console.log('Notification WebSocket connected');
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'stock_alert') {
                    // Refresh notifications when new alert arrives
                    loadNotifications();
                    loadUnreadCount();
                }
            };

            ws.onclose = () => {
                console.log('Notification WebSocket disconnected');
                // Reconnect after 5 seconds
                setTimeout(setupWebSocket, 5000);
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            wsRef.current = ws;

            // Send ping every 30 seconds to keep alive
            const pingInterval = setInterval(() => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send('ping');
                }
            }, 30000);

            ws.onclose = () => {
                clearInterval(pingInterval);
                setTimeout(setupWebSocket, 5000);
            };
        } catch (error) {
            console.error('Failed to setup WebSocket:', error);
        }
    };

    const loadNotifications = async () => {
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE}/notifications/stock-alerts?limit=10`);
            const data = await response.json();
            setNotifications(data.notifications || []);
        } catch (error) {
            console.error('Failed to load notifications:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadUnreadCount = async () => {
        try {
            const response = await fetch(`${API_BASE}/notifications/unread-count`);
            const data = await response.json();
            setUnreadCount(data.count || 0);
        } catch (error) {
            console.error('Failed to load unread count:', error);
        }
    };

    const markAsRead = async (notificationId) => {
        try {
            await fetch(`${API_BASE}/notifications/${notificationId}/read`, { method: 'PATCH' });
            setNotifications(prev =>
                prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
            );
            setUnreadCount(prev => Math.max(0, prev - 1));
        } catch (error) {
            console.error('Failed to mark as read:', error);
        }
    };

    const acknowledgeNotification = async (notificationId) => {
        try {
            await fetch(`${API_BASE}/notifications/${notificationId}/acknowledge`, { method: 'PATCH' });
            setNotifications(prev => prev.filter(n => n.id !== notificationId));
            setUnreadCount(prev => Math.max(0, prev - 1));
        } catch (error) {
            console.error('Failed to acknowledge:', error);
        }
    };

    const markAllRead = async () => {
        try {
            await fetch(`${API_BASE}/notifications/mark-all-read`, { method: 'POST' });
            setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
            setUnreadCount(0);
        } catch (error) {
            console.error('Failed to mark all as read:', error);
        }
    };

    const getNotificationIcon = (type) => {
        if (type === 'out_of_stock') {
            return <AlertTriangle className="notification-icon danger" size={16} />;
        }
        return <Package className="notification-icon warning" size={16} />;
    };

    const formatTime = (timestamp) => {
        if (!timestamp) return '';
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
        return date.toLocaleDateString();
    };

    return (
        <div className="notification-bell-container" ref={dropdownRef}>
            <button
                className={`notification-bell-btn ${unreadCount > 0 ? 'has-unread' : ''}`}
                onClick={() => setIsOpen(!isOpen)}
                title="Stock Alerts"
            >
                <Bell size={18} />
                {unreadCount > 0 && (
                    <span className="notification-badge">{unreadCount > 9 ? '9+' : unreadCount}</span>
                )}
            </button>

            {isOpen && (
                <div className="notification-dropdown">
                    <div className="notification-header">
                        <h4>Stock Alerts</h4>
                        {notifications.length > 0 && (
                            <button className="mark-all-btn" onClick={markAllRead}>
                                Mark all read
                            </button>
                        )}
                    </div>

                    <div className="notification-list">
                        {loading ? (
                            <div className="notification-loading">Loading...</div>
                        ) : notifications.length === 0 ? (
                            <div className="notification-empty">
                                <Bell size={32} />
                                <p>No stock alerts</p>
                            </div>
                        ) : (
                            notifications.map(notification => (
                                <div
                                    key={notification.id}
                                    className={`notification-item ${notification.is_read ? 'read' : 'unread'}`}
                                    onClick={() => !notification.is_read && markAsRead(notification.id)}
                                >
                                    {getNotificationIcon(notification.notification_type)}
                                    <div className="notification-content">
                                        <span className="notification-medicine">
                                            {notification.medicine_name}
                                        </span>
                                        <span className="notification-message">
                                            {notification.notification_type === 'out_of_stock'
                                                ? 'Out of stock!'
                                                : `Low stock: ${notification.stock_level} units`}
                                        </span>
                                        <span className="notification-time">
                                            {formatTime(notification.created_at)}
                                        </span>
                                    </div>
                                    <button
                                        className="notification-dismiss"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            acknowledgeNotification(notification.id);
                                        }}
                                        title="Dismiss"
                                    >
                                        <X size={14} />
                                    </button>
                                </div>
                            ))
                        )}
                    </div>

                    {notifications.length > 0 && (
                        <div className="notification-footer">
                            <a href="/admin" className="view-all-link">
                                View all in Admin
                                <ChevronDown size={14} style={{ transform: 'rotate(-90deg)' }} />
                            </a>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default NotificationBell;
