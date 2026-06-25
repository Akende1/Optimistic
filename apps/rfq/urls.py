from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RfqRequestViewSet

router = DefaultRouter()
router.register(r'rfqs', RfqRequestViewSet, basename='rfq')

urlpatterns = [
    path('', include(router.urls)),
]
