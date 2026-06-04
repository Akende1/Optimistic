"""
Canonical page-to-endpoint alignment matrix for frontend/backend integration.
"""

PAGE_ENDPOINT_ALIGNMENT = {
    'public': {
        'products.html': ['GET /api/v1/categories/', 'GET /api/v1/products/'],
        'product-detail.html': ['GET /api/v1/products/{id}/', 'GET /api/v1/reviews/?product={id}'],
        'login.html': ['POST /api/v1/auth/login/', 'POST /api/v1/auth/token/refresh/', 'GET /api/v1/auth/me/'],
        'register.html': ['POST /api/v1/auth/register/'],
    },
    'buyer': {
        'buyer-dashboard.html': ['GET /api/v1/auth/profile/', 'GET /api/v1/orders/'],
        'checkout.html': ['GET /api/v1/orders/', 'POST /api/v1/orders/'],
        'orders.html': ['GET /api/v1/orders/', 'GET /api/v1/orders/{id}/', 'POST /api/v1/orders/{id}/confirm_delivery/'],
    },
    'seller': {
        'seller-dashboard-v2.html': ['GET /api/v1/sellers/analytics/', 'GET /api/v1/sellers/orders/'],
        'seller-products-v2.html': ['GET /api/v1/products/', 'POST /api/v1/products/', 'PATCH /api/v1/products/{id}/'],
        'seller-store-v2.html': ['PATCH /api/v1/sellers/update_profile/', 'GET /api/v1/sellers/me/'],
    },
    'admin': {
        'admin-dashboard-v2.html': ['GET /api/v1/admin/metrics/'],
        'admin-users-v2.html': ['GET /api/v1/admin/users/', 'GET /api/v1/admin/users/{id}/'],
        'admin-products-v2.html': ['GET /api/v1/products/', 'POST /api/v1/admin/products/{id}/approve/'],
        'admin-disputes-v2.html': ['GET /api/v1/admin/disputes/', 'POST /api/v1/admin/disputes/{id}/resolve/'],
        'admin-reports-v2.html': ['GET /api/v1/admin/reports/gmv/', 'GET /api/v1/admin/reports/revenue/'],
    },
}


KNOWN_ALIGNMENT_GAPS = {
    'missing_pages': [
        'courier-dashboard.html',
        'deliveries.html',
        'courier-earnings.html',
        'routes.html',
        'notifications.html',
    ],
    'duplicate_frontend_guards': ['frontend/js/roleGuard.js', 'frontend/js/role-guard.js'],
}
