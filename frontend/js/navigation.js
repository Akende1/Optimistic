/**
 * Smart Navigation System
 * 
 * Purpose: Render context-aware navigation based on user role and current page
 * 
 * Design Principles:
 * - Buyers see shopping-focused nav (Products, Cart, Orders, Wishlist)
 * - Sellers see business-focused nav (Dashboard, Products, Orders, Profile)
 * - Couriers see delivery-focused nav (Deliveries, Earnings, Profile)
 * - Admins see management-focused nav (Dashboard, Users, Disputes, Reports)
 * - Anonymous users see minimal nav (Home, Products, About, Login)
 */

class NavigationManager {
    constructor() {
        this.user = null;
        this.currentPage = this.getCurrentPage();
    }

    /**
     * Get current page identifier from URL
     */
    getCurrentPage() {
        const path = window.location.pathname;
        const page = path.split('/').pop() || 'index.html';
        return page.replace('.html', '');
    }

    /**
     * Fetch current user data from API
     */
    async loadUser() {
        try {
            const api = new ZuStoreAPI();
            if (!api.isAuthenticated()) {
                return null;
            }
            this.user = await api.getProfile();
            return this.user;
        } catch (error) {
            console.warn('Failed to load user:', error);
            return null;
        }
    }

    /**
     * Get navigation items based on user role
     */
    getNavItems(role) {
        const navConfigs = {
            // Anonymous users
            guest: [
                { label: 'Home', href: 'index.html', icon: '🏠' },
                { label: 'Products', href: 'products.html', icon: '🛍️' },
                { label: 'About', href: 'about.html', icon: 'ℹ️' },
                { label: 'Contact', href: 'contact.html', icon: '📧' },
                { label: 'Login', href: 'login.html', icon: '🔐', align: 'right', highlight: true }
            ],

            // Buyers (shopping focus)
            BUYER: [
                { label: 'Home', href: 'index.html', icon: '🏠' },
                { label: 'Products', href: 'products.html', icon: '🛍️' },
                { label: 'Cart', href: 'cart.html', icon: '🛒', badge: 'cart' },
                { label: 'Orders', href: 'orders.html', icon: '📦' },
                { label: 'Wishlist', href: 'wishlist.html', icon: '❤️' },
                { label: 'Dashboard', href: 'buyer-dashboard.html', icon: '📊', align: 'right' },
                { label: 'Profile', href: 'profile.html', icon: '👤', align: 'right' }
            ],

            // Sellers (business focus)
            SELLER: [
                { label: 'Dashboard', href: 'seller-dashboard-v2.html', icon: '📊' },
                { label: 'Products', href: 'seller-products-v2.html', icon: '📦' },
                { label: 'Add Product', href: 'add-product.html', icon: '➕' },
                { label: 'Orders', href: 'seller-orders-v2.html', icon: '🛒' },
                { label: 'Earnings', href: 'seller-earnings-v2.html', icon: '💰', align: 'right' },
                { label: 'Store', href: 'seller-store-v2.html', icon: '🏪', align: 'right' },
                { label: 'Profile', href: 'profile.html', icon: '👤', align: 'right' }
            ],

            // Couriers (delivery focus)
            COURIER: [
                { label: 'Dashboard', href: 'courier-dashboard.html', icon: '🚚' },
                { label: 'Deliveries', href: 'deliveries.html', icon: '📦' },
                { label: 'Earnings', href: 'courier-earnings.html', icon: '💰' },
                { label: 'Routes', href: 'routes.html', icon: '🗺️' },
                { label: 'Profile', href: 'profile.html', icon: '👤', align: 'right' }
            ],

            // Admins (management focus)
            ADMIN: [
                { label: 'Dashboard', href: 'admin-dashboard-v2.html', icon: '🔧' },
                { label: 'Users', href: 'admin-users-v2.html', icon: '👥' },
                { label: 'Products', href: 'admin-products-v2.html', icon: '📦' },
                { label: 'Orders', href: 'admin-orders-v2.html', icon: '🛒' },
                { label: 'Disputes', href: 'admin-disputes-v2.html', icon: '⚖️' },
                { label: 'Reports', href: 'admin-reports-v2.html', icon: '📊', align: 'right' }
            ]
        };

        return navConfigs[role] || navConfigs.guest;
    }

    /**
     * Get cart count from localStorage
     */
    getCartCount() {
        try {
            const cart = JSON.parse(localStorage.getItem('cart') || '[]');
            return cart.reduce((total, item) => total + (item.quantity || 1), 0);
        } catch {
            return 0;
        }
    }

