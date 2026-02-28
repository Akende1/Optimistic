from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from . import admin_views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('profile/', views.profile, name='profile'),
    path('me/', views.profile, name='me'),  # Alias for current user
    path('profile/picture/', views.update_profile_picture, name='update-profile-picture'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Super Admin endpoints
    path('super-admin/create-admin/', admin_views.create_admin_user, name='create-admin-user'),
]
