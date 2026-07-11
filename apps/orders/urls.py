from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'fulfillments', views.OrderFulfillmentViewSet, basename='fulfillment')

urlpatterns = [
    path('payments/webhooks/<str:provider>/', views.payment_webhook, name='payment-webhook'),
    path('', include(router.urls)),
]
