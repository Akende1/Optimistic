/**
 * Optimistic API Client
 * 
 * Purpose: Centralized HTTP client for all backend communication
 * 
 * Why centralized?
 * - Single source of truth for API calls
 * - Consistent authentication across all requests
 * - Unified error handling
 * - Easy to add logging, retry, loading states
 * - DRY: Don't repeat fetch() setup everywhere
 * 
 * Authentication Flow:
 * 1. User logs in → Backend returns {access, refresh} tokens
 * 2. Store both tokens in localStorage
 * 3. Every API call: Authorization: Bearer <access_token>
 * 4. Access expires (1 hour) → Use refresh to get new access
 * 5. Refresh expires (7 days) → Redirect to login
 * 
 * Token Storage:
 * - localStorage: Persists across browser sessions
 * - Pro: User stays logged in after closing browser
 * - Con: Vulnerable to XSS attacks
 * - Production: Consider httpOnly cookies instead
 * 
 * Security Considerations:
 * - Always use HTTPS in production (prevent token theft)
 * - Sanitize all user input (prevent XSS)
 * - Consider httpOnly cookies (immune to XSS)
 * - Token rotation enabled (limits stolen token lifespan)
 */

const API_BASE = `${window.location.origin}/api/v1`;

class ZuStoreAPI {
    /**
     * Initialize API client and load stored tokens
     */
    constructor() {
        // Load tokens from localStorage (if user was logged in)
        this.accessToken = localStorage.getItem('access_token');
        this.refreshToken = localStorage.getItem('refresh_token');
    }

    /**
     * Build HTTP headers for requests
     * @param {boolean} includeAuth - Include Authorization header?
     * @returns {Object} Headers object
     */
    getHeaders(includeAuth = true) {
        const headers = {
            'Content-Type': 'application/json',  // All requests send JSON
        };
        // Add JWT token if available and required
        if (includeAuth && this.accessToken) {
            headers['Authorization'] = `Bearer ${this.accessToken}`;
        }
        return headers;
    }

    extractErrorMessage(data) {
        if (!data) return 'API request failed';
        if (data.error?.message) return data.error.message;
        if (typeof data.error === 'string') return data.error;
        if (data.detail) return typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
        if (data.message) return data.message;
        return 'API request failed';
    }

