/**
 * Role-Based Access Control (RBAC) Guard
 * 
 * Purpose: Enforce role separation across all pages
 * 
 * Principles:
 * - Buyers see only shopping pages
 * - Sellers see only business pages
 * - Admins see only governance pages
 * - No overlap, no confusion
 * 
 * Usage: Include this script in the <head> of protected pages:
 * <script src="/static/js/roleGuard.js"></script>
 */

class RoleGuard {
    constructor() {
        this.api = new ZuStoreAPI();
        this.currentPage = this.getCurrentPage();
        this.pageRules = this.definePageRules();
    }

    /**
     * Get current page name from URL
     */
    getCurrentPage() {
        const path = window.location.pathname;
        const page = path.split('/').pop() || 'index.html';
        return page;
    }

    /**
     * Define which roles can access which pages
     */
    definePageRules() {
        return {
            // Public pages (anyone can access)
            public: [
                'index.html',
                'products.html',
                'product-detail.html',
                'about.html',
                'contact.html',
                'login.html',
                'register.html',
                'cart.html'  // Cart is public, but personalized if logged in
            ],

            // Buyer-only pages
            buyer: [
                'buyer-dashboard.html',
                'checkout.html',
                'orders.html',
                'order-detail.html',
                'wishlist.html'
            ],

            // Seller-only pages
            seller: [
                'seller-dashboard.html',
                'seller-dashboard-v2.html',
                'seller-products-v2.html',
                'seller-orders-v2.html',
                'seller-earnings-v2.html',
                'seller-store-v2.html',
                'seller-disputes-v2.html',
                'seller-profile-v2.html',
                'add-product.html'
            ],

            // Admin-only pages
            admin: [
                'admin-dashboard.html',
                'admin-dashboard-v2.html',
                'admin-users-v2.html',
                'admin-user-detail.html',
                'admin-products-v2.html',
                'admin-orders-v2.html',
                'admin-disputes-v2.html',
                'admin-finances-v2.html',
                'admin-courier-payouts-v2.html',
                'admin-reports-v2.html',
                'admin-settings-v2.html',
                'admin-audit-logs-v2.html',
                'super-admin-dashboard.html'
            ],

            // Courier-only pages
            courier: [
                'courier-dashboard.html',
                'deliveries.html',
                'courier-earnings.html',
                'routes.html'
            ],

            // Shared pages (all authenticated users, content adapts)
            shared: [
                'profile.html',
                'notifications.html',
                'system-test.html',  // Debug page
                'debug-user.html'    // Debug page
            ]
        };
    }

    /**
     * Check if page requires authentication
     */
    requiresAuth() {
        const page = this.currentPage;
        return ![...this.pageRules.public].includes(page);
    }

    /**
     * Get required role for current page
     * Returns: 'BUYER' | 'SELLER' | 'ADMIN' | 'COURIER' | null (if public)
     */
    getRequiredRole() {
        const page = this.currentPage;

        if (this.pageRules.public.includes(page)) {
            return null; // Public page
        }

        if (this.pageRules.buyer.includes(page)) {
            return 'BUYER';
        }

        if (this.pageRules.seller.includes(page)) {
            return 'SELLER';
        }

        if (this.pageRules.admin.includes(page)) {
            return 'ADMIN';
        }

        if (this.pageRules.courier.includes(page)) {
            return 'COURIER';
        }

        if (this.pageRules.shared.includes(page)) {
            return 'authenticated'; // Any authenticated user
        }

        return null; // Unknown page, treat as public
    }

    /**
     * Get default landing page for each role
     */
    getDefaultPage(role) {
        const defaults = {
            BUYER: 'buyer-dashboard.html',
            SELLER: 'seller-dashboard-v2.html',
            ADMIN: 'admin-dashboard-v2.html',
            COURIER: 'courier-dashboard.html'
        };

        return defaults[role] || 'index.html';
    }

