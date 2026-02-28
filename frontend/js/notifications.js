/**
 * Notification UI Component for Optimistic Marketplace
 * 
 * Features:
 * - Real-time notification fetching
 * - Unread count badge
 * - Mark as read functionality
 * - Notification dropdown panel
 * - Toast notifications for instant feedback
 * - Auto-refresh every 30 seconds
 */

class NotificationManager {
    constructor(apiClient) {
        this.api = apiClient;
        this.notifications = [];
        this.unreadCount = 0;
        this.isOpen = false;
        this.refreshInterval = null;
        
        // DOM elements
        this.badge = null;
        this.panel = null;
        this.list = null;
        
        this.init();
    }

    /**
     * Initialize notification system
     */
    async init() {
        this.createUI();
        await this.loadNotifications();
        this.startAutoRefresh();
        this.setupEventListeners();
    }

    /**
     * Create notification UI elements
     */
    createUI() {
        // Create notification bell icon with badge
        const nav = document.querySelector('.nav-links');
        if (!nav) return;

        const notifItem = document.createElement('li');
        notifItem.innerHTML = `
            <a href="#" id="notificationBell" class="notification-bell">
                🔔
                <span class="notification-badge" id="notificationBadge">0</span>
            </a>
        `;
        
        // Insert before auth link
        const authLink = nav.querySelector('#authLink')?.parentElement;
        if (authLink) {
            nav.insertBefore(notifItem, authLink);
        } else {
            nav.appendChild(notifItem);
        }

        // Create notification panel (dropdown)
        const panel = document.createElement('div');
        panel.id = 'notificationPanel';
        panel.className = 'notification-panel';
        panel.innerHTML = `
            <div class="notification-header">
                <h3>Notifications</h3>
                <button id="markAllRead" class="btn-text">Mark all read</button>
            </div>
            <div class="notification-list" id="notificationList">
                <div class="notification-loading">Loading...</div>
            </div>
            <div class="notification-footer">
                <a href="notifications.html">View all notifications</a>
            </div>
        `;
        document.body.appendChild(panel);

        // Store references
        this.badge = document.getElementById('notificationBadge');
        this.panel = document.getElementById('notificationPanel');
        this.list = document.getElementById('notificationList');

        // Add styles
        this.injectStyles();
    }

