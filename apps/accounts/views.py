from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import UserSerializer, UserProfileSerializer
from django.contrib.auth import get_user_model
from apps.common.api_contract import success_response

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user.
    POST /api/auth/register/
    """
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        profile = UserProfileSerializer(user).data
        access = str(refresh.access_token)
        refresh_token = str(refresh)
        return success_response(
            data={
                'user': profile,
                'access': access,
                'refresh': refresh_token,
            },
            status_code=status.HTTP_201_CREATED,
            user=profile,
            access=access,
            refresh=refresh_token,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login user and return JWT tokens.
    POST /api/auth/login/
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({'error': 'Username and password required'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(username=username, password=password)
    
    if user is None:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    
    if not user.is_active:
        return Response({'error': 'Account is disabled'}, status=status.HTTP_403_FORBIDDEN)
    
    # Determine redirect URL based on role
    role = 'SUPER_ADMIN' if user.is_superuser else user.role
    redirect_urls = {
        'SUPER_ADMIN': '/super-admin-dashboard.html',
        'ADMIN': '/admin-dashboard-v2.html',
        'SELLER': '/seller-dashboard-v2.html',
        'BUYER': '/buyer-dashboard.html',
        'COURIER': '/courier-dashboard.html',
    }
    
    refresh = RefreshToken.for_user(user)
    profile = UserProfileSerializer(user).data
    access = str(refresh.access_token)
    refresh_token = str(refresh)
    redirect = redirect_urls.get(role, '/index.html')

    return success_response(
        data={
            'user': profile,
            'access': access,
            'refresh': refresh_token,
            'redirect': redirect,
        },
        user=profile,
        access=access,
        refresh=refresh_token,
        redirect=redirect,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    Get current user profile.
    GET /api/auth/profile/
    GET /api/auth/me/  (alias)
    """
    serializer = UserProfileSerializer(request.user, context={'request': request})
    return success_response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def update_profile_picture(request):
    """
    Update user profile picture.
    PATCH /api/auth/profile/picture/
    
    Body (multipart/form-data):
        - profile_picture: Image file
    """
    user = request.user
    
    if 'profile_picture' not in request.FILES:
        return Response(
            {'error': 'profile_picture file required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user.profile_picture = request.FILES['profile_picture']
    user.save()
    
    return success_response(UserProfileSerializer(user, context={'request': request}).data)
