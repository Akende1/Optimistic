from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from . import admin_views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='profile-update'),
    path('me/', views.profile, name='me'),  # Alias for current user
    path('profile/picture/', views.update_profile_picture, name='update-profile-picture'),
    path('change-password/', views.change_password, name='change-password'),
    path('addresses/', views.addresses, name='addresses'),
    path('addresses/<int:address_id>/', views.address_detail, name='address-detail'),
    path('verification/request/', views.request_verification_code, name='verification-request'),
    path('verification/confirm/', views.confirm_verification_code, name='verification-confirm'),
    path('verification/status/', views.verification_status, name='verification-status'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Super Admin endpoints
    path('super-admin/create-admin/', admin_views.create_admin_user, name='create-admin-user'),
]
