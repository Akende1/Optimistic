from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'deliveries', views.DeliveryViewSet, basename='delivery')
router.register(r'delivery-partners', views.DeliveryPartnerViewSet, basename='delivery-partner')
router.register(r'locations', views.ZambianLocationViewSet, basename='location')

urlpatterns = [
    path('', include(router.urls)),
]