    /**
     * Inject CSS styles for notifications
     */
    injectStyles() {
        if (document.getElementById('notification-styles')) return;

        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            /* Notification Bell */
            .notification-bell {
                position: relative;
                font-size: 1.5rem;
                cursor: pointer;
            }

            .notification-badge {
                position: absolute;
                top: -5px;
                right: -5px;
                background: var(--danger-color, #EF4444);
                color: white;
                border-radius: 50%;
                width: 20px;
                height: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 0.75rem;
                font-weight: bold;
                display: none;
            }

            .notification-badge.active {
                display: flex;
            }

            /* Notification Panel */
            .notification-panel {
                position: fixed;
                top: 70px;
                right: 20px;
                width: 380px;
                max-height: 500px;
                background: white;
                border-radius: var(--radius-xl, 1rem);
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
                z-index: 1000;
                display: none;
                flex-direction: column;
            }

            .notification-panel.active {
                display: flex;
            }

            .notification-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: var(--space-4, 1rem);
                border-bottom: 1px solid var(--border-light, #E2E8F0);
            }

            .notification-header h3 {
                margin: 0;
                font-size: 1.125rem;
            }

            .btn-text {
                background: none;
                border: none;
                color: var(--primary-color, #0EA5E9);
                font-size: 0.875rem;
                cursor: pointer;
                padding: 0;
            }

            .btn-text:hover {
                text-decoration: underline;
            }

            .notification-list {
                flex: 1;
                overflow-y: auto;
                max-height: 380px;
            }

            .notification-loading {
                padding: var(--space-8, 2rem);
                text-align: center;
                color: var(--text-medium, #475569);
            }

            .notification-empty {
                padding: var(--space-8, 2rem);
                text-align: center;
                color: var(--text-medium, #475569);
            }

            .notification-item {
                padding: var(--space-4, 1rem);
                border-bottom: 1px solid var(--border-light, #E2E8F0);
                cursor: pointer;
                transition: background var(--transition-fast, 150ms);
            }

            .notification-item:hover {
                background: var(--bg-secondary, #F8FAFC);
            }

            .notification-item.unread {
                background: #EFF6FF;
                border-left: 3px solid var(--primary-color, #0EA5E9);
            }

            .notification-item-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: var(--space-2, 0.5rem);
            }

            .notification-type {
                font-size: 0.75rem;
                background: var(--bg-tertiary, #F1F5F9);
                padding: 2px 8px;
                border-radius: var(--radius-sm, 0.375rem);
                text-transform: uppercase;
                font-weight: 600;
            }

            .notification-time {
                font-size: 0.75rem;
                color: var(--text-light, #94A3B8);
            }

            .notification-title {
                font-weight: 600;
                margin-bottom: var(--space-1, 0.25rem);
            }

            .notification-message {
                font-size: 0.875rem;
                color: var(--text-medium, #475569);
            }

            .notification-footer {
                padding: var(--space-3, 0.75rem);
                border-top: 1px solid var(--border-light, #E2E8F0);
                text-align: center;
            }

            .notification-footer a {
                color: var(--primary-color, #0EA5E9);
                font-size: 0.875rem;
                font-weight: 600;
                text-decoration: none;
            }

            .notification-footer a:hover {
                text-decoration: underline;
            }

            /* Toast Notifications */
            .toast-container {
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 9999;
            }

            .toast {
                background: white;
                padding: var(--space-4, 1rem);
                border-radius: var(--radius-lg, 0.75rem);
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
                margin-top: var(--space-2, 0.5rem);
                min-width: 300px;
                max-width: 400px;
                animation: slideInRight 0.3s ease-out;
                display: flex;
                align-items: flex-start;
                gap: var(--space-3, 0.75rem);
            }

            .toast.success {
                border-left: 4px solid var(--success-color, #10B981);
            }

            .toast.error {
                border-left: 4px solid var(--danger-color, #EF4444);
            }

            .toast.info {
                border-left: 4px solid var(--info-color, #3B82F6);
            }

            .toast-icon {
                font-size: 1.5rem;
            }

            .toast-content {
                flex: 1;
            }

            .toast-title {
                font-weight: 600;
                margin-bottom: var(--space-1, 0.25rem);
            }

            .toast-message {
                font-size: 0.875rem;
                color: var(--text-medium, #475569);
            }

            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }

            /* Mobile Responsive */
            @media (max-width: 640px) {
                .notification-panel {
                    right: 10px;
                    left: 10px;
                    width: auto;
                }

                .toast {
                    min-width: 250px;
                    max-width: calc(100vw - 40px);
                }
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Toggle notification panel
        document.getElementById('notificationBell')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.togglePanel();
        });

        // Mark all as read
        document.getElementById('markAllRead')?.addEventListener('click', () => {
            this.markAllAsRead();
        });

        // Close panel when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.panel?.contains(e.target) && !e.target.closest('.notification-bell')) {
                this.closePanel();
            }
        });
    }

    /**
     * Load notifications from API
     */
    async loadNotifications() {
        if (!this.api.isAuthenticated()) return;

        try {
            const response = await this.api.get('/notifications/?limit=10');
            this.notifications = response.results || response;
            this.updateUI();
            await this.updateUnreadCount();
        } catch (error) {
            console.error('Failed to load notifications:', error);
        }
    }

    /**
     * Update unread count
     */
    async updateUnreadCount() {
        if (!this.api.isAuthenticated()) return;

        try {
            const response = await this.api.get('/notifications/unread-count/');
            this.unreadCount = response.count || 0;
            this.updateBadge();
        } catch (error) {
            console.error('Failed to update unread count:', error);
        }
    }

    /**
     * Update notification badge
     */
    updateBadge() {
        if (!this.badge) return;

        this.badge.textContent = this.unreadCount;
        if (this.unreadCount > 0) {
            this.badge.classList.add('active');
        } else {
            this.badge.classList.remove('active');
        }
    }

    /**
     * Update notification list UI
     */
    updateUI() {
        if (!this.list) return;

        if (this.notifications.length === 0) {
            this.list.innerHTML = `
                <div class="notification-empty">
                    <p>📭 No notifications yet</p>
                </div>
            `;
            return;
        }

        this.list.innerHTML = this.notifications.map(notif => `
            <div class="notification-item ${notif.is_read ? '' : 'unread'}" 
                 data-id="${notif.id}" 
                 onclick="notificationManager.markAsRead(${notif.id})">
                <div class="notification-item-header">
                    <span class="notification-type">${notif.notification_type}</span>
                    <span class="notification-time">${this.formatTime(notif.created_at)}</span>
                </div>
                <div class="notification-title">${notif.title}</div>
                <div class="notification-message">${notif.message}</div>
            </div>
        `).join('');
    }

    /**
     * Format timestamp to relative time
     */
    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000); // seconds

        if (diff < 60) return 'Just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
        return date.toLocaleDateString();
    }

    /**
     * Toggle notification panel
     */
    togglePanel() {
        if (this.panel) {
            this.panel.classList.toggle('active');
            this.isOpen = !this.isOpen;
        }
    }

    /**
     * Close notification panel
     */
    closePanel() {
        if (this.panel) {
            this.panel.classList.remove('active');
            this.isOpen = false;
        }
    }

    /**
     * Mark notification as read
     */
    async markAsRead(notificationId) {
        try {
            await this.api.post(`/notifications/${notificationId}/read/`);
            
            // Update local state
            const notif = this.notifications.find(n => n.id === notificationId);
            if (notif) notif.is_read = true;
            
            this.updateUI();
            await this.updateUnreadCount();
        } catch (error) {
            console.error('Failed to mark notification as read:', error);
        }
    }

    /**
     * Mark all notifications as read
     */
    async markAllAsRead() {
        try {
            await this.api.post('/notifications/read-all/');
            
            // Update local state
            this.notifications.forEach(n => n.is_read = true);
            
            this.updateUI();
            await this.updateUnreadCount();
            this.showToast('All notifications marked as read', 'success');
        } catch (error) {
            console.error('Failed to mark all as read:', error);
            this.showToast('Failed to mark notifications as read', 'error');
        }
    }

    /**
     * Start auto-refresh
     */
    startAutoRefresh() {
        // Refresh every 30 seconds
        this.refreshInterval = setInterval(() => {
            if (this.api.isAuthenticated()) {
                this.updateUnreadCount();
                if (this.isOpen) {
                    this.loadNotifications();
                }
            }
        }, 30000);
    }

    /**
     * Stop auto-refresh
     */
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info', title = '') {
        // Create toast container if it doesn't exist
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        const icons = {
            success: '✓',
            error: '✗',
            info: 'ℹ',
        };

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-icon">${icons[type]}</div>
            <div class="toast-content">
                ${title ? `<div class="toast-title">${title}</div>` : ''}
                <div class="toast-message">${message}</div>
            </div>
        `;
        
        container.appendChild(toast);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            toast.style.animation = 'slideInRight 0.3s ease-out reverse';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }
}

// Initialize notification manager when DOM is ready
let notificationManager;

document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if API client is available
    if (typeof ZuStoreAPI !== 'undefined') {
        const api = new ZuStoreAPI();
        if (api.isAuthenticated()) {
            notificationManager = new NotificationManager(api);
        }
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationManager;
}
