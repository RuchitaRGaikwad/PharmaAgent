import React, { useState, useEffect } from 'react';
import { Search, AlertTriangle, RefreshCw } from 'lucide-react';
import { getMedicines } from '../services/api';

function Medicines() {
    const [medicines, setMedicines] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [category, setCategory] = useState('all');

    useEffect(() => {
        loadMedicines();
    }, []);

    const loadMedicines = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await getMedicines();
            setMedicines(data);
        } catch (err) {
            setError('Connection error. Backend may be offline.');
        } finally {
            setLoading(false);
        }
    };

    const filteredMedicines = medicines.filter(med => {
        const matchesSearch = med.name.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesCategory = category === 'all' ||
            (category === 'prescription' && med.prescription_required) ||
            (category === 'otc' && !med.prescription_required);
        return matchesSearch && matchesCategory;
    });

    return (
        <div className="page-container">
            <div className="page-header">
                <h1 className="page-title">💊 Medicines</h1>
                <p className="page-subtitle">Browse and order medicines with real-time safety verification</p>
            </div>

            <div className="search-bar">
                <div className="search-input-wrapper">
                    <Search size={18} />
                    <input
                        type="text"
                        className="search-input"
                        placeholder="Search medicines..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <select
                    className="filter-select"
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                >
                    <option value="all">All Categories</option>
                    <option value="prescription">Prescription Only</option>
                    <option value="otc">Over the Counter</option>
                </select>
            </div>

            {error && (
                <div className="alert-banner">
                    <div className="alert-content">
                        <AlertTriangle size={18} />
                        {error}
                    </div>
                    <button className="retry-btn" onClick={loadMedicines}>
                        Retry
                    </button>
                </div>
            )}

            {loading ? (
                <div style={{ textAlign: 'center', padding: '60px' }}>
                    <RefreshCw size={32} style={{ animation: 'spin 1s linear infinite', color: 'var(--accent-primary)' }} />
                    <p style={{ marginTop: '16px', color: 'var(--text-muted)' }}>Loading medicines...</p>
                </div>
            ) : (
                <div className="cards-grid">
                    {filteredMedicines.map((medicine) => (
                        <div key={medicine.id} className="medicine-card">
                            <div className="medicine-name">{medicine.name}</div>
                            <div className="medicine-info">
                                <span>Stock: {medicine.stock_level} {medicine.unit_type}</span>
                                <span>${medicine.price.toFixed(2)}</span>
                            </div>
                            <div style={{ marginTop: '12px' }}>
                                {medicine.prescription_required ? (
                                    <span className="badge badge-warning">Prescription Required</span>
                                ) : (
                                    <span className="badge badge-success">OTC</span>
                                )}
                                {medicine.stock_level < 20 && medicine.stock_level > 0 && (
                                    <span className="badge badge-warning" style={{ marginLeft: '8px' }}>Low Stock</span>
                                )}
                                {medicine.stock_level === 0 && (
                                    <span className="badge badge-danger" style={{ marginLeft: '8px' }}>Out of Stock</span>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {!loading && !error && filteredMedicines.length === 0 && (
                <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
                    No medicines found matching your search.
                </div>
            )}
        </div>
    );
}

export default Medicines;
