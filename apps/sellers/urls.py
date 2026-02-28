from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, dashboard

router = DefaultRouter()
router.register(r'sellers', views.SellerViewSet, basename='seller')

urlpatterns = [
    path('', include(router.urls)),
    path('sellers/dashboard/', dashboard.seller_dashboard, name='seller-dashboard'),
    path('sellers/my-products/', dashboard.my_products, name='my-products'),
    path('sellers/my-orders/', dashboard.my_orders, name='my-orders'),
]
