"""
Role-based access control middleware
Enforces strict role separation across templates and views
"""
from django.shortcuts import redirect
from django.urls import reverse


class RoleBasedAccessMiddleware:
    """
    Middleware that enforces role-based template access.
    Prevents cross-role navigation (e.g., ADMIN accessing seller pages).
    """
    
    # Define which URL patterns are accessible by which roles
    ROLE_PATTERNS = {
        'ADMIN': [
            '/admin-', '/super-admin', '/api/admin', '/api/super-admin'
        ],
        'SELLER': [
            '/seller-', '/add-product', '/api/seller',
            # Sellers can also access buyer features
            '/buyer-', '/products', '/product-detail', '/cart', '/checkout', 
            '/orders', '/order-detail', '/profile', '/wishlist', '/api/orders', '/api/cart'
        ],
        'BUYER': [
            '/buyer-', '/products', '/product-detail', '/cart', '/checkout', 
            '/orders', '/order-detail', '/profile', '/wishlist', '/api/orders', '/api/cart'
        ],
        'COURIER': [
            '/courier-', '/api/courier'
        ],
    }
    
    # Public pages accessible to everyone
    PUBLIC_PATTERNS = [
        '/login',
        '/register',
        '/index',
        '/about',
        '/contact',
        '/static/',
        '/media/',
        '/api/auth/',
        '/api/categories/',
        '/api/products/',  # Public product browsing
        '/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip middleware for public pages
        path = request.path
        
        if any(path.startswith(pattern) for pattern in self.PUBLIC_PATTERNS):
            return self.get_response(request)
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Get user role (ADMIN role covers both regular admin and superuser)
        user_role = request.user.role
        
        # Check if user is accessing authorized pattern
        authorized_patterns = self.ROLE_PATTERNS.get(user_role, [])
        
        # Allow access if path matches user's role patterns
        if any(path.startswith(pattern) for pattern in authorized_patterns):
            return self.get_response(request)
        
        # Check if user is accessing another role's restricted area
        for role, patterns in self.ROLE_PATTERNS.items():
            if role != user_role:
                if any(path.startswith(pattern) for pattern in patterns):
                    # User trying to access restricted area - redirect to their dashboard
                    return redirect(self.get_dashboard_for_role(user_role))
        
        # Allow access if not explicitly restricted
        return self.get_response(request)
    
    def get_dashboard_for_role(self, role):
        """Return the appropriate dashboard URL for a given role."""
        dashboards = {
            'ADMIN': '/admin-dashboard',  # Clean URL for dashboard
            'SELLER': '/seller-dashboard',
            'BUYER': '/buyer-dashboard',
            'COURIER': '/courier-dashboard',
        }
        return dashboards.get(role, '/')
