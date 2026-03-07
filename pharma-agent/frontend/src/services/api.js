/**
 * API Service for PharmaAgent
 * Handles all communication with the backend
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`API Error [${endpoint}]:`, error);
        throw error;
    }
}

// ==================== Chat API ====================

/**
 * Send a message to the chat agent
 */
export async function sendMessage(message, sessionId = null, customerId = null) {
    return fetchAPI('/chat', {
        method: 'POST',
        body: JSON.stringify({
            message,
            session_id: sessionId,
            customer_id: customerId,
        }),
    });
}

// ==================== Medicines API ====================

/**
 * Get all medicines with optional filters
 */
export async function getMedicines(params = {}) {
    const query = new URLSearchParams(params).toString();
    return fetchAPI(`/medicines${query ? `?${query}` : ''}`);
}

/**
 * Get a single medicine by ID
 */
export async function getMedicine(id) {
    return fetchAPI(`/medicines/${id}`);
}

/**
 * Search medicines by name
 */
export async function searchMedicines(name) {
    return fetchAPI(`/medicines/search/${encodeURIComponent(name)}`);
}

/**
 * Update medicine inventory
 */
export async function updateInventory(medicineId, stockLevel, action = 'set') {
    return fetchAPI(`/medicines/inventory/${medicineId}`, {
        method: 'PATCH',
        body: JSON.stringify({ stock_level: stockLevel, action }),
    });
}

// ==================== Orders API ====================

/**
 * Get all orders
 */
export async function getOrders(params = {}) {
    const query = new URLSearchParams(params).toString();
    return fetchAPI(`/orders${query ? `?${query}` : ''}`);
}

/**
 * Get a single order by ID
 */
export async function getOrder(id) {
    return fetchAPI(`/orders/${id}`);
}

/**
 * Create a new order
 */
export async function createOrder(orderData) {
    return fetchAPI('/orders', {
        method: 'POST',
        body: JSON.stringify(orderData),
    });
}

/**
 * Update order status
 */
export async function updateOrderStatus(orderId, status, rejectionReason = null) {
    return fetchAPI(`/orders/${orderId}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status, rejection_reason: rejectionReason }),
    });
}

// ==================== Customers API ====================

/**
 * Get all customers
 */
export async function getCustomers() {
    return fetchAPI('/customers');
}

/**
 * Get a single customer by ID
 */
export async function getCustomer(id) {
    return fetchAPI(`/customers/${id}`);
}

/**
 * Get customer order history
 */
export async function getCustomerHistory(customerId) {
    return fetchAPI(`/customers/${customerId}/history`);
}

/**
 * Upload prescription for a customer
 */
export async function uploadPrescription(customerId, file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/customers/${customerId}/prescription`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
        throw new Error(error.detail);
    }

    return response.json();
}

// ==================== Alerts API ====================

/**
 * Get all proactive refill alerts
 */
export async function getAlerts(params = {}) {
    const query = new URLSearchParams(params).toString();
    return fetchAPI(`/alerts${query ? `?${query}` : ''}`);
}

/**
 * Get pending alerts
 */
export async function getPendingAlerts() {
    return fetchAPI('/alerts/pending');
}

/**
 * Update alert status
 */
export async function updateAlertStatus(alertId, status) {
    return fetchAPI(`/alerts/${alertId}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
    });
}

// ==================== Webhook API ====================

/**
 * Trigger fulfillment webhook
 */
export async function triggerFulfillment(orderId) {
    return fetchAPI('/webhook/fulfillment', {
        method: 'POST',
        body: JSON.stringify({ order_id: orderId, action: 'fulfill' }),
    });
}

/**
 * Trigger notification webhook
 */
export async function triggerNotification(orderId, type = 'confirmation', channel = 'email') {
    return fetchAPI('/webhook/notification', {
        method: 'POST',
        body: JSON.stringify({
            order_id: orderId,
            notification_type: type,
            channel,
        }),
    });
}

/**
 * Get webhook logs
 */
export async function getWebhookLogs(limit = 50) {
    return fetchAPI(`/webhook/logs?limit=${limit}`);
}

// ==================== Refill Check API ====================

/**
 * Trigger refill prediction check
 */
export async function triggerRefillCheck() {
    return fetchAPI('/refill-check', {
        method: 'POST',
    });
}

// ==================== Health Check ====================

/**
 * Check API health
 */
export async function healthCheck() {
    return fetchAPI('/health');
}

// ==================== Cart API ====================

/**
 * Get user's cart
 */
export async function getCart(userId = 1) {
    return fetchAPI(`/cart/${userId}`);
}

/**
 * Add item to cart
 */
export async function addToCart(userId = 1, medicineId, quantity = 1) {
    return fetchAPI(`/cart/${userId}/add`, {
        method: 'POST',
        body: JSON.stringify({ medicine_id: medicineId, quantity }),
    });
}

/**
 * Remove item from cart
 */
export async function removeFromCart(userId = 1, itemId) {
    return fetchAPI(`/cart/${userId}/remove/${itemId}`, {
        method: 'DELETE',
    });
}

/**
 * Update cart item quantity
 */
export async function updateCartItem(userId = 1, itemId, quantity) {
    return fetchAPI(`/cart/${userId}/update/${itemId}?quantity=${quantity}`, {
        method: 'PATCH',
    });
}

/**
 * Checkout cart
 */
export async function checkout(userId = 1, customerId = 1) {
    return fetchAPI(`/cart/${userId}/checkout`, {
        method: 'POST',
        body: JSON.stringify({ customer_id: customerId }),
    });
}

/**
 * Clear cart
 */
export async function clearCart(userId = 1) {
    return fetchAPI(`/cart/${userId}/clear`, {
        method: 'DELETE',
    });
}

export default {
    sendMessage,
    getMedicines,
    getMedicine,
    searchMedicines,
    updateInventory,
    getOrders,
    getOrder,
    createOrder,
    updateOrderStatus,
    getCustomers,
    getCustomer,
    getCustomerHistory,
    uploadPrescription,
    getAlerts,
    getPendingAlerts,
    updateAlertStatus,
    triggerFulfillment,
    triggerNotification,
    getWebhookLogs,
    triggerRefillCheck,
    healthCheck,
    // Cart API
    getCart,
    addToCart,
    removeFromCart,
    updateCartItem,
    checkout,
    clearCart,
};
