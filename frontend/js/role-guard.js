/**
 * Role-Based Access Control Guards
 * Include this in every protected page to enforce role-based access
 */

const RoleGuard = {
    /**
     * Check if current user has required role
     * @param {string|string[]} allowedRoles - Single role or array of allowed roles
     * @param {string} redirectUrl - Where to redirect if unauthorized (optional)
     */
    async checkAccess(allowedRoles, redirectUrl = null) {
        try {
            // Check authentication first
            if (!api.isAuthenticated()) {
                window.location.href = 'login.html';
                return false;
            }

            // Get user profile
            const profile = await api.getProfile();
            
            // Normalize allowedRoles to array
            const roles = Array.isArray(allowedRoles) ? allowedRoles : [allowedRoles];
            
            // Check for super admin access (superusers can access everything except explicitly restricted)
            const isSuperAdmin = profile.is_superuser;
            const userRole = profile.role;
            
            // Super admins get special treatment
            if (isSuperAdmin && roles.includes('SUPER_ADMIN')) {
                return true;
            }
            
            // Check if user's role is in allowed roles
            if (roles.includes(userRole)) {
                return true;
            }
            
            // Unauthorized - redirect to appropriate dashboard
            console.warn(`Access denied. User role: ${userRole}, Required: ${roles.join(', ')}`);
            
            if (redirectUrl) {
                window.location.href = redirectUrl;
            } else {
                window.location.href = this.getDashboardForRole(isSuperAdmin ? 'SUPER_ADMIN' : userRole);
            }
            
            return false;
            
        } catch (err) {
            console.error('Access check failed:', err);
            window.location.href = 'login.html';
            return false;
        }
    },
    
    /**
     * Get the appropriate dashboard URL for a role
     * @param {string} role - User role
     * @returns {string} Dashboard URL
     */
    getDashboardForRole(role) {
        const dashboards = {
            'SUPER_ADMIN': 'super-admin-dashboard.html',
            'ADMIN': 'admin-dashboard-v2.html',
            'SELLER': 'seller-dashboard-v2.html',
            'BUYER': 'buyer-dashboard.html',
            'COURIER': 'courier-dashboard.html'
        };
        return dashboards[role] || 'index.html';
    },
    
    /**
     * Convenience methods for specific roles
     */
    requireSuperAdmin() {
        return this.checkAccess('SUPER_ADMIN');
    },
    
    requireAdmin() {
        return this.checkAccess('ADMIN');
    },
    
    requireSeller() {
        return this.checkAccess('SELLER');
    },
    
    requireBuyer() {
        return this.checkAccess('BUYER');
    },
    
    requireCourier() {
        return this.checkAccess('COURIER');
    },
    
    /**
     * Allow multiple roles
     */
    requireAnyRole(...roles) {
        return this.checkAccess(roles);
    }
};

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RoleGuard;
}
