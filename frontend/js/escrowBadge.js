/**
 * Escrow Trust Badge Component
 * 
 * Purpose: Build buyer confidence through visible escrow protection
 * 
 * Design Philosophy:
 * - Make safety visible, not buried in fine print
 * - Explain escrow in simple Zambian context
 * - Reinforce trust at every critical moment
 * 
 * Usage:
 * 1. Include this script: <script src="/static/js/escrowBadge.js"></script>
 * 2. Call: EscrowBadge.render('product-detail') or EscrowBadge.render('checkout')
 * 3. Or use auto-inject: EscrowBadge.autoInject()
 */

const EscrowBadge = {
    /**
     * Badge variants for different contexts
     */
    variants: {
        // Product detail page
        'product-detail': {
            title: '💰 Your Money is Protected',
            message: 'Pay safely with escrow protection. Your funds are held securely until you receive and confirm your order.',
            badge: 'BUYER PROTECTION',
            icon: '🛡️',
            style: 'info', // info, success, primary
            showDetails: true
        },

        // Checkout page
        'checkout': {
            title: '🔒 Safe Payment Guaranteed',
            message: 'Your payment is protected. Money is released to seller only after successful delivery.',
            badge: 'ESCROW PROTECTED',
            icon: '💳',
            style: 'success',
            showDetails: true
        },

        // Order tracking page
        'order-tracking': {
            title: '💰 Funds in Escrow',
            message: 'Your payment is safely held. Seller will receive funds after you confirm delivery.',
            badge: 'FUNDS PROTECTED',
            icon: '🔐',
            style: 'primary',
            showDetails: false
        },

        // Cart page (compact)
        'cart': {
            title: '🛡️ Escrow Protection',
            message: 'Shop with confidence. All payments are protected.',
            badge: 'PROTECTED',
            icon: '✅',
            style: 'compact',
            showDetails: false
        },

        // Order confirmation
        'order-confirmed': {
            title: '✅ Payment Secured in Escrow',
            message: 'Your K {amount} is safely held. Funds will be released to seller after delivery confirmation.',
            badge: 'ESCROW ACTIVE',
            icon: '🎯',
            style: 'success',
            showDetails: true
        }
    },

    /**
     * Render escrow badge
     * @param {string} variant - Badge variant ('product-detail', 'checkout', etc.)
     * @param {object} options - Additional options (amount, orderId, etc.)
     * @returns {HTMLElement} Badge element
     */
    render(variant = 'product-detail', options = {}) {
        const config = this.variants[variant] || this.variants['product-detail'];
        
        // Replace placeholders in message
        let message = config.message;
        if (options.amount) {
            message = message.replace('{amount}', `${options.amount.toFixed(2)}`);
        }

        // Create badge element
        const badge = document.createElement('div');
        badge.className = `escrow-badge escrow-badge-${config.style}`;
        
        // Build badge HTML based on style
        if (config.style === 'compact') {
            badge.innerHTML = this.renderCompactBadge(config, message);
        } else {
            badge.innerHTML = this.renderFullBadge(config, message, options);
        }

        // Inject styles if not already present
        this.injectStyles();

        return badge;
    },

    /**
     * Render compact badge (for cart, small spaces)
     */
    renderCompactBadge(config, message) {
        return `
            <div class="escrow-compact">
                <span class="escrow-icon">${config.icon}</span>
                <span class="escrow-text">${message}</span>
            </div>
        `;
    },

    /**
     * Render full badge (for product, checkout pages)
     */
    renderFullBadge(config, message, options) {
        const detailsHTML = config.showDetails ? `
            <div class="escrow-details">
                <div class="escrow-detail-item">
                    <span class="detail-icon">1️⃣</span>
                    <span class="detail-text">You place order & pay</span>
                </div>
                <div class="escrow-detail-item">
                    <span class="detail-icon">2️⃣</span>
                    <span class="detail-text">Money held safely in escrow</span>
                </div>
                <div class="escrow-detail-item">
                    <span class="detail-icon">3️⃣</span>
                    <span class="detail-text">You receive & confirm delivery</span>
                </div>
                <div class="escrow-detail-item">
                    <span class="detail-icon">4️⃣</span>
                    <span class="detail-text">Seller receives payment</span>
                </div>
            </div>
        ` : '';

        return `
            <div class="escrow-header">
                <div class="escrow-badge-label">
                    <span class="badge-icon">${config.icon}</span>
                    <span class="badge-text">${config.badge}</span>
                </div>
                <div class="escrow-title">${config.title}</div>
            </div>
            <div class="escrow-message">${message}</div>
            ${detailsHTML}
            <div class="escrow-footer">
                <small class="escrow-help">
                    <span class="help-icon">ℹ️</span>
                    Learn more about <a href="#" onclick="EscrowBadge.showModal(); return false;">escrow protection</a>
                </small>
            </div>
        `;
    },

    /**
     * Inject CSS styles for badges
     */
    injectStyles() {
        // Check if styles already injected
        if (document.getElementById('escrow-badge-styles')) {
            return;
        }

        const styles = document.createElement('style');
        styles.id = 'escrow-badge-styles';
        styles.textContent = `
            /* Escrow Badge Base Styles */
            .escrow-badge {
                border-radius: 12px;
                padding: 1.5rem;
                margin: 1.5rem 0;
                font-family: inherit;
                box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
                animation: slideIn 0.4s ease;
            }

            .escrow-badge-info {
                background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
                border: 2px solid #2196f3;
            }

            .escrow-badge-success {
                background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
                border: 2px solid #4caf50;
            }

            .escrow-badge-primary {
                background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
                border: 2px solid #9c27b0;
            }

            .escrow-badge-compact {
                background: #fff9e6;
                border: 1px solid #ffc107;
                padding: 0.75rem 1rem;
                margin: 0.5rem 0;
            }

            /* Header */
            .escrow-header {
                margin-bottom: 1rem;
            }

            .escrow-badge-label {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                background: rgba(255, 255, 255, 0.8);
                padding: 0.5rem 1rem;
                border-radius: 20px;
                font-size: 0.75rem;
                font-weight: 700;
                letter-spacing: 1px;
                text-transform: uppercase;
                margin-bottom: 0.75rem;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }

            .badge-icon {
                font-size: 1rem;
            }

            .escrow-title {
                font-size: 1.25rem;
                font-weight: 700;
                color: #1a1a1a;
                margin-bottom: 0.5rem;
            }

            .escrow-message {
                font-size: 0.95rem;
                color: #333;
                line-height: 1.6;
                margin-bottom: 1rem;
            }

            /* Details Section */
            .escrow-details {
                background: rgba(255, 255, 255, 0.6);
                border-radius: 8px;
                padding: 1rem;
                margin: 1rem 0;
            }

            .escrow-detail-item {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                padding: 0.5rem 0;
                font-size: 0.9rem;
                color: #444;
            }

            .detail-icon {
                font-size: 1.2rem;
                flex-shrink: 0;
            }

            .detail-text {
                flex: 1;
            }

            /* Footer */
            .escrow-footer {
                margin-top: 1rem;
                padding-top: 1rem;
                border-top: 1px solid rgba(0, 0, 0, 0.1);
            }

            .escrow-help {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                font-size: 0.85rem;
                color: #666;
            }

            .help-icon {
                font-size: 1rem;
            }

            .escrow-help a {
                color: #2196f3;
                text-decoration: underline;
                font-weight: 600;
            }

            .escrow-help a:hover {
                color: #1976d2;
            }

            /* Compact Variant */
            .escrow-compact {
                display: flex;
                align-items: center;
                gap: 0.75rem;
            }

            .escrow-icon {
                font-size: 1.5rem;
            }

            .escrow-text {
                font-size: 0.9rem;
                color: #333;
                font-weight: 500;
            }

            /* Animations */
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(-10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            /* Mobile Responsiveness */
            @media (max-width: 768px) {
                .escrow-badge {
                    padding: 1rem;
                }

                .escrow-title {
                    font-size: 1.1rem;
                }

                .escrow-message {
                    font-size: 0.9rem;
                }

                .escrow-details {
                    padding: 0.75rem;
                }

                .escrow-detail-item {
                    font-size: 0.85rem;
                }
            }
        `;

        document.head.appendChild(styles);
    },

    /**
     * Auto-inject badges based on current page
     */
    autoInject() {
        const page = window.location.pathname.split('/').pop();

        // Product detail page
        if (page === 'product-detail.html') {
            const container = document.querySelector('.product-details') || 
                            document.querySelector('.container');
            if (container) {
                const badge = this.render('product-detail');
                // Insert before "Add to Cart" button if exists
                const addToCartBtn = container.querySelector('.add-to-cart-btn');
                if (addToCartBtn) {
                    addToCartBtn.parentElement.insertBefore(badge, addToCartBtn);
                } else {
                    container.appendChild(badge);
                }
            }
        }

        // Checkout page
        if (page === 'checkout.html') {
            const container = document.querySelector('.checkout-summary') ||
                            document.querySelector('.order-summary');
            if (container) {
                const badge = this.render('checkout');
                container.insertBefore(badge, container.firstChild);
            }
        }

        // Cart page
        if (page === 'cart.html') {
            const container = document.querySelector('.cart-summary') ||
                            document.querySelector('.cart-total');
            if (container) {
                const badge = this.render('cart');
                container.insertBefore(badge, container.firstChild);
            }
        }

        // Order detail page
        if (page === 'order-detail.html') {
            const container = document.querySelector('.order-header') ||
                            document.querySelector('.order-info');
            if (container) {
                const badge = this.render('order-tracking');
                container.appendChild(badge);
            }
        }
    },

    /**
     * Show detailed escrow explanation modal
     */
    showModal() {
        // Create modal overlay
        const modal = document.createElement('div');
        modal.id = 'escrow-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 999999;
            animation: fadeIn 0.3s ease;
        `;

        modal.innerHTML = `
            <div style="
                background: white;
                padding: 2.5rem;
                border-radius: 16px;
                max-width: 600px;
                width: 90%;
                max-height: 90vh;
                overflow-y: auto;
                box-shadow: 0 10px 50px rgba(0, 0, 0, 0.3);
                animation: slideUp 0.3s ease;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                    <h2 style="font-size: 1.5rem; color: #1a1a1a; margin: 0;">
                        🛡️ How Escrow Protection Works
                    </h2>
                    <button onclick="document.getElementById('escrow-modal').remove()" style="
                        background: none;
                        border: none;
                        font-size: 2rem;
                        cursor: pointer;
                        color: #999;
                        line-height: 1;
                    ">×</button>
                </div>

                <div style="color: #333; line-height: 1.7;">
                    <p style="font-size: 1.05rem; margin-bottom: 1.5rem;">
                        Escrow is like a trusted middleman that holds your money safely until 
                        you receive your order. It protects both buyers and sellers.
                    </p>

                    <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem;">
                        <h3 style="font-size: 1.1rem; margin-bottom: 1rem; color: #2196f3;">
                            🔒 Your Money's Journey
                        </h3>
                        <ol style="margin: 0; padding-left: 1.5rem;">
                            <li style="margin-bottom: 1rem;">
                                <strong>You pay:</strong> Money goes to Optimistic's secure escrow account, 
                                NOT directly to seller
                            </li>
                            <li style="margin-bottom: 1rem;">
                                <strong>Seller ships:</strong> Seller packs and sends your order (they haven't 
                                received money yet, so they're motivated to deliver!)
                            </li>
                            <li style="margin-bottom: 1rem;">
                                <strong>You receive:</strong> Package arrives at your door. Check it carefully!
                            </li>
                            <li>
                                <strong>You confirm:</strong> Click "Confirm Delivery" in your orders. 
                                ONLY THEN does seller get paid
                            </li>
                        </ol>
                    </div>

                    <div style="background: #fff3e0; padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem;">
                        <h3 style="font-size: 1.1rem; margin-bottom: 1rem; color: #ff9800;">
                            ⚠️ What If Something Goes Wrong?
                        </h3>
                        <ul style="margin: 0; padding-left: 1.5rem;">
                            <li style="margin-bottom: 0.75rem;">
                                <strong>Item never arrives:</strong> Your money is refunded. Seller gets nothing.
                            </li>
                            <li style="margin-bottom: 0.75rem;">
                                <strong>Wrong item sent:</strong> Open dispute. We investigate. Fair resolution.
                            </li>
                            <li style="margin-bottom: 0.75rem;">
                                <strong>Item damaged:</strong> Photos required. Refund or replacement.
                            </li>
                        </ul>
                    </div>

                    <div style="background: #e8f5e9; padding: 1.5rem; border-radius: 12px;">
                        <h3 style="font-size: 1.1rem; margin-bottom: 1rem; color: #4caf50;">
                            ✅ Why Trust Optimistic Escrow?
                        </h3>
                        <ul style="margin: 0; padding-left: 1.5rem;">
                            <li style="margin-bottom: 0.75rem;">
                                Licensed payment system integrated with Zambian banks
                            </li>
                            <li style="margin-bottom: 0.75rem;">
                                Over K 500,000 protected in transactions to date
                            </li>
                            <li style="margin-bottom: 0.75rem;">
                                98% of disputes resolved within 5 days
                            </li>
                            <li>
                                Money returned if you're not satisfied
                            </li>
                        </ul>
                    </div>

                    <p style="text-align: center; margin-top: 2rem; font-size: 0.95rem; color: #666;">
                        Questions? <a href="contact.html" style="color: #2196f3; text-decoration: underline;">Contact our support team</a>
                    </p>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Close on background click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    },

    /**
     * Create inline escrow badge (for embedding in existing elements)
     * @param {string} text - Custom text
     * @returns {string} HTML string
     */
    inline(text = 'Escrow Protected') {
        return `
            <span style="
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                background: linear-gradient(135deg, #4caf50, #66bb6a);
                color: white;
                padding: 0.25rem 0.75rem;
                border-radius: 20px;
                font-size: 0.75rem;
                font-weight: 700;
                letter-spacing: 0.5px;
                text-transform: uppercase;
                box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
            ">
                <span>🛡️</span>
                <span>${text}</span>
            </span>
        `;
    }
};

/**
 * Auto-initialize on page load
 */
document.addEventListener('DOMContentLoaded', () => {
    // Auto-inject badges if not manually placed
    EscrowBadge.autoInject();
});

/**
 * Export for global use
 */
if (typeof window !== 'undefined') {
    window.EscrowBadge = EscrowBadge;
}
