/**
 * Real-time updates manager for Optimistic
 * Handles live data polling, notifications, and status updates
 */

class RealtimeManager {
    constructor() {
        this.intervals = {};
        this.isActive = true;
    }

    /**
     * Start polling for notifications
     */
    startNotificationPolling() {
        if (!api.isAuthenticated()) return;

        // Poll every 30 seconds
        this.intervals.notifications = setInterval(async () => {
            try {
                const data = await api.getNotifications();
                this.updateNotificationBadge(data.results || []);
            } catch (error) {
                console.error('Failed to fetch notifications:', error);
            }
        }, 30000);

        // Initial load
        this.fetchNotifications();
    }

    async fetchNotifications() {
        try {
            const data = await api.getNotifications();
            this.updateNotificationBadge(data.results || []);
        } catch (error) {
            console.error('Failed to fetch notifications:', error);
        }
    }

    updateNotificationBadge(notifications) {
        const unreadCount = notifications.filter(n => !n.is_read).length;
        const badge = document.getElementById('notification-badge');
        
        if (badge) {
            if (unreadCount > 0) {
                badge.textContent = unreadCount > 9 ? '9+' : unreadCount;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        }
    }

    /**
     * Watch localStorage for cart/wishlist changes
     */
    startLocalStorageWatcher() {
        // Poll cart and wishlist every 2 seconds
        this.intervals.storage = setInterval(() => {
            this.updateCartCount();
            this.updateWishlistCount();
        }, 2000);

        // Listen for changes from other tabs
        window.addEventListener('storage', (e) => {
            if (e.key === 'cart') {
                this.updateCartCount();
            } else if (e.key === 'wishlist') {
                this.updateWishlistCount();
            }
        });
    }

    updateCartCount() {
        const cart = JSON.parse(localStorage.getItem('cart') || '[]');
        const cartCount = document.getElementById('cart-count');
        if (cartCount) {
            cartCount.textContent = cart.length;
            
            // Animate on change
            cartCount.style.animation = 'none';
            setTimeout(() => {
                cartCount.style.animation = 'pulse 0.3s ease';
            }, 10);
        }
    }

    updateWishlistCount() {
        const wishlist = JSON.parse(localStorage.getItem('wishlist') || '[]');
        const wishlistCount = document.getElementById('wishlist-count');
        if (wishlistCount) {
            wishlistCount.textContent = wishlist.length;
        }
    }

    /**
     * Add live timestamps to elements
     */
    startTimestampUpdates() {
        this.intervals.timestamps = setInterval(() => {
            document.querySelectorAll('[data-timestamp]').forEach(el => {
                const timestamp = el.getAttribute('data-timestamp');
                el.textContent = this.getRelativeTime(new Date(timestamp));
            });
        }, 60000); // Update every minute
    }

    getRelativeTime(date) {
        const now = new Date();
        const diff = now - date;
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (seconds < 60) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        return date.toLocaleDateString();
    }

    /**
     * Show live connection status
     */
    showConnectionStatus(isOnline) {
        const statusEl = document.getElementById('connection-status');
        if (statusEl) {
            statusEl.textContent = isOnline ? '🟢 Online' : '🔴 Offline';
            statusEl.className = isOnline ? 'status-online' : 'status-offline';
        }
    }

    /**
     * Monitor online/offline status
     */
    startConnectionMonitor() {
        window.addEventListener('online', () => {
            this.showConnectionStatus(true);
            console.log('Connection restored');
            // Refresh data
            window.location.reload();
        });

        window.addEventListener('offline', () => {
            this.showConnectionStatus(false);
            console.log('Connection lost');
        });

        // Initial status
        this.showConnectionStatus(navigator.onLine);
    }

    /**
     * Start all real-time features
     */
    start() {
        this.startLocalStorageWatcher();
        this.startNotificationPolling();
        this.startTimestampUpdates();
        this.startConnectionMonitor();
        
        console.log('✅ Real-time updates started');
    }

    /**
     * Stop all polling and clean up
     */
    stop() {
        Object.values(this.intervals).forEach(interval => clearInterval(interval));
        this.intervals = {};
        this.isActive = false;
        console.log('🛑 Real-time updates stopped');
    }
}

// Export single instance
const realtimeManager = new RealtimeManager();

// Auto-start on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        realtimeManager.start();
    });
} else {
    realtimeManager.start();
}

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    realtimeManager.stop();
});
