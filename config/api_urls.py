"""
Centralized API route includes.
Supports mounting under multiple API namespaces (e.g. /api/ and /api/v1/).
"""
from django.urls import include, path

urlpatterns = [
    path('auth/', include('apps.accounts.urls')),
    path('', include('apps.products.urls')),
    path('', include('apps.sellers.urls')),
    path('', include('apps.orders.urls')),
    path('', include('apps.logistics.urls')),
    path('', include('apps.notifications.urls')),
    path('', include('apps.reviews.urls')),
    path('admin/', include('apps.common.urls')),
]
