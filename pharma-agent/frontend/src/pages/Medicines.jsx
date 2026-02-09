import React, { useState, useEffect, useRef } from 'react';
import { Search, Filter, ShoppingCart, Plus, Minimize2, AlertTriangle, Shield, Check, Info, X, ChevronDown, Lock, RefreshCw } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { getMedicines, addToCart, getCart, healthCheck, getCustomer, uploadPrescription } from '../services/api';
import './Medicines.css';

function Medicines() {
    const { t } = useTranslation();
    const [medicines, setMedicines] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [cartCount, setCartCount] = useState(0);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('All');
    const [sortBy, setSortBy] = useState('none');
    const [isRxVerified, setIsRxVerified] = useState(false);
    const fileInputRef = useRef(null);

    // Modal state
    const [selectedMedicine, setSelectedMedicine] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    // Cart sidebar state
    const [isCartOpen, setIsCartOpen] = useState(false);
    const [cartItems, setCartItems] = useState([]);
    const [cartTotal, setCartTotal] = useState(0);
    const [cartLoading, setCartLoading] = useState(false);

    // Categories
    const categories = ['All', 'Pain Relief', 'Antibiotics', 'Diabetes', 'Blood Pressure', 'Digestive Health', 'Allergy', 'Cold & Flu', 'Vitamins'];

    const getCategoryLabel = (cat) => {
        const key = cat.toLowerCase().replace(/ & /g, '_and_').replace(/ /g, '_');
        return t(`medicines.categories.${key}`, cat);
    };

    useEffect(() => {
        loadMedicines();
        loadCart();
        loadCustomerStatus();
    }, []);

    const loadCustomerStatus = async () => {
        try {
            const customer = await getCustomer(1); // Default user ID 1
            setIsRxVerified(customer.has_verified_prescription);
        } catch (err) {
            console.error('Failed to load customer status:', err);
        }
    };

    const loadMedicines = async () => {
        setLoading(true);
        try {
            // Build query params
            const params = {};
            if (searchTerm) params.search = searchTerm;
            if (selectedCategory !== 'All') params.category = selectedCategory;
            if (sortBy !== 'none') params.sort = sortBy;

            const data = await getMedicines(params);
            setMedicines(data);
        } catch (err) {
            console.error('Failed to load medicines:', err);
            setError(t('medicines.error_load') || 'Failed to load medicines. Please try again later.');
        } finally {
            setLoading(false);
        }
    };

    const loadCart = async () => {
        try {
            const cart = await getCart(1); // Default user ID 1
            setCartItems(cart.items || []);
            setCartCount(cart.total_items || 0);
            setCartTotal(cart.total_price || 0);
        } catch (err) {
            console.error('Failed to load cart:', err);
        }
    };

    // Debounce search
    useEffect(() => {
        const timer = setTimeout(() => {
            loadMedicines();
        }, 500);
        return () => clearTimeout(timer);
    }, [searchTerm, selectedCategory, sortBy]);

    const handleAddToCart = async (medicine) => {
        if (medicine.stock_level <= 0) return;

        try {
            await addToCart(1, medicine.id, 1);
            showToast(t('medicines.toast_added', { name: medicine.name }), 'success');
            loadCart(); // Refresh cart

            // Close modal if open
            if (isModalOpen) setIsModalOpen(false);
        } catch (err) {
            showToast(err.message || t('medicines.toast_add_failed'), 'error');
        }
    };

    const openMedicineDetails = (medicine) => {
        setSelectedMedicine(medicine);
        setIsModalOpen(true);
    };

    // Toast notification helper
    const showToast = (message, type = 'info') => {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            ${type === 'success' ? '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>' : ''}
            ${type === 'error' ? '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>' : ''}
            <span>${message}</span>
        `;

        const container = document.querySelector('.toast-container') || createToastContainer();
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    };

    const createToastContainer = () => {
        const container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
        return container;
    };

    const updateCartItemQty = async (itemId, newQty) => {
        if (newQty < 1) return;
        try {
            // Optimistic update
            const updatedItems = cartItems.map(item =>
                item.id === itemId ? { ...item, quantity: newQty } : item
            );
            setCartItems(updatedItems);

            // API call
            await import('../services/api').then(mod => mod.updateCartItem(1, itemId, newQty));
            loadCart(); // Refresh totals
        } catch (err) {
            console.error('Failed to update quantity:', err);
            loadCart(); // Revert on error
            showToast(t('medicines.toast_update_failed') || 'Failed to update quantity', 'error');
        }
    };

    const handleRemoveFromCart = async (itemId) => {
        try {
            // Optimistic update
            const updatedItems = cartItems.filter(item => item.id !== itemId);
            setCartItems(updatedItems);

            // API call
            await import('../services/api').then(mod => mod.removeFromCart(1, itemId));
            loadCart(); // Refresh totals
            showToast(t('medicines.toast_removed'), 'success');
        } catch (err) {
            console.error('Failed to remove item:', err);
            loadCart(); // Revert on error
            showToast(t('medicines.toast_remove_failed'), 'error');
        }
    };

    const handleUploadClick = () => {
        if (fileInputRef.current) {
            fileInputRef.current.click();
        }
    };

    const handleFileChange = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        // Check file type
        if (!file.type.match('image.*') && file.type !== 'application/pdf') {
            showToast(t('medicines.toast_file_type_error'), 'error');
            return;
        }

        try {
            showToast(t('medicines.toast_uploading'), 'info');
            const result = await uploadPrescription(1, file); // Customer ID 1

            if (result.success) {
                showToast(t('medicines.toast_upload_success'), 'success');
                setIsRxVerified(true);
                // Refresh medicines to update locks if logic depended on it
            }
        } catch (err) {
            console.error('Upload failed:', err);
            showToast(t('medicines.toast_upload_failed'), 'error');
        }

        // Reset input
        event.target.value = null;
    };

    const handleCheckout = async () => {
        setCartLoading(true);
        try {
            // Import checkout function dynamically to ensure it's loaded
            const api = await import('../services/api');
            const result = await api.checkout(1, 1); // User ID 1, Customer ID 1

            if (result.success) {
                showToast(result.message, 'success');
                setIsCartOpen(false);
                loadCart();
                loadMedicines(); // Update stock levels
            } else {
                if (result.blocked) {
                    showToast(t('medicines.checkout_blocked_safety'), 'error');
                    // Show blocked items in toast or modal (could be improved)
                    if (result.blocked_items && result.blocked_items.length > 0) {
                        setTimeout(() => showToast(result.blocked_items[0], 'error'), 500);
                    }
                } else {
                    showToast(result.message || t('medicines.checkout_failed'), 'error');
                }
            }
        } catch (err) {
            console.error('Checkout error:', err);
            showToast(err.message || t('medicines.checkout_failed'), 'error');
        } finally {
            setCartLoading(false);
        }
    };

    return (
        <div className="medicines-page">
            <div className="medicines-header">
                <h1>
                    <span>💊</span> {t('medicines.title')}
                </h1>

                <button className="cart-badge-btn" onClick={() => setIsCartOpen(true)}>
                    <ShoppingCart size={20} />
                    <span>{t('common.cart') || 'Cart'}</span>
                    {cartCount > 0 && <span className="cart-count">{cartCount}</span>}
                </button>
            </div>

            <div className="search-filter-bar">
                <div className="search-box">
                    <Search size={18} />
                    <input
                        type="text"
                        placeholder={t('medicines.search_placeholder')}
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>

                {/* Hidden File Input */}
                <input
                    type="file"
                    ref={fileInputRef}
                    style={{ display: 'none' }}
                    onChange={handleFileChange}
                    accept="image/*,.pdf"
                />

                <select
                    className="filter-dropdown"
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                >
                    <option value="none">{t('medicines.sort_default')}</option>
                    <option value="price_asc">{t('medicines.sort_price_low')}</option>
                    <option value="price_desc">{t('medicines.sort_price_high')}</option>
                    <option value="name_asc">{t('medicines.sort_name_az')}</option>
                </select>
            </div>

            <div className="category-chips">
                {categories.map(cat => (
                    <button
                        key={cat}
                        className={`category-chip ${selectedCategory === cat ? 'active' : ''}`}
                        onClick={() => setSelectedCategory(cat)}
                    >
                        {getCategoryLabel(cat)}
                    </button>
                ))}
            </div>

            {loading ? (
                <div className="loading-state">
                    <div className="loading-spinner">
                        <RefreshCw size={32} color="#3b82f6" />
                    </div>
                    <p>{t('common.loading')}</p>
                </div>
            ) : error ? (
                <div className="empty-state">
                    <AlertTriangle size={48} color="#ef4444" />
                    <h3>{t('common.error')}</h3>
                    <p>{error}</p>
                    <button className="btn-details" onClick={loadMedicines} style={{ marginTop: 16 }}>
                        {t('common.retry')}
                    </button>
                </div>
            ) : medicines.length === 0 ? (
                <div className="empty-state">
                    <Search size={48} color="#64748b" />
                    <h3>{t('medicines.no_results')}</h3>
                    <p>{t('medicines.no_results_hint') || 'Try adjusting your search or filters'}</p>
                </div>
            ) : (
                <div className="medicine-grid">
                    {medicines.map(medicine => (
                        <div
                            key={medicine.id}
                            className={`medicine-card ${medicine.prescription_required ? 'prescription-required' : ''} ${medicine.stock_level === 0 ? 'out-of-stock' : ''}`}
                        >
                            {/* Prescription Required Badge/Overlay */}
                            {medicine.prescription_required && !isRxVerified && (
                                <div className="prescription-lock">
                                    <Lock size={24} />
                                    <span>{t('medicines.rx_required')}</span>
                                    <button className="btn-upload-rx" onClick={handleUploadClick}>{t('medicines.upload_rx')}</button>
                                </div>
                            )}

                            <div className="card-header">
                                <div className="medicine-icon">
                                    <img
                                        src={`https://ui-avatars.com/api/?name=${medicine.name}&background=random&color=fff&size=52&font-size=0.4`}
                                        alt={medicine.name}
                                        style={{ borderRadius: 12 }}
                                        onError={(e) => { e.target.style.display = 'none'; e.target.parentElement.innerHTML = '💊' }}
                                    />
                                </div>
                                <div className="medicine-info">
                                    <h3 className="medicine-name">{medicine.name}</h3>
                                    <span className="medicine-dosage">{medicine.dosage_info}</span>
                                </div>
                            </div>

                            <div className="card-badges">
                                {medicine.prescription_required ? (
                                    <span className="badge badge-rx">{t('medicines.badge_rx')}</span>
                                ) : (
                                    <span className="badge badge-otc">{t('medicines.badge_otc')}</span>
                                )}
                                <span className="badge badge-category">{medicine.category || 'General'}</span>
                            </div>

                            <div className="stock-indicator">
                                <div className="stock-dots">
                                    <div className={`stock-dot filled ${getStockStatus(medicine.stock_level)}`}></div>
                                    <div className={`stock-dot ${medicine.stock_level > 20 ? 'filled ' + getStockStatus(medicine.stock_level) : ''}`}></div>
                                    <div className={`stock-dot ${medicine.stock_level > 50 ? 'filled ' + getStockStatus(medicine.stock_level) : ''}`}></div>
                                </div>
                                <span className={`stock-text ${getStockStatus(medicine.stock_level)}`}>
                                    {medicine.stock_level === 0 ? t('medicines.out_of_stock') :
                                        medicine.stock_level < 20 ? t('medicines.low_stock') : t('medicines.in_stock')}
                                </span>
                            </div>

                            <div className="medicine-price">
                                <span className="currency">$</span>
                                {medicine.price.toFixed(2)}
                            </div>

                            <div className="card-actions">
                                <button
                                    className="btn-details"
                                    onClick={() => openMedicineDetails(medicine)}
                                >
                                    {t('medicines.details')}
                                </button>
                                <button
                                    className="btn-add-cart"
                                    disabled={medicine.stock_level === 0 || (medicine.prescription_required && !isRxVerified)}
                                    onClick={() => handleAddToCart(medicine)}
                                >
                                    <Plus size={18} />
                                    {t('medicines.add')}
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Quick Preview Modal */}
            <div className={`modal-overlay ${isModalOpen ? 'active' : ''}`} onClick={(e) => {
                if (e.target.classList.contains('modal-overlay')) setIsModalOpen(false);
            }}>
                <div className="modal-content">
                    {selectedMedicine && (
                        <>
                            <div className="modal-header">
                                <h2>{selectedMedicine.name}</h2>
                                <button className="modal-close" onClick={() => setIsModalOpen(false)}>
                                    <X size={20} />
                                </button>
                            </div>
                            <div className="modal-body">
                                <div className="modal-info-row">
                                    <label>{t('medicines.price')}</label>
                                    <span style={{ color: '#22c55e', fontSize: 18, fontWeight: 700 }}>${selectedMedicine.price.toFixed(2)}</span>
                                </div>
                                <div className="modal-info-row">
                                    <label>{t('medicines.dosage')}</label>
                                    <span>{selectedMedicine.dosage_info}</span>
                                </div>
                                <div className="modal-info-row">
                                    <label>{t('medicines.unit_type')}</label>
                                    <span>{selectedMedicine.unit_type}</span>
                                </div>
                                <div className="modal-info-row">
                                    <label>{t('medicines.category')}</label>
                                    <span>{selectedMedicine.category}</span>
                                </div>

                                {selectedMedicine.safety_notes && (
                                    <div className="safety-warning">
                                        <Shield size={20} />
                                        <div>
                                            <strong style={{ color: '#ef4444', display: 'block', marginBottom: 4 }}>{t('medicines.safety_info')}</strong>
                                            <p>{selectedMedicine.safety_notes}</p>
                                        </div>
                                    </div>
                                )}
                            </div>
                            <div className="modal-footer">
                                <button
                                    className="btn-add-cart"
                                    disabled={selectedMedicine.stock_level === 0 || (selectedMedicine.prescription_required && !isRxVerified)}
                                    onClick={() => handleAddToCart(selectedMedicine)}
                                >
                                    {selectedMedicine.stock_level === 0 ? t('medicines.out_of_stock') :
                                        (selectedMedicine.prescription_required && !isRxVerified) ? t('medicines.rx_required') : t('medicines.add_to_cart')}
                                </button>
                            </div>
                        </>
                    )}
                </div>
            </div>

            {/* Cart Sidebar */}
            <div className={`cart-overlay ${isCartOpen ? 'open' : ''}`} onClick={() => setIsCartOpen(false)}></div>
            <div className={`cart-sidebar ${isCartOpen ? 'open' : ''}`}>
                <div className="cart-sidebar-header">
                    <h2>
                        <ShoppingCart size={20} />
                        {t('medicines.your_cart')}
                    </h2>
                    <button className="modal-close" onClick={() => setIsCartOpen(false)}>
                        <X size={20} />
                    </button>
                </div>

                <div className="cart-items-list">
                    {cartItems.length === 0 ? (
                        <div className="cart-empty">
                            <ShoppingCart size={48} />
                            <p>{t('medicines.cart_empty')}</p>
                            <button className="btn-details" onClick={() => setIsCartOpen(false)}>
                                {t('medicines.start_shopping')}
                            </button>
                        </div>
                    ) : (
                        cartItems.map(item => (
                            <div key={item.id} className="cart-item">
                                <div className="cart-item-info">
                                    <h4>{item.medicine_name}</h4>
                                    <p>${item.price.toFixed(2)} x {item.quantity}</p>
                                </div>
                                <div className="cart-item-actions">
                                    <button
                                        className="qty-btn"
                                        onClick={() => updateCartItemQty(item.id, item.quantity - 1)}
                                    >
                                        -
                                    </button>
                                    <span className="cart-item-qty">{item.quantity}</span>
                                    <button
                                        className="qty-btn"
                                        onClick={() => updateCartItemQty(item.id, item.quantity + 1)}
                                    >
                                        +
                                    </button>
                                    <button
                                        className="btn-remove"
                                        onClick={() => handleRemoveFromCart(item.id)}
                                    >
                                        <X size={16} />
                                    </button>
                                </div>
                            </div>
                        ))
                    )}
                </div>

                {cartItems.length > 0 && (
                    <div className="cart-summary">
                        <div className="cart-total">
                            <span>{t('medicines.total')}</span>
                            <strong>${cartTotal.toFixed(2)}</strong>
                        </div>
                        <button
                            className="btn-checkout"
                            onClick={handleCheckout}
                            disabled={cartLoading}
                        >
                            {cartLoading ? (
                                <RefreshCw size={18} className="loading-spinner" />
                            ) : (
                                <>{t('medicines.checkout')} <Shield size={18} style={{ marginLeft: 8 }} /></>
                            )}
                        </button>
                    </div>
                )}
            </div>

        </div>
    );
}

// Helper to determine stock status class
function getStockStatus(level) {
    if (level === 0) return 'out';
    if (level < 20) return 'low';
    if (level < 50) return 'medium';
    return 'high';
}

export default Medicines;