    /**
     * Generic fetch wrapper with error handling and token refresh
     * @param {string} endpoint - API endpoint (e.g., '/products/')
     * @param {Object} options - fetch() options
     * @returns {Promise} Resolved JSON or throws error
     */
    async request(endpoint, options = {}) {
        const url = `${API_BASE}${endpoint}`;
        
        // Handle FormData differently from JSON
        let headers;
        let body;
        
        if (options.isFormData) {
            // For FormData, only set Authorization header (browser sets Content-Type with boundary)
            headers = {};
            if (this.accessToken && options.auth !== false) {
                headers['Authorization'] = `Bearer ${this.accessToken}`;
            }
            body = options.body; // FormData object
        } else {
            // For JSON requests
            headers = this.getHeaders(options.auth !== false);
            body = options.body;
        }
        
        const config = {
            method: options.method || 'GET',
            headers: headers,
            body: body
        };

        try {
            let response = await fetch(url, config);
            
            // Handle token expiration - try to refresh and retry
            if (response.status === 401 && this.refreshToken && options.auth !== false) {
                console.log('Token expired, attempting refresh...');
                const refreshed = await this.refreshAccessToken();
                if (refreshed) {
                    // Retry request with new token
                    if (options.isFormData) {
                        config.headers = { 'Authorization': `Bearer ${this.accessToken}` };
                    } else {
                        config.headers = this.getHeaders(true);
                    }
                    response = await fetch(url, config);
                }
            }

            // Parse response
            let data;
            try {
                data = await response.json();
            } catch (e) {
                data = { error: 'Invalid response from server' };
            }

            // Handle HTTP errors and standardized envelope errors
            if (!response.ok || data?.success === false) {
                const errorMessage = this.extractErrorMessage(data);
                const error = new Error(errorMessage);
                error.status = response.status;
                error.data = data;
                throw error;
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            
            // Auto-logout on authentication failures
            if (error.status === 401 || error.status === 403) {
                console.warn('Authentication failed, logging out...');
                // Only logout if we're on a protected endpoint
                if (options.auth !== false && !endpoint.includes('/auth/')) {
                    this.logout();
                }
            }
            
            throw error;
        }
    }

    /**
     * Refresh access token using refresh token
     * @returns {Promise<boolean>} True if refresh succeeded
     */
    async refreshAccessToken() {
        if (!this.refreshToken) {
            return false;
        }

        try {
            const response = await fetch(`${API_BASE}/auth/token/refresh/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh: this.refreshToken })
            });

            if (response.ok) {
                const data = await response.json();
                const tokenPayload = data?.data || data;
                this.accessToken = tokenPayload.access;
                localStorage.setItem('access_token', tokenPayload.access);
                console.log('Token refreshed successfully');
                return true;
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
        }

        // Refresh failed - clear tokens
        this.logout();
        return false;
    }

    // Auth methods
    async register(username, email, password, role = 'BUYER') {
        const data = await this.request('/auth/register/', {
            method: 'POST',
            auth: false,
            body: JSON.stringify({ username, email, password, role })
        });
        const payload = data?.data || data;
        this.setTokens(payload.access, payload.refresh);
        return data;
    }

    async login(username, password) {
        const data = await this.request('/auth/login/', {
            method: 'POST',
            auth: false,
            body: JSON.stringify({ username, password })
        });
        const payload = data?.data || data;
        this.setTokens(payload.access, payload.refresh);
        return data;
    }

    logout() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        this.accessToken = null;
        this.refreshToken = null;
        window.location.href = 'index.html';
    }

    setTokens(access, refresh) {
        this.accessToken = access;
        this.refreshToken = refresh;
        localStorage.setItem('access_token', access);
        localStorage.setItem('refresh_token', refresh);
    }

    isAuthenticated() {
        return !!this.accessToken;
    }

    // Product methods
    async getCategories() {
        return this.request('/categories/', { auth: false });
    }

    async getProducts(filters = {}) {
        const params = new URLSearchParams(filters);
        return this.request(`/products/?${params}`, { auth: false });
    }

    async getProduct(id) {
        return this.request(`/products/${id}/`, { auth: false });
    }

    async createProduct(productData) {
        return this.request('/products/', {
            method: 'POST',
            body: JSON.stringify(productData)
        });
    }

    async updateProduct(id, productData) {
        return this.request(`/products/${id}/`, {
            method: 'PATCH',
            body: JSON.stringify(productData)
        });
    }

    async uploadProductImage(productId, formData) {
        return this.request(`/products/${productId}/upload_image/`, {
            method: 'POST',
            body: formData,
            isFormData: true
        });
    }

    async submitProductForApproval(productId) {
        return this.request(`/products/${productId}/submit_for_approval/`, {
            method: 'POST'
        });
    }

    // Seller methods
    async getSellers() {
        return this.request('/sellers/', { auth: false });
    }

    async getSeller(id) {
        return this.request(`/sellers/${id}/`, { auth: false });
    }

    async getSellerProducts(id) {
        return this.request(`/sellers/${id}/products/`, { auth: false });
    }
    
    // Seller-specific authenticated endpoints
    async getSellerOrders() {
        return this.request('/sellers/orders/');
    }
    
    async getSellerAnalytics() {
        return this.request('/sellers/analytics/');
    }
    
    async updateSellerProfile(formData) {
        return this.request('/sellers/update_profile/', {
            method: 'PATCH',
            body: formData,
            isFormData: true
        });
    }

    // Notifications
    async getNotifications() {
        return this.request('/notifications/');
    }

    async markNotificationRead(id) {
        return this.request(`/notifications/${id}/read/`, { method: 'POST' });
    }

    // Reviews
    async getProductReviews(productId) {
        return this.request(`/reviews/?product=${productId}`, { auth: false });
    }

    async createReview(orderId, productId, sellerId, rating, comment) {
        return this.request('/reviews/', {
            method: 'POST',
            body: JSON.stringify({
                order: orderId,
                product: productId,
                seller: sellerId,
                rating,
                comment
            })
        });
    }

    // User Profile
    async getProfile() {
        const data = await this.request('/auth/profile/');
        return data?.data || data;
    }
    
    async updateProfilePicture(imageFile) {
        const formData = new FormData();
        formData.append('profile_picture', imageFile);
        
        return this.request('/auth/profile/picture/', {
            method: 'PATCH',
            body: formData,
            isFormData: true
        });
    }

    // Orders
    async getOrders() {
        return this.request('/orders/');
    }

    // Alias for admin to get all orders
    async getAllOrders(params = {}) {
        const queryParams = new URLSearchParams(params);
        return this.request(`/orders/?${queryParams}`);
    }

    async getOrderDetail(orderId) {
        return this.request(`/orders/${orderId}/`);
    }

    async confirmDelivery(orderId) {
        return this.request(`/orders/${orderId}/confirm_delivery/`, {
            method: 'POST'
        });
    }

    async cancelOrder(orderId, reason = '') {
        return this.request(`/orders/${orderId}/cancel/`, {
            method: 'POST',
            body: JSON.stringify({ reason })
        });
    }

    // Delivery Partners / Couriers
    async getDeliveryPartners(verified = true) {
        return this.request(`/logistics/delivery-partners/?verified=${verified}`);
    }

    async registerCourier(data) {
        return this.request('/logistics/delivery-partners/register/', {
            method: 'POST',
            auth: false,
            body: JSON.stringify(data)
        });
    }

    async getPendingCouriers() {
        return this.request('/logistics/delivery-partners/pending/');
    }

    async verifyCourier(partnerId) {
        return this.request(`/logistics/delivery-partners/${partnerId}/verify/`, {
            method: 'POST'
        });
    }

    // Locations
    async getProvinces() {
        return this.request('/logistics/locations/provinces/');
    }

    async getCities(provinceId = null) {
        const url = provinceId 
            ? `/logistics/locations/cities/?province=${provinceId}`
            : '/logistics/locations/cities/';
        return this.request(url);
    }

    async getZones(cityId) {
        return this.request(`/logistics/locations/?type=ZONE&parent=${cityId}`);
    }

    async deleteProductImage(productId, imageId) {
        return this.request(`/products/${productId}/delete_image/?image_id=${imageId}`, {
            method: 'DELETE'
        });
    }

    // Admin Dashboard
    async getSystemMetrics() {
        return this.request('/admin/metrics/');
    }

    // Admin - Get all users
    async getAllUsers(params = {}) {
        const queryParams = new URLSearchParams(params);
        return this.request(`/admin/users/?${queryParams}`);
    }

    async getUserDetail(userId) {
        return this.request(`/admin/users/${userId}/`);
    }

    // Admin - Get all products for moderation
    async getAllProducts(params = {}) {
        const queryParams = new URLSearchParams(params);
        return this.request(`/products/?${queryParams}`);
    }

    // Admin - Get recent activity (orders, users, products)
    async getRecentActivity() {
        // Fetch recent orders, users, and products to build activity feed
        const [orders, products] = await Promise.all([
            this.request('/orders/?ordering=-created_at&page_size=10'),
            this.request('/products/?ordering=-created_at&page_size=10')
        ]);
        return { orders: orders.results || [], products: products.results || [] };
    }

    // Reports
    async getGMVReport(params = {}) {
        const queryParams = new URLSearchParams(params);
        return this.request(`/admin/reports/gmv/?${queryParams}`);
    }

    async getRevenueReport(params = {}) {
        const queryParams = new URLSearchParams(params);
        return this.request(`/admin/reports/revenue/?${queryParams}`);
    }

    async getUserGrowthReport(params = {}) {
        const queryParams = new URLSearchParams(params);
        return this.request(`/admin/reports/user-growth/?${queryParams}`);
    }

    async getSellerPerformanceReport(params = {}) {
        const queryParams = new URLSearchParams(params);
        return this.request(`/admin/reports/seller-performance/?${queryParams}`);
    }

    async getProductMetricsReport(params = {}) {
        const queryParams = new URLSearchParams(params);
        return this.request(`/admin/reports/product-metrics/?${queryParams}`);
    }

    async getFinancialAuditReport(params = {}) {
        const queryParams = new URLSearchParams(params);
        return this.request(`/admin/reports/financial-audit/?${queryParams}`);
    }

    async getAuditLogsReport(params = {}) {
        const queryParams = new URLSearchParams(params);
        return this.request(`/admin/reports/audit-logs/?${queryParams}`);
    }

    downloadReport(reportType, params = {}) {
        params.format = 'csv';
        const queryParams = new URLSearchParams(params);
        const url = `${API_BASE}/admin/reports/${reportType}/?${queryParams}`;
        window.open(url, '_blank');
    }

    // Admin - Product Moderation
    async approveProduct(productId) {
        return this.request(`/admin/products/${productId}/approve/`, {
            method: 'POST'
        });
    }

    async suspendProduct(productId, reason) {
        return this.request(`/admin/products/${productId}/suspend/`, {
            method: 'POST',
            body: JSON.stringify({ reason })
        });
    }

    async flagProduct(productId, reason, severity = 'MEDIUM') {
        return this.request(`/admin/products/${productId}/flag/`, {
            method: 'POST',
            body: JSON.stringify({ reason, severity })
        });
    }

    async archiveProduct(productId) {
        return this.request(`/admin/products/${productId}/archive/`, {
            method: 'POST'
        });
    }

    // Admin - Disputes
    async getDisputes(params = {}) {
        const queryParams = new URLSearchParams(params);
        return this.request(`/admin/disputes/?${queryParams}`);
    }

    async resolveDispute(disputeId, outcome, resolution_notes) {
        return this.request(`/admin/disputes/${disputeId}/resolve/`, {
            method: 'POST',
            body: JSON.stringify({ outcome, resolution_notes })
        });
    }

    async closeDispute(disputeId) {
        return this.request(`/admin/disputes/${disputeId}/close/`, {
            method: 'POST'
        });
    }
}

// Export single instance
const api = new ZuStoreAPI();