    /**
     * Render navigation bar
     */
    async render() {
        await this.loadUser();
        const role = this.user ? this.user.role : 'guest';
        const navItems = this.getNavItems(role);

        const navbar = document.querySelector('.navbar .nav-container');
        if (!navbar) return;

        // Build navigation HTML
        const leftItems = navItems.filter(item => !item.align || item.align === 'left');
        const rightItems = navItems.filter(item => item.align === 'right');

        const leftHTML = leftItems.map(item => this.renderNavItem(item)).join('');
        const rightHTML = rightItems.map(item => this.renderNavItem(item)).join('');

        navbar.innerHTML = `
            <a href="index.html" class="nav-logo">Optimistic</a>
            
            <!-- Mobile Menu Toggle -->
            <button class="mobile-menu-toggle" aria-label="Toggle mobile menu" aria-expanded="false">
                <span class="hamburger-line"></span>
                <span class="hamburger-line"></span>
                <span class="hamburger-line"></span>
            </button>
            
            <!-- Mobile Overlay -->
            <div class="mobile-overlay"></div>
            
            <ul class="nav-links">
                ${leftHTML}
                ${rightHTML}
            </ul>
        `;

        // Add logout button if authenticated
        if (this.user) {
            const navLinks = navbar.querySelector('.nav-links');
            const logoutItem = document.createElement('li');
            logoutItem.innerHTML = '<a href="#" id="logout-btn" style="color: #ff4444;">🚪 Logout</a>';
            navLinks.appendChild(logoutItem);

            document.getElementById('logout-btn').addEventListener('click', (e) => {
                e.preventDefault();
                new ZuStoreAPI().logout();
            });
        }

        this.highlightCurrentPage();
        this.initMobileMenu();
    }

    /**
     * Initialize mobile menu toggle functionality
     */
    initMobileMenu() {
        const toggle = document.querySelector('.mobile-menu-toggle');
        const navLinks = document.querySelector('.nav-links');
        const overlay = document.querySelector('.mobile-overlay');
        const body = document.body;

        if (!toggle || !navLinks || !overlay) return;

        // Toggle mobile menu
        const toggleMenu = () => {
            const isActive = navLinks.classList.toggle('active');
            overlay.classList.toggle('active');
            toggle.classList.toggle('active');
            toggle.setAttribute('aria-expanded', isActive.toString());
            
            // Prevent body scroll when menu is open
            if (isActive) {
                body.style.overflow = 'hidden';
            } else {
                body.style.overflow = '';
            }
        };

        // Close mobile menu
        const closeMenu = () => {
            navLinks.classList.remove('active');
            overlay.classList.remove('active');
            toggle.classList.remove('active');
            toggle.setAttribute('aria-expanded', 'false');
            body.style.overflow = '';
        };

        // Toggle button click
        toggle.addEventListener('click', toggleMenu);

        // Overlay click (close menu)
        overlay.addEventListener('click', closeMenu);

        // Close menu when clicking nav links
        const links = navLinks.querySelectorAll('a');
        links.forEach(link => {
            link.addEventListener('click', closeMenu);
        });

        // Close menu on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && navLinks.classList.contains('active')) {
                closeMenu();
            }
        });

        // Close menu when resizing to desktop
        let resizeTimer;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                if (window.innerWidth > 767) {
                    closeMenu();
                }
            }, 150);
        });
    }

    /**
     * Render individual navigation item
     */
    renderNavItem(item) {
        const isActive = this.isActivePage(item.href);
        const activeClass = isActive ? 'active' : '';
        const highlightClass = item.highlight ? 'btn btn-primary' : '';
        
        let badge = '';
        if (item.badge === 'cart') {
            const count = this.getCartCount();
            badge = count > 0 ? `<span class="cart-badge">${count}</span>` : '';
        }

        return `
            <li class="${activeClass}">
                <a href="${item.href}" class="${highlightClass}">
                    ${item.icon} ${item.label}${badge}
                </a>
            </li>
        `;
    }

    /**
     * Check if given href matches current page
     */
    isActivePage(href) {
        const linkPage = href.split('#')[0].replace('.html', '');
        return linkPage === this.currentPage || 
               (this.currentPage === 'index' && linkPage === 'index.html');
    }

    /**
     * Add active class to current page link
     */
    highlightCurrentPage() {
        const links = document.querySelectorAll('.nav-links a');
        links.forEach(link => {
            const href = link.getAttribute('href');
            if (href && this.isActivePage(href)) {
                link.parentElement.classList.add('active');
            }
        });
    }
}

/**
 * Initialize navigation on page load
 */
document.addEventListener('DOMContentLoaded', async () => {
    const nav = new NavigationManager();
    await nav.render();
});

/**
 * Update cart badge when cart changes
 */
window.addEventListener('storage', (e) => {
    if (e.key === 'cart') {
        const nav = new NavigationManager();
        nav.render();
    }
});