    /**
     * Check if user has permission to access current page
     */
    async checkAccess() {
        // Get required role for this page
        const requiredRole = this.getRequiredRole();

        // Public page - allow everyone
        if (requiredRole === null) {
            return true;
        }

        // Page requires authentication
        if (!this.api.isAuthenticated()) {
            console.warn('🔒 Access denied: Authentication required');
            this.redirectToLogin();
            return false;
        }

        // Shared page - allow any authenticated user
        if (requiredRole === 'authenticated') {
            return true;
        }

        // Get current user
        let user;
        try {
            user = await this.api.getProfile();
        } catch (error) {
            console.error('Failed to fetch user:', error);
            this.redirectToLogin();
            return false;
        }

        // Check if user role matches required role
        if (user.role !== requiredRole) {
            console.warn(`🚫 Access denied: Page requires ${requiredRole}, but user is ${user.role}`);
            this.redirectToRoleDashboard(user.role);
            return false;
        }

        // Access granted
        console.log(`✅ Access granted: User ${user.username} (${user.role}) can access ${this.currentPage}`);
        return true;
    }

    /**
     * Redirect to login page
     */
    redirectToLogin() {
        const returnUrl = encodeURIComponent(window.location.pathname + window.location.search);
        window.location.href = `login.html?return=${returnUrl}`;
    }

    /**
     * Redirect to role-appropriate dashboard
     */
    redirectToRoleDashboard(role) {
        const dashboard = this.getDefaultPage(role);
        
        // Show friendly message
        this.showAccessDeniedMessage(role, dashboard);

        // Redirect after brief delay
        setTimeout(() => {
            window.location.href = dashboard;
        }, 2000);
    }

    /**
     * Show access denied message
     */
    showAccessDeniedMessage(userRole, redirectPage) {
        const messages = {
            BUYER: {
                title: '🛍️ This page is for sellers',
                message: 'You\'re logged in as a buyer. Redirecting to your dashboard...',
                icon: '🛒'
            },
            SELLER: {
                title: '📊 This page is for your role',
                message: 'Redirecting to your seller dashboard...',
                icon: '🏪'
            },
            ADMIN: {
                title: '🔧 Admin Access Only',
                message: 'This page is for system administrators only.',
                icon: '⚙️'
            },
            COURIER: {
                title: '🚚 This page is for couriers',
                message: 'Redirecting to your courier dashboard...',
                icon: '📦'
            }
        };

        const config = messages[userRole] || {
            title: '🔒 Access Restricted',
            message: 'Redirecting to appropriate page...',
            icon: '🚫'
        };

        // Create overlay
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 999999;
            animation: fadeIn 0.3s ease;
        `;

        overlay.innerHTML = `
            <div style="
                background: white;
                padding: 3rem;
                border-radius: 12px;
                text-align: center;
                max-width: 400px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
                animation: slideUp 0.3s ease;
            ">
                <div style="font-size: 4rem; margin-bottom: 1rem;">${config.icon}</div>
                <h2 style="font-size: 1.5rem; margin-bottom: 1rem; color: #333;">${config.title}</h2>
                <p style="color: #666; margin-bottom: 1.5rem;">${config.message}</p>
                <div style="
                    width: 40px;
                    height: 40px;
                    border: 3px solid #f3f3f3;
                    border-top: 3px solid #3498db;
                    border-radius: 50%;
                    margin: 0 auto;
                    animation: spin 1s linear infinite;
                "></div>
            </div>
        `;

        // Add keyframe animations
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            @keyframes slideUp {
                from { transform: translateY(30px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            @keyframes spin {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);

        document.body.appendChild(overlay);
    }

    /**
     * Initialize guard and check access
     */
    async init() {
        // Skip guard for completely public pages
        if (this.currentPage === 'login.html' || this.currentPage === 'register.html') {
            return;
        }

        // Check access
        const hasAccess = await this.checkAccess();

        if (!hasAccess) {
            // Access denied - redirect handled in checkAccess()
            return false;
        }

        return true;
    }
}

/**
 * Auto-initialize on page load
 */
(async function() {
    // Wait for API to be defined
    if (typeof ZuStoreAPI === 'undefined') {
        console.error('RoleGuard: ZuStoreAPI not found. Make sure api.js is loaded first.');
        return;
    }

    const guard = new RoleGuard();
    await guard.init();
})();

/**
 * Export for manual use
 */
if (typeof window !== 'undefined') {
    window.RoleGuard = RoleGuard;
}
