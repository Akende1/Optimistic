"""
Admin/Moderation URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .admin_views import AdminModerationViewSet, SystemMetricsView
from apps.accounts import admin_views as user_admin_views
from apps.products import admin_views as product_admin_views
from apps.disputes import admin_views as dispute_admin_views
from . import reports

router = DefaultRouter()
router.register(r'moderation', AdminModerationViewSet, basename='admin-moderation')

urlpatterns = [
    path('metrics/', SystemMetricsView.as_view(), name='system-metrics'),
    
    # User Management
    path('users/', user_admin_views.list_users, name='admin-list-users'),
    path('users/<int:user_id>/', user_admin_views.get_user_detail, name='admin-user-detail'),
    path('users/<int:user_id>/suspend/', user_admin_views.suspend_user, name='admin-suspend-user'),
    path('users/<int:user_id>/activate/', user_admin_views.activate_user, name='admin-activate-user'),
    
    # Product Moderation
    path('products/<int:product_id>/approve/', product_admin_views.approve_product, name='admin-approve-product'),
    path('products/<int:product_id>/suspend/', product_admin_views.suspend_product, name='admin-suspend-product'),
    path('products/<int:product_id>/flag/', product_admin_views.flag_product, name='admin-flag-product'),
    path('products/<int:product_id>/archive/', product_admin_views.archive_product, name='admin-archive-product'),
    
    # Disputes
    path('disputes/', dispute_admin_views.list_disputes, name='admin-list-disputes'),
    path('disputes/<int:dispute_id>/resolve/', dispute_admin_views.resolve_dispute, name='admin-resolve-dispute'),
    path('disputes/<int:dispute_id>/close/', dispute_admin_views.close_dispute, name='admin-close-dispute'),
    
    # Reports
    path('reports/gmv/', reports.gmv_report, name='gmv-report'),
    path('reports/revenue/', reports.revenue_report, name='revenue-report'),
    path('reports/user-growth/', reports.user_growth_report, name='user-growth-report'),
    path('reports/seller-performance/', reports.seller_performance_report, name='seller-performance-report'),
    path('reports/product-metrics/', reports.product_metrics_report, name='product-metrics-report'),
    path('reports/financial-audit/', reports.financial_audit_report, name='financial-audit-report'),
    path('reports/audit-logs/', reports.export_audit_logs, name='audit-logs-report'),
    
    path('', include(router.urls)),
]
