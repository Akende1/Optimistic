"""Versioned API composition for mobile and other long-lived clients."""
from django.urls import include, path
from .mobile import api_meta, legal_documents, accept_legal_document

urlpatterns = [
    path('meta/', api_meta, name='mobile-api-meta'),
    path('legal/', legal_documents, name='legal-documents'),
    path('legal/accept/', accept_legal_document, name='legal-accept'),
    path('auth/', include('apps.accounts.urls')),
    path('', include('apps.products.urls')),
    path('', include('apps.sellers.urls')),
    path('', include('apps.orders.urls')),
    path('', include('apps.logistics.urls')),
    path('', include('apps.notifications.urls')),
    path('', include('apps.reviews.urls')),
    path('', include('apps.rfq.urls')),
]
