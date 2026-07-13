from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.contrib.auth import authenticate
from django.db.models import Q
from django.utils import timezone
from django.core.mail import send_mail
from django.core.cache import cache
from apps.common.models import AuditLog
from .serializers import (
    UserSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    ChangePasswordSerializer,
    BuyerAddressSerializer,
    VerificationRequestSerializer,
    VerificationConfirmSerializer,
)
from .models import BuyerAddress, AccountVerificationCode
from .sms import send_sms
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from datetime import timedelta
import secrets
import time

User = get_user_model()


VERIFICATION_CODE_TTL_MINUTES = getattr(settings, 'VERIFICATION_CODE_TTL_MINUTES', 10)
VERIFICATION_RESEND_COOLDOWN_SECONDS = getattr(settings, 'VERIFICATION_RESEND_COOLDOWN_SECONDS', 60)
VERIFICATION_MAX_REQUESTS_PER_HOUR = getattr(settings, 'VERIFICATION_MAX_REQUESTS_PER_HOUR', 6)
VERIFICATION_MAX_REQUESTS_PER_HOUR_PER_IP = getattr(settings, 'VERIFICATION_MAX_REQUESTS_PER_HOUR_PER_IP', 25)
VERIFICATION_LOCKOUT_SECONDS = getattr(settings, 'VERIFICATION_LOCKOUT_SECONDS', 900)


def _get_client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0') or '0.0.0.0'


def _log_verification_audit(action, user, request, details):
    try:
        AuditLog.objects.create(
            actor=user,
            action=action,
            target_type='User',
            target_id=user.id,
            details=details,
            ip_address=_get_client_ip(request),
        )
    except Exception:
        # Never block auth flow on audit write failures.
        pass


def _increment_cache_counter(key, window_seconds):
    current = cache.get(key)
    if current is None:
        cache.set(key, 1, timeout=window_seconds)
        return 1

    current += 1
    cache.set(key, current, timeout=window_seconds)
    return current


def _lockout_cache_key(user_id, channel):
    return f'verification:lockout:user:{user_id}:{channel}'


def _set_lockout(user_id, channel):
    unlock_at = int(time.time() + VERIFICATION_LOCKOUT_SECONDS)
    cache.set(_lockout_cache_key(user_id, channel), unlock_at, timeout=VERIFICATION_LOCKOUT_SECONDS)
    return VERIFICATION_LOCKOUT_SECONDS


def _get_lockout_remaining(user_id, channel):
    unlock_at = cache.get(_lockout_cache_key(user_id, channel))
    if unlock_at is None:
        return 0
    return max(0, int(unlock_at - time.time()))


def _issue_verification_code(user, channel):
    # Invalidate previous pending codes for the same channel to keep one active challenge.
    AccountVerificationCode.objects.filter(
        user=user,
        channel=channel,
        purpose='ACCOUNT_VERIFICATION',
        used_at__isnull=True,
        expires_at__gte=timezone.now(),
    ).update(expires_at=timezone.now())

    code = f"{secrets.randbelow(1000000):06d}"
    verification = AccountVerificationCode.objects.create(
        user=user,
        channel=channel,
        purpose='ACCOUNT_VERIFICATION',
        code=code,
        expires_at=timezone.now() + timedelta(minutes=VERIFICATION_CODE_TTL_MINUTES),
    )
    return verification


