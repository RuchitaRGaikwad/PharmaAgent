import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { RefreshCw, Package, Clock, CheckCircle, XCircle } from 'lucide-react';
import { getOrders } from '../services/api';

function Orders() {
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);

    const { t } = useTranslation();

    useEffect(() => {
        loadOrders();
    }, []);

    const loadOrders = async () => {
        try {
            const data = await getOrders();
            setOrders(data);
        } catch (err) {
            console.error('Failed to load orders:', err);
        } finally {
            setLoading(false);
        }
    };

    const getStatusText = (status) => {
        switch (status) {
            case 'pending': return t('orders.pending');
            case 'approved': return t('orders.completed');
            case 'fulfilled': return t('orders.completed');
            case 'rejected': return t('orders.cancelled');
            default: return status;
        }
    };

    const getStatusBadge = (status) => {
        const statusMap = {
            pending: { class: 'badge-warning', icon: Clock },
            approved: { class: 'badge-info', icon: CheckCircle },
            fulfilled: { class: 'badge-success', icon: CheckCircle },
            rejected: { class: 'badge-danger', icon: XCircle }
        };
        const config = statusMap[status] || statusMap.pending;
        const Icon = config.icon;
        return (
            <span className={`badge ${config.class}`}>
                <Icon size={12} style={{ marginRight: '4px' }} />
                {getStatusText(status)}
            </span>
        );
    };

    return (
        <div className="page-container">
            <div className="page-header">
                <h1 className="page-title">📦 {t('orders.title')}</h1>
                <p className="page-subtitle">{t('orders.subtitle')}</p>
            </div>

            {loading ? (
                <div style={{ textAlign: 'center', padding: '60px' }}>
                    <RefreshCw size={32} style={{ animation: 'spin 1s linear infinite', color: 'var(--accent-primary)' }} />
                </div>
            ) : orders.length === 0 ? (
                <div style={{
                    textAlign: 'center',
                    padding: '60px',
                    background: 'var(--bg-tertiary)',
                    borderRadius: '12px'
                }}>
                    <Package size={48} style={{ color: 'var(--text-muted)', marginBottom: '16px' }} />
                    <p style={{ color: 'var(--text-muted)' }}>{t('orders.no_orders')}</p>
                </div>
            ) : (
                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>{t('orders.order_id')}</th>
                                <th>{t('orders.medicine')}</th>
                                <th>{t('orders.quantity')}</th>
                                <th>{t('orders.total')}</th>
                                <th>{t('orders.status')}</th>
                                <th>{t('orders.date')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {orders.map((order) => (
                                <tr key={order.id}>
                                    <td><strong>#{order.id}</strong></td>
                                    <td>{order.medicine_name || `Medicine #${order.medicine_id}`}</td>
                                    <td>{order.quantity}</td>
                                    <td>${order.total_price.toFixed(2)}</td>
                                    <td>{getStatusBadge(order.status)}</td>
                                    <td>{new Date(order.created_at).toLocaleDateString()}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}

export default Orders;
