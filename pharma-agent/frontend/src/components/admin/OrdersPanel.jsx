import React, { useState, useEffect } from 'react';
import { ShoppingCart, RefreshCw, Eye, RotateCcw, CheckCircle, Clock, XCircle, Truck } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function OrdersPanel() {
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedOrder, setSelectedOrder] = useState(null);
    const [filter, setFilter] = useState('all');

    useEffect(() => {
        loadOrders();
    }, []);

    const loadOrders = async () => {
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE}/admin/orders`);
            const data = await response.json();
            setOrders(data.orders || []);
        } catch (error) {
            console.error('Failed to load orders:', error);
        } finally {
            setLoading(false);
        }
    };

    const retryWebhook = async (orderId) => {
        try {
            await fetch(`${API_BASE}/admin/webhook-retry?order_id=${orderId}`, {
                method: 'POST'
            });
            loadOrders();
        } catch (error) {
            console.error('Webhook retry failed:', error);
        }
    };

    const updateStatus = async (orderId, newStatus) => {
        try {
            await fetch(`${API_BASE}/admin/orders/${orderId}/status?new_status=${newStatus}`, {
                method: 'PATCH'
            });
            loadOrders();
            setSelectedOrder(null);
        } catch (error) {
            console.error('Status update failed:', error);
        }
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'completed': return <CheckCircle className="text-success" />;
            case 'pending': return <Clock className="text-warning" />;
            case 'cancelled': return <XCircle className="text-danger" />;
            case 'delivered': return <Truck className="text-success" />;
            default: return <Clock className="text-muted" />;
        }
    };

    const getStatusClass = (status) => {
        switch (status) {
            case 'completed':
            case 'delivered': return 'status-success';
            case 'pending':
            case 'processing': return 'status-warning';
            case 'cancelled':
            case 'failed': return 'status-danger';
            default: return 'status-default';
        }
    };

    const filteredOrders = orders.filter(order => {
        if (filter === 'all') return true;
        return order.status === filter;
    });

    return (
        <div className="orders-panel">
            {/* Filter Bar */}
            <div className="panel-toolbar">
                <div className="filter-tabs">
                    <button
                        className={`filter-tab ${filter === 'all' ? 'active' : ''}`}
                        onClick={() => setFilter('all')}
                    >
                        All ({orders.length})
                    </button>
                    <button
                        className={`filter-tab ${filter === 'pending' ? 'active' : ''}`}
                        onClick={() => setFilter('pending')}
                    >
                        Pending
                    </button>
                    <button
                        className={`filter-tab ${filter === 'completed' ? 'active' : ''}`}
                        onClick={() => setFilter('completed')}
                    >
                        Completed
                    </button>
                </div>
                <button className="btn-secondary" onClick={loadOrders}>
                    <RefreshCw size={16} />
                    Refresh
                </button>
            </div>

            {/* Orders Table */}
            <div className="table-container">
                {loading ? (
                    <div className="loading-state">Loading orders...</div>
                ) : filteredOrders.length === 0 ? (
                    <div className="empty-state">
                        <ShoppingCart size={48} />
                        <h3>No Orders</h3>
                        <p>No orders match your filter.</p>
                    </div>
                ) : (
                    <table className="admin-table">
                        <thead>
                            <tr>
                                <th>Order ID</th>
                                <th>Customer</th>
                                <th>Medicine</th>
                                <th>Qty</th>
                                <th>Status</th>
                                <th>Webhook</th>
                                <th>Date</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredOrders.map(order => (
                                <tr key={order.id}>
                                    <td className="order-id">#{order.id}</td>
                                    <td>Customer {order.customer_id}</td>
                                    <td>Medicine #{order.medicine_id}</td>
                                    <td>{order.quantity}</td>
                                    <td>
                                        <span className={`status-badge ${getStatusClass(order.status)}`}>
                                            {getStatusIcon(order.status)}
                                            {order.status}
                                        </span>
                                    </td>
                                    <td>
                                        <span className={`status-badge ${getStatusClass(order.webhook_status)}`}>
                                            {order.webhook_status}
                                        </span>
                                    </td>
                                    <td className="date-cell">
                                        {order.created_at ? new Date(order.created_at).toLocaleDateString() : 'N/A'}
                                    </td>
                                    <td>
                                        <div className="action-btns">
                                            <button
                                                className="action-btn view"
                                                onClick={() => setSelectedOrder(order)}
                                                title="View Details"
                                            >
                                                <Eye size={14} />
                                            </button>
                                            {order.webhook_status === 'failed' && (
                                                <button
                                                    className="action-btn retry"
                                                    onClick={() => retryWebhook(order.id)}
                                                    title="Retry Webhook"
                                                >
                                                    <RotateCcw size={14} />
                                                </button>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Order Details Modal */}
            {selectedOrder && (
                <div className="modal-overlay" onClick={() => setSelectedOrder(null)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>Order #{selectedOrder.id}</h3>
                            <button className="modal-close" onClick={() => setSelectedOrder(null)}>×</button>
                        </div>
                        <div className="modal-content">
                            <div className="detail-grid">
                                <div className="detail-item">
                                    <span className="detail-label">Customer ID</span>
                                    <span className="detail-value">{selectedOrder.customer_id}</span>
                                </div>
                                <div className="detail-item">
                                    <span className="detail-label">Medicine</span>
                                    <span className="detail-value">#{selectedOrder.medicine_id}</span>
                                </div>
                                <div className="detail-item">
                                    <span className="detail-label">Quantity</span>
                                    <span className="detail-value">{selectedOrder.quantity}</span>
                                </div>
                                <div className="detail-item">
                                    <span className="detail-label">Status</span>
                                    <span className={`status-badge ${getStatusClass(selectedOrder.status)}`}>
                                        {selectedOrder.status}
                                    </span>
                                </div>
                            </div>

                            <div className="status-actions">
                                <span className="detail-label">Update Status:</span>
                                <div className="status-btns">
                                    <button onClick={() => updateStatus(selectedOrder.id, 'processing')}>Processing</button>
                                    <button onClick={() => updateStatus(selectedOrder.id, 'completed')}>Completed</button>
                                    <button onClick={() => updateStatus(selectedOrder.id, 'delivered')}>Delivered</button>
                                    <button className="danger" onClick={() => updateStatus(selectedOrder.id, 'cancelled')}>Cancel</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default OrdersPanel;
