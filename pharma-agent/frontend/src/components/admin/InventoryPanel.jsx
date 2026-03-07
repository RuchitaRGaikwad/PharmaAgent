import React, { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, RefreshCw, Search, X, Check, AlertTriangle } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function InventoryPanel({ onStatsChange }) {
    const [inventory, setInventory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [showModal, setShowModal] = useState(false);
    const [editingMedicine, setEditingMedicine] = useState(null);
    const [formData, setFormData] = useState({
        name: '',
        stock_level: 0,
        unit_type: 'tablets',
        price: 0,
        prescription_required: false
    });
    const [message, setMessage] = useState(null);

    useEffect(() => {
        loadInventory();
    }, []);

    const loadInventory = async () => {
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE}/admin/inventory`);
            const data = await response.json();
            setInventory(data.inventory || []);
        } catch (error) {
            console.error('Failed to load inventory:', error);
            showMessage('Failed to load inventory', 'error');
        } finally {
            setLoading(false);
        }
    };

    const showMessage = (text, type = 'success') => {
        setMessage({ text, type });
        setTimeout(() => setMessage(null), 3000);
    };

    const handleRestock = async (medicine) => {
        try {
            const response = await fetch(`${API_BASE}/admin/restock?medicine_id=${medicine.id}&quantity=50`, {
                method: 'POST'
            });
            const data = await response.json();
            if (data.success) {
                showMessage(`Restocked ${medicine.name}: +50 units`);
                loadInventory();
                onStatsChange?.();
            }
        } catch (error) {
            showMessage('Restock failed', 'error');
        }
    };

    const openAddModal = () => {
        setEditingMedicine(null);
        setFormData({
            name: '',
            stock_level: 0,
            unit_type: 'tablets',
            price: 0,
            prescription_required: false
        });
        setShowModal(true);
    };

    const openEditModal = (medicine) => {
        setEditingMedicine(medicine);
        setFormData({
            name: medicine.name,
            stock_level: medicine.stock_level,
            unit_type: medicine.unit_type || 'tablets',
            price: medicine.price || 0,
            prescription_required: medicine.prescription_required || false
        });
        setShowModal(true);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (editingMedicine) {
                // Update
                await fetch(`${API_BASE}/admin/inventory/${editingMedicine.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });
                showMessage(`Updated ${formData.name}`);
            } else {
                // Create
                await fetch(`${API_BASE}/admin/inventory`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });
                showMessage(`Added ${formData.name}`);
            }
            setShowModal(false);
            loadInventory();
            onStatsChange?.();
        } catch (error) {
            showMessage('Operation failed', 'error');
        }
    };

    const handleDelete = async (medicine) => {
        if (!confirm(`Delete ${medicine.name}?`)) return;
        try {
            await fetch(`${API_BASE}/admin/inventory/${medicine.id}`, {
                method: 'DELETE'
            });
            showMessage(`Deleted ${medicine.name}`);
            loadInventory();
            onStatsChange?.();
        } catch (error) {
            showMessage('Delete failed', 'error');
        }
    };

    const filteredInventory = inventory.filter(med =>
        med.name?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const getStatusClass = (status) => {
        switch (status) {
            case 'out_of_stock': return 'status-danger';
            case 'low': return 'status-warning';
            default: return 'status-success';
        }
    };

    return (
        <div className="inventory-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* Message Toast */}
            {message && (
                <div className={`toast ${message.type}`}>
                    {message.type === 'success' ? <Check size={16} /> : <AlertTriangle size={16} />}
                    {message.text}
                </div>
            )}

            {/* Toolbar */}
            <div className="panel-toolbar">
                <div className="search-box">
                    <Search size={18} />
                    <input
                        type="text"
                        placeholder="Search medicines..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <div className="toolbar-actions">
                    <button className="btn-secondary" onClick={loadInventory}>
                        <RefreshCw size={16} />
                        Refresh
                    </button>
                    <button className="btn-primary" onClick={openAddModal}>
                        <Plus size={16} />
                        Add Medicine
                    </button>
                </div>
            </div>

            {/* Table */}
            <div className="table-container">
                {loading ? (
                    <div className="loading-state">Loading inventory...</div>
                ) : (
                    <table className="admin-table">
                        <thead>
                            <tr>
                                <th>Medicine</th>
                                <th>Stock</th>
                                <th>Unit</th>
                                <th>Price</th>
                                <th>Rx Required</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredInventory.map(med => (
                                <tr key={med.id} className={med.status !== 'ok' ? 'row-warning' : ''}>
                                    <td className="medicine-name">
                                        {med.name || <span className="text-muted italic" style={{ fontStyle: 'italic', color: '#64748b' }}>Unknown Medicine</span>}
                                    </td>
                                    <td className={med.status !== 'ok' ? 'text-warning' : ''}>
                                        {med.stock_level}
                                    </td>
                                    <td>{med.unit_type}</td>
                                    <td>₹{med.price?.toFixed(2)}</td>
                                    <td>{med.prescription_required ? 'Yes' : 'No'}</td>
                                    <td>
                                        <span className={`status-badge ${getStatusClass(med.status)}`}>
                                            {med.status === 'out_of_stock' ? 'Out of Stock' :
                                                med.status === 'low' ? 'Low Stock' : 'In Stock'}
                                        </span>
                                    </td>
                                    <td>
                                        <div className="action-btns">
                                            <button
                                                className="action-btn restock"
                                                onClick={() => handleRestock(med)}
                                                title="Restock +50"
                                            >
                                                <RefreshCw size={14} />
                                            </button>
                                            <button
                                                className="action-btn edit"
                                                onClick={() => openEditModal(med)}
                                                title="Edit"
                                            >
                                                <Edit2 size={14} />
                                            </button>
                                            <button
                                                className="action-btn delete"
                                                onClick={() => handleDelete(med)}
                                                title="Delete"
                                            >
                                                <Trash2 size={14} />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Modal */}
            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>{editingMedicine ? 'Edit Medicine' : 'Add Medicine'}</h3>
                            <button className="modal-close" onClick={() => setShowModal(false)}>
                                <X size={20} />
                            </button>
                        </div>
                        <form onSubmit={handleSubmit} className="modal-form">
                            <div className="form-group">
                                <label>Medicine Name</label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    required
                                />
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Stock Level</label>
                                    <input
                                        type="number"
                                        value={formData.stock_level}
                                        onChange={(e) => setFormData({ ...formData, stock_level: parseInt(e.target.value) })}
                                        min="0"
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Unit Type</label>
                                    <select
                                        value={formData.unit_type}
                                        onChange={(e) => setFormData({ ...formData, unit_type: e.target.value })}
                                    >
                                        <option value="tablets">Tablets</option>
                                        <option value="capsules">Capsules</option>
                                        <option value="ml">ml</option>
                                        <option value="bottles">Bottles</option>
                                    </select>
                                </div>
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Price (₹)</label>
                                    <input
                                        type="number"
                                        value={formData.price}
                                        onChange={(e) => setFormData({ ...formData, price: parseFloat(e.target.value) })}
                                        step="0.01"
                                        min="0"
                                    />
                                </div>
                                <div className="form-group checkbox-group">
                                    <label>
                                        <input
                                            type="checkbox"
                                            checked={formData.prescription_required}
                                            onChange={(e) => setFormData({ ...formData, prescription_required: e.target.checked })}
                                        />
                                        Prescription Required
                                    </label>
                                </div>
                            </div>
                            <div className="modal-actions">
                                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>
                                    Cancel
                                </button>
                                <button type="submit" className="btn-primary">
                                    {editingMedicine ? 'Update' : 'Add'} Medicine
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

export default InventoryPanel;