def _issue_password_reset_code(user):
    AccountVerificationCode.objects.filter(
        user=user, channel='EMAIL', purpose='PASSWORD_RESET', used_at__isnull=True,
    ).update(expires_at=timezone.now())
    return AccountVerificationCode.objects.create(
        user=user, channel='EMAIL', purpose='PASSWORD_RESET',
        code=f"{secrets.randbelow(1000000):06d}",
        expires_at=timezone.now() + timedelta(minutes=VERIFICATION_CODE_TTL_MINUTES),
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    """Issue a short-lived email reset challenge without revealing account existence."""
    email = str(request.data.get('email', '')).strip().lower()
    user = User.objects.filter(email__iexact=email, is_active=True).first()
    challenge = None
    if user and _increment_cache_counter(f'password-reset:{user.pk}', 3600) <= 6:
        challenge = _issue_password_reset_code(user)
        send_mail(
            subject='Reset your Optimistic password',
            message=f'Your password reset code is {challenge.code}. It expires in {VERIFICATION_CODE_TTL_MINUTES} minutes.',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@optimistic.local'),
            recipient_list=[user.email], fail_silently=True,
        )
    response = {'message': 'If that email belongs to an active account, a reset code has been sent.'}
    if settings.DEBUG and challenge:
        response['debug_code'] = challenge.code
    return Response(response)


@api_view(['POST'])
@permission_classes([AllowAny])
def confirm_password_reset(request):
    email = str(request.data.get('email', '')).strip().lower()
    code = str(request.data.get('code', '')).strip()
    password = str(request.data.get('new_password', ''))
    if len(password) < 8:
        return Response({'new_password': 'Password must contain at least 8 characters.'}, status=status.HTTP_400_BAD_REQUEST)
    user = User.objects.filter(email__iexact=email, is_active=True).first()
    challenge = AccountVerificationCode.objects.filter(
        user=user, channel='EMAIL', purpose='PASSWORD_RESET', code=code,
    ).order_by('-created_at').first() if user else None
    if not challenge or not challenge.can_attempt():
        return Response({'code': 'The reset code is invalid or expired.'}, status=status.HTTP_400_BAD_REQUEST)
    challenge.mark_used()
    user.set_password(password)
    user.save(update_fields=['password'])
    return Response({'message': 'Password reset successfully. Sign in with the new password.'})


def _mark_account_verified_if_ready(user):
    user.refresh_verification_status()


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user.
    POST /api/auth/register/
    """
    serializer = UserSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserProfileSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login user and return JWT tokens.
    POST /api/auth/login/
    """
    identifier = (
        request.data.get('identifier')
        or request.data.get('username')
        or request.data.get('email')
        or request.data.get('phone_number')
    )
    password = request.data.get('password')
    
    if not identifier or not password:
        return Response(
            {'error': 'Login identifier and password required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user_lookup = User.objects.filter(
        Q(username__iexact=identifier) |
        Q(email__iexact=identifier) |
        Q(phone_number=identifier)
    ).first()
    auth_username = user_lookup.username if user_lookup else identifier

    user = authenticate(username=auth_username, password=password)
    
    if user is None:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.is_active:
        return Response(
            {'error': 'Account is disabled'},
            status=status.HTTP_403_FORBIDDEN
        )
    
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
    return Response({
        'user': UserProfileSerializer(user).data,
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'redirect': redirect_urls.get(role, '/index.html'),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    Get current user profile.
    GET /api/auth/profile/
    GET /api/auth/me/  (alias)
    """
    serializer = UserProfileSerializer(request.user, context={'request': request})
    return Response(serializer.data)


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
    
    return Response(UserProfileSerializer(user, context={'request': request}).data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    Update editable profile fields.

    PATCH /api/auth/profile/
    """
    serializer = UserProfileUpdateSerializer(instance=request.user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(UserProfileSerializer(user, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change current user's password.

    POST /api/auth/change-password/
    """
    serializer = ChangePasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = request.user
    current_password = serializer.validated_data['current_password']
    if not check_password(current_password, user.password):
        return Response({'error': 'Current password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(serializer.validated_data['new_password'])
    user.save(update_fields=['password'])
    return Response({'message': 'Password updated successfully.'}, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def addresses(request):
    """
    Manage buyer receiving addresses.

    GET /api/auth/addresses/ - List current user's addresses
    POST /api/auth/addresses/ - Create a new receiving address
    """
    if request.method == 'GET':
        queryset = BuyerAddress.objects.filter(user=request.user).select_related('location')
        serializer = BuyerAddressSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    serializer = BuyerAddressSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    address = serializer.save(user=request.user)
    return Response(BuyerAddressSerializer(address, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def address_detail(request, address_id):
    """
    Retrieve/update/delete one buyer receiving address.

    GET /api/auth/addresses/{id}/
    PATCH /api/auth/addresses/{id}/
    DELETE /api/auth/addresses/{id}/
    """
    try:
        address = BuyerAddress.objects.select_related('location').get(id=address_id, user=request.user)
    except BuyerAddress.DoesNotExist:
        return Response({'error': 'Address not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(BuyerAddressSerializer(address, context={'request': request}).data)

    if request.method == 'PATCH':
        serializer = BuyerAddressSerializer(address, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(BuyerAddressSerializer(address, context={'request': request}).data)

    address.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_verification_code(request):
    """
    Request phone/email verification code.

    POST /api/auth/verification/request/
    """
    serializer = VerificationRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    channel = serializer.validated_data['channel']
    user = request.user
    client_ip = _get_client_ip(request)

    lockout_remaining = _get_lockout_remaining(user.id, channel)
    if lockout_remaining > 0:
        _log_verification_audit(
            'VERIFICATION_LOCKOUT',
            user,
            request,
            {
                'channel': channel,
                'phase': 'request',
                'retry_after_seconds': lockout_remaining,
            },
        )
        return Response(
            {
                'error': 'Verification temporarily locked due to repeated failed attempts.',
                'retry_after_seconds': lockout_remaining,
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    latest = AccountVerificationCode.objects.filter(
        user=user,
        channel=channel,
        purpose='ACCOUNT_VERIFICATION',
    ).order_by('-created_at').first()
    if latest:
        delta = timezone.now() - latest.created_at
        if delta.total_seconds() < VERIFICATION_RESEND_COOLDOWN_SECONDS:
            retry_after = int(VERIFICATION_RESEND_COOLDOWN_SECONDS - delta.total_seconds())
            return Response(
                {
                    'error': 'Please wait before requesting another verification code.',
                    'retry_after_seconds': retry_after,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

    user_rate_key = f'verification:requests:user:{user.id}:{channel}'
    ip_rate_key = f'verification:requests:ip:{client_ip}:{channel}'

    user_count = _increment_cache_counter(user_rate_key, 3600)
    ip_count = _increment_cache_counter(ip_rate_key, 3600)
    if user_count > VERIFICATION_MAX_REQUESTS_PER_HOUR:
        _log_verification_audit(
            'VERIFICATION_LOCKOUT',
            user,
            request,
            {
                'channel': channel,
                'phase': 'request',
                'reason': 'user_rate_limit',
            },
        )
        return Response(
            {'error': 'Verification request limit exceeded. Try again in one hour.'},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    if ip_count > VERIFICATION_MAX_REQUESTS_PER_HOUR_PER_IP:
        _log_verification_audit(
            'VERIFICATION_LOCKOUT',
            user,
            request,
            {
                'channel': channel,
                'phase': 'request',
                'reason': 'ip_rate_limit',
            },
        )
        return Response(
            {'error': 'Too many verification requests from this network. Try again in one hour.'},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    if channel == 'PHONE' and not user.phone_number:
        return Response({'error': 'Phone number not set on account.'}, status=status.HTTP_400_BAD_REQUEST)
    if channel == 'EMAIL' and not user.email:
        return Response({'error': 'Email address not set on account.'}, status=status.HTTP_400_BAD_REQUEST)

    if channel == 'PHONE' and user.phone_verified:
        _log_verification_audit(
            'VERIFICATION_REQUEST',
            user,
            request,
            {'channel': channel, 'already_verified': True},
        )
        return Response({'message': 'Phone number is already verified.', 'channel': channel}, status=status.HTTP_200_OK)
    if channel == 'EMAIL' and getattr(user, 'email_verified', False):
        _log_verification_audit(
            'VERIFICATION_REQUEST',
            user,
            request,
            {'channel': channel, 'already_verified': True},
        )
        return Response({'message': 'Email address is already verified.', 'channel': channel}, status=status.HTTP_200_OK)

    verification = _issue_verification_code(user, channel)

    _log_verification_audit(
        'VERIFICATION_REQUEST',
        user,
        request,
        {
            'channel': channel,
            'expires_at': verification.expires_at.isoformat(),
        },
    )

    if channel == 'EMAIL':
        send_mail(
            subject='Your account verification code',
            message=f'Your verification code is {verification.code}. It expires in 10 minutes.',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@optimistic.local'),
            recipient_list=[user.email],
            fail_silently=True,
        )
    elif channel == 'PHONE':
        # Send via configured SMS provider; don't block on failure
        try:
            send_sms(user.phone_number, f'Your Optimistic verification code is {verification.code}. It expires in {VERIFICATION_CODE_TTL_MINUTES} minutes.')
        except Exception:
            # Keep silent but audit already handled in adapter
            pass

    response = {
        'message': f'{channel.title()} verification code sent.',
        'channel': channel,
        'expires_at': verification.expires_at,
    }
    if settings.DEBUG:
        response['debug_code'] = verification.code

    return Response(response, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_verification_code(request):
    """
    Confirm phone/email verification code.

    POST /api/auth/verification/confirm/
    """
    serializer = VerificationConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    channel = serializer.validated_data['channel']
    code = serializer.validated_data['code']
    user = request.user

    lockout_remaining = _get_lockout_remaining(user.id, channel)
    if lockout_remaining > 0:
        _log_verification_audit(
            'VERIFICATION_LOCKOUT',
            user,
            request,
            {
                'channel': channel,
                'phase': 'confirm',
                'retry_after_seconds': lockout_remaining,
            },
        )
        return Response(
            {
                'error': 'Too many failed attempts. Please try again later.',
                'retry_after_seconds': lockout_remaining,
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    pending = AccountVerificationCode.objects.filter(
        user=user,
        channel=channel,
        purpose='ACCOUNT_VERIFICATION',
        used_at__isnull=True,
    ).order_by('-created_at')

    verification = pending.filter(code=code, expires_at__gt=timezone.now()).first()
    if verification is None:
        latest = pending.first()
        if latest and latest.attempts >= latest.max_attempts:
            retry_after = _set_lockout(user.id, channel)
            _log_verification_audit(
                'VERIFICATION_LOCKOUT',
                user,
                request,
                {
                    'channel': channel,
                    'phase': 'confirm',
                    'reason': 'max_attempts_previously_reached',
                    'retry_after_seconds': retry_after,
                },
            )
            return Response(
                {
                    'error': 'Maximum attempts reached. Verification is temporarily locked.',
                    'retry_after_seconds': retry_after,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        if latest and latest.attempts < latest.max_attempts:
            latest.attempts += 1
            latest.save(update_fields=['attempts'])
            if latest.attempts >= latest.max_attempts:
                retry_after = _set_lockout(user.id, channel)
                _log_verification_audit(
                    'VERIFICATION_LOCKOUT',
                    user,
                    request,
                    {
                        'channel': channel,
                        'phase': 'confirm',
                        'reason': 'max_attempts_reached',
                        'retry_after_seconds': retry_after,
                    },
                )
                return Response(
                    {
                        'error': 'Maximum attempts reached. Verification is temporarily locked.',
                        'retry_after_seconds': retry_after,
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )
        _log_verification_audit(
            'VERIFICATION_CONFIRM_FAILURE',
            user,
            request,
            {
                'channel': channel,
                'reason': 'invalid_or_expired_code',
            },
        )
        return Response({'error': 'Invalid or expired verification code.'}, status=status.HTTP_400_BAD_REQUEST)

    if not verification.can_attempt():
        return Response({'error': 'Verification code can no longer be used.'}, status=status.HTTP_400_BAD_REQUEST)

    verification.mark_used()

    if channel == 'PHONE':
        user.phone_verified = True
        user.phone_verified_at = timezone.now()
        user.save(update_fields=['phone_verified', 'phone_verified_at'])
    else:
        user.email_verified = True
        user.email_verified_at = timezone.now()
        user.save(update_fields=['email_verified', 'email_verified_at'])

    _mark_account_verified_if_ready(user)

    _log_verification_audit(
        'VERIFICATION_CONFIRM_SUCCESS',
        user,
        request,
        {
            'channel': channel,
            'phone_verified': user.phone_verified,
            'email_verified': user.email_verified,
            'status': user.status,
        },
    )

    return Response(
        {
            'message': f'{channel.title()} verification successful.',
            'verification_status': {
                'phone_verified': user.phone_verified,
                'email_verified': user.email_verified,
                'status': user.status,
            },
        },
        status=status.HTTP_200_OK,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verification_status(request):
    """
    Get current account verification state.

    GET /api/auth/verification/status/
    """
    user = request.user
    seller = getattr(user, 'seller', None)

    return Response(
        {
            'phone_verified': user.phone_verified,
            'phone_verified_at': user.phone_verified_at,
            'email_verified': getattr(user, 'email_verified', False),
            'email_verified_at': getattr(user, 'email_verified_at', None),
            'status': user.status,
            'is_account_verified': user.is_account_verified(),
            'seller': {
                'verified': seller.verified,
                'verification_status': seller.verification_status,
            }
            if seller
            else None,
            'policy': {
                'code_ttl_minutes': VERIFICATION_CODE_TTL_MINUTES,
                'resend_cooldown_seconds': VERIFICATION_RESEND_COOLDOWN_SECONDS,
                'max_requests_per_hour': VERIFICATION_MAX_REQUESTS_PER_HOUR,
                'max_requests_per_hour_per_ip': VERIFICATION_MAX_REQUESTS_PER_HOUR_PER_IP,
                'lockout_seconds': VERIFICATION_LOCKOUT_SECONDS,
            },
            'lockouts': {
                'phone_retry_after_seconds': _get_lockout_remaining(user.id, 'PHONE'),
                'email_retry_after_seconds': _get_lockout_remaining(user.id, 'EMAIL'),
            },
        }
    )
