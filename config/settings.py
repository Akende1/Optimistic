"""
Django settings for Optimistic project.
"""

from pathlib import Path
from decouple import config
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-development-key-change-this')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'debug_toolbar',
    
    # Local apps
    'apps.common',
    'apps.accounts',
    'apps.sellers',
    'apps.products',
    'apps.orders',
    'apps.logistics',
    'apps.notifications',
    'apps.reviews',
    'apps.finances',
    'apps.disputes',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.accounts.middleware.RoleBasedAccessMiddleware',  # Role-based access control
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'frontend'],  # Frontend HTML files
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Uncomment below to use PostgreSQL
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': config('DB_NAME', default='zu_store'),
#         'USER': config('DB_USER', default='postgres'),
#         'PASSWORD': config('DB_PASSWORD', default=''),
#         'HOST': config('DB_HOST', default='localhost'),
#         'PORT': config('DB_PORT', default='5432'),
#     }
# }

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Lusaka'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'frontend',  # Serve CSS, JS from frontend directory
]

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework - API Configuration
# Controls how Django REST Framework behaves
REST_FRAMEWORK = {
    # Authentication: How users prove their identity
    # JWTAuthentication: Stateless tokens (scalable, no server session)
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    
    # Permissions: Who can access what (global default)
    # IsAuthenticatedOrReadOnly:
    # - GET/HEAD/OPTIONS: Anyone (even anonymous)
    # - POST/PUT/PATCH/DELETE: Must be logged in
    # Views can override this with permission_classes attribute
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    
    # Pagination: Limit response size
    # PageNumberPagination: ?page=1, ?page=2, etc.
    # PAGE_SIZE: Items per page (20 is reasonable for mobile)
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,  # Balance: fewer API calls vs smaller payloads
}

# JWT Settings - Token Configuration
# How long tokens last and how they refresh
SIMPLE_JWT = {
    # Access token: Short-lived (1 hour)
    # Used for API authentication on every request
    # Short lifetime = less risk if stolen
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    
    # Refresh token: Long-lived (7 days)
    # Used to get new access tokens without re-login
    # Allows "stay logged in" functionality
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    
    # Rotate tokens: Get new refresh token when refreshing
    # Security: Limits impact of refresh token theft
    'ROTATE_REFRESH_TOKENS': True,
    
    # Blacklist old tokens: Old refresh tokens become invalid
    # Prevents reuse of rotated tokens
    'BLACKLIST_AFTER_ROTATION': True,
    
    # Authorization header format: "Bearer <token>"
    # Standard format for JWT in HTTP headers
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React dev server
    "http://127.0.0.1:3000",
    "http://localhost:8000",  # Django dev server
    "http://127.0.0.1:8000",  # Django dev server (IP)
]

# Allow credentials for JWT authentication
CORS_ALLOW_CREDENTIALS = True

# Allow common headers needed for API calls
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Debug Toolbar
INTERNAL_IPS = [
    '127.0.0.1',
]
