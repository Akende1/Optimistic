"""
URL Configuration for Optimistic
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # Frontend pages
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('index.html', TemplateView.as_view(template_name='index.html'), name='index'),
    path('products.html', TemplateView.as_view(template_name='products.html'), name='products'),
    path('product-detail.html', TemplateView.as_view(template_name='product-detail.html'), name='product-detail'),
    path('cart.html', TemplateView.as_view(template_name='cart.html'), name='cart'),
    path('checkout.html', TemplateView.as_view(template_name='checkout.html'), name='checkout'),
    path('orders.html', TemplateView.as_view(template_name='orders.html'), name='orders'),
    path('order-detail.html', TemplateView.as_view(template_name='order-detail.html'), name='order-detail'),
    path('profile.html', TemplateView.as_view(template_name='profile.html'), name='profile'),
    path('login.html', TemplateView.as_view(template_name='login.html'), name='login'),
    path('register.html', TemplateView.as_view(template_name='register.html'), name='register'),
    path('about.html', TemplateView.as_view(template_name='about.html'), name='about'),
    path('contact.html', TemplateView.as_view(template_name='contact.html'), name='contact'),
    path('add-product.html', TemplateView.as_view(template_name='add-product.html'), name='add-product'),
    path('admin-dashboard.html', TemplateView.as_view(template_name='admin-dashboard.html'), name='admin-dashboard'),
    path('buyer-dashboard.html', TemplateView.as_view(template_name='buyer-dashboard.html'), name='buyer-dashboard'),
    path('wishlist.html', TemplateView.as_view(template_name='wishlist.html'), name='wishlist'),
    path('system-test.html', TemplateView.as_view(template_name='system-test.html'), name='system-test'),
    path('debug-user.html', TemplateView.as_view(template_name='debug-user.html'), name='debug-user'),
    
    # Seller Operating System (Operational single-purpose pages)
    path('seller-dashboard.html', TemplateView.as_view(template_name='seller-dashboard-v2.html'), name='seller-dashboard'),
    path('seller-dashboard-v2.html', TemplateView.as_view(template_name='seller-dashboard-v2.html'), name='seller-dashboard-v2'),
    path('seller-products-v2.html', TemplateView.as_view(template_name='seller-products-v2.html'), name='seller-products-v2'),
    path('seller-orders-v2.html', TemplateView.as_view(template_name='seller-orders-v2.html'), name='seller-orders-v2'),
    path('seller-earnings-v2.html', TemplateView.as_view(template_name='seller-earnings-v2.html'), name='seller-earnings-v2'),
    path('seller-store-v2.html', TemplateView.as_view(template_name='seller-store-v2.html'), name='seller-store-v2'),
    path('seller-disputes-v2.html', TemplateView.as_view(template_name='seller-disputes-v2.html'), name='seller-disputes-v2'),
    path('seller-profile-v2.html', TemplateView.as_view(template_name='seller-profile-v2.html'), name='seller-profile-v2'),
    
    # Admin System Control (Instruments for platform governance)
    # Super admin features are integrated into admin-dashboard-v2.html with conditional visibility
    path('super-admin-dashboard.html', TemplateView.as_view(template_name='admin-dashboard-v2.html'), name='super-admin-dashboard'),
    path('admin-dashboard-v2.html', TemplateView.as_view(template_name='admin-dashboard-v2.html'), name='admin-dashboard-v2'),
    path('admin-users-v2.html', TemplateView.as_view(template_name='admin-users-v2.html'), name='admin-users-v2'),
    path('admin-user-detail.html', TemplateView.as_view(template_name='admin-user-detail.html'), name='admin-user-detail'),
    path('admin-products-v2.html', TemplateView.as_view(template_name='admin-products-v2.html'), name='admin-products-v2'),
    path('admin-orders-v2.html', TemplateView.as_view(template_name='admin-orders-v2.html'), name='admin-orders-v2'),
    path('admin-disputes-v2.html', TemplateView.as_view(template_name='admin-disputes-v2.html'), name='admin-disputes-v2'),
    path('admin-finances-v2.html', TemplateView.as_view(template_name='admin-finances-v2.html'), name='admin-finances-v2'),
    path('admin-courier-payouts-v2.html', TemplateView.as_view(template_name='admin-courier-payouts-v2.html'), name='admin-courier-payouts-v2'),
    path('admin-reports-v2.html', TemplateView.as_view(template_name='admin-reports-v2.html'), name='admin-reports-v2'),
    path('admin-settings-v2.html', TemplateView.as_view(template_name='admin-settings-v2.html'), name='admin-settings-v2'),
    path('admin-audit-logs-v2.html', TemplateView.as_view(template_name='admin-audit-logs-v2.html'), name='admin-audit-logs-v2'),
    
    # API endpoints (backward-compatible + versioned namespace)
    path('admin/', admin.site.urls),
    path('api/', include('config.api_urls')),
    path('api/v1/', include('config.api_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]

# Admin site customization
admin.site.site_header = "Optimistic Administration"
admin.site.site_title = "Optimistic Admin"
admin.site.index_title = "Marketplace Control Center"
