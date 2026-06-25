/**
 * Optimistic Unified Navigation System
 * Handles role-based links and clean URL routing.
 */
class OptimisticNavigation {
    constructor() {
        this.navContainer = document.querySelector('.nav-container');
        this.init();
    }

    async init() {
        const user = this.getStoredUser();
        const role = user ? user.role : 'GUEST';
        this.setupFavicon();
        
        // Render base navigation
        this.render(role, user);
        
        // Realtime sync with API
        if (user) {
            await this.updateRealtimeBadges();
        }
    }

    setupFavicon() {
        let link = document.querySelector("link[rel~='icon']");
        if (!link) {
            link = document.createElement('link');
            link.rel = 'icon';
            document.head.appendChild(link);
        }
        link.href = '/static/images/brand/favicon-purple.png';
    }

    async updateRealtimeBadges() {
        try {
            const api = new OptimisticAPI();
            // Real-time API calls instead of placeholders
            const [cart, notifications] = await Promise.all([
                api.get('/api/cart/count/'),
                api.get('/api/notifications/unread-count/')
            ]);
            
            const cartBadge = document.querySelector('.badge-cart');
            const notifBadge = document.querySelector('.badge-notif');
            
            if (cartBadge) cartBadge.innerText = cart.count || 0;
            if (notifBadge) notifBadge.innerText = notifications.count || 0;
        } catch (e) {
            console.warn("Realtime data fetch failed. Using local state.");
        }
    }

    getStoredUser() {
        try {
            return JSON.parse(localStorage.getItem('user_data'));
        } catch (e) {
            return null;
        }
    }

    getNavItems(role) {
        const navConfigs = {
            BUYER: [
                { label: 'Market', href: '/', icon: '🏠' },
                { label: 'Shop', href: '/products', icon: '🛍️' },
                { label: 'Cart', href: '/cart', icon: '🛒', badgeClass: 'badge-cart dynamic' },
                { label: 'Track', href: '/orders', icon: '📦' },
                { label: 'Me', href: '/buyer-dashboard', icon: '👤' }
            ],
            SELLER: [
                { label: 'Dashboard', href: '/seller-dashboard', icon: '📊' },
                { label: 'Inventory', href: '/seller-products', icon: '📦' },
                { label: 'Sales', href: '/seller-orders', icon: '🛒' },
                { label: 'Finances', href: '/seller-earnings', icon: '💰' },
                { label: 'My Store', href: '/seller-store', icon: '🏪' }
            ],
            ADMIN: [
                { label: 'Admin Hub', href: '/admin-dashboard', icon: '🔧' },
                { label: 'Users', href: '/admin-users', icon: '👥' },
                { label: 'KYC Queue', href: '/admin-sellers', icon: '🛡️' },
                { label: 'Products', href: '/admin-products', icon: '📦' },
                { label: 'Disputes', href: '/admin-disputes', icon: '⚖️' }
            ],
            GUEST: [
                { label: 'Home', href: '/', icon: '🏠' },
                { label: 'Browse', href: '/products', icon: '🛍️' },
                { label: 'Login', href: '/login', icon: '🔑', highlight: true },
                { label: 'Sell on Optimistic', href: '/seller-register', icon: '📈' }
            ]
        };
        return navConfigs[role] || navConfigs.GUEST;
    }

    render(role, user) {
        if (!this.navContainer) return;
        
        const items = this.getNavItems(role);
        const navHtml = items.map(item => `
            <a href="${item.href}" class="nav-link ${item.highlight ? 'btn-purple' : ''}">
                <span class="nav-icon">${item.icon}</span>
                <span class="nav-label">${item.label}</span>
                ${item.badgeClass ? `<span class="badge ${item.badgeClass}">0</span>` : ''}
            </a>
        `).join('') + (user ? `<div class="user-avatar-small"><img src="${user.profile_picture || '/static/images/default-avatar.png'}" alt="Profile"></div>` : '');

        this.navContainer.innerHTML = navHtml;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new OptimisticNavigation();
});