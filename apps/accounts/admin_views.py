"""
Admin user management views
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db.models import Sum
from .models import User

get_user_model()


class IsSuperUser(IsAdminUser):
    """Permission class that only allows superusers"""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


@api_view(['POST'])
@permission_classes([IsSuperUser])
def create_admin_user(request):
    """
    Create a new admin user with specific permissions.
    POST /api/super-admin/create-admin/
    
    Body:
    {
        "username": "admin2",
        "email": "admin2@example.com",
        "password": "securepass123",
        "first_name": "John",
        "last_name": "Doe",
        "permissions": ["manage_users", "manage_products"]
    }
    """
    try:
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not request.data.get(field):
                return Response(
                    {'error': f'{field} is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Check if username or email already exists
        if User.objects.filter(username=request.data['username']).exists():
            return Response(
                {'error': 'Username already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(email=request.data['email']).exists():
            return Response(
                {'error': 'Email already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create admin user
        admin_user = User.objects.create(
            username=request.data['username'],
            email=request.data['email'],
            password=make_password(request.data['password']),
            first_name=request.data.get('first_name', ''),
            last_name=request.data.get('last_name', ''),
            role='ADMIN',
            status='ACTIVE',
            is_staff=True,  # Required for admin access
            is_active=True
        )
        
        # TODO: Store permissions in a separate AdminPermissions model
        # For now, we'll just create the user with ADMIN role
        
        return Response({
            'message': 'Admin user created successfully',
            'user': {
                'id': admin_user.pk,
                'username': admin_user.username,
                'email': admin_user.email,
                'role': admin_user.role
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_users(request):
    """
    Get all users for admin management.
    GET /api/admin/users/
    
    Query params:
    - role: Filter by role (ADMIN, SELLER, BUYER, COURIER)
    - is_active: Filter by active status (true/false)
    - search: Search by username or email
    """
    users = User.objects.all().order_by('-date_joined')
    
    # Apply filters
    role = request.query_params.get('role')
    if role:
        users = users.filter(role=role)
    
    is_active = request.query_params.get('is_active')
    if is_active is not None:
        users = users.filter(is_active=is_active.lower() == 'true')
    
    search = request.query_params.get('search')
    if search:
        users = users.filter(
            username__icontains=search
        ) | users.filter(
            email__icontains=search
        )
    
    # Serialize
    data = [{
        'id': u.pk,
        'username': u.username,
        'email': u.email,
        'role': u.role,
        'is_active': u.is_active,
        'date_joined': u.date_joined
    } for u in users]
    
    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_user_detail(request, user_id):
    """
    Get detailed information about a specific user.
    GET /api/admin/users/{user_id}/
    
    Returns:
    - Full user profile
    - Related seller/courier data if applicable
    - Activity statistics
    - Recent orders/sales
    """
    try:
        user = User.objects.get(pk=user_id)
        
        # Build base user data
        user_data = {
            'id': user.pk,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone_number': user.phone_number,
            'phone_verified': user.phone_verified,
            'email_verified': getattr(user, 'email_verified', False),
            'role': user.role,
            'status': user.status,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'suspended_at': user.suspended_at.isoformat() if user.suspended_at else None,
            'suspension_reason': user.suspension_reason,
        }

        # Trust review context: account verification and risk flags
        from .models import AccountVerificationCode
        latest_phone_code = AccountVerificationCode.objects.filter(user=user, channel='PHONE').order_by('-created_at').first()
        latest_email_code = AccountVerificationCode.objects.filter(user=user, channel='EMAIL').order_by('-created_at').first()
        total_codes_issued = AccountVerificationCode.objects.filter(user=user).count()
        total_failed_attempts = AccountVerificationCode.objects.filter(user=user).aggregate(total=Sum('attempts'))['total'] or 0

        user_data['trust_review'] = {
            'is_account_verified': user.is_account_verified() if hasattr(user, 'is_account_verified') else False,
            'phone_verified': user.phone_verified,
            'email_verified': getattr(user, 'email_verified', False),
            'total_codes_issued': total_codes_issued,
            'total_failed_code_attempts': int(total_failed_attempts),
            'latest_phone_verification_request_at': latest_phone_code.created_at.isoformat() if latest_phone_code else None,
            'latest_email_verification_request_at': latest_email_code.created_at.isoformat() if latest_email_code else None,
            'risk_flags': {
                'account_unverified': not (user.is_account_verified() if hasattr(user, 'is_account_verified') else False),
                'high_failed_code_attempts': int(total_failed_attempts) >= 10,
                'is_suspended': bool(user.suspended_at),
            },
        }
        
        # Add role-specific data
        if user.role == 'SELLER':
            from apps.sellers.models import Seller
            from apps.orders.models import OrderItem
            from apps.products.models import Product
            
            try:
                seller = Seller.objects.get(user=user)
                order_items = OrderItem.objects.filter(seller=seller)
                total_revenue = order_items.aggregate(total=Sum('price_snapshot'))['total'] or 0
                
                user_data['seller'] = {
                    'id': seller.pk,
                    'store_name': seller.store_name,
                    'description': seller.description,
                    'phone': seller.phone,
                    'business_name': seller.business_name,
                    'business_registration_number': seller.business_registration_number,
                    'tax_pin': seller.tax_pin,
                    'verified': seller.verified,
                    'verification_status': seller.verification_status,
                    'physical_address': seller.physical_address,
                    'town_city': seller.town_city,
                    'province': seller.province,
                    'primary_location': seller.primary_location.get_full_address() if seller.primary_location else '',
                    'profile_completion': seller.get_completion_percentage(),
                    'total_products': Product.objects.filter(seller=seller).count(),
                    'active_products': Product.objects.filter(seller=seller, status='ACTIVE').count(),
                    'pending_products': Product.objects.filter(seller=seller, status='PENDING_APPROVAL').count(),
                    'total_sales': order_items.count(),
                    'total_revenue': float(total_revenue),
                }

                verification = getattr(seller, 'kyc_documents', None)
                user_data['trust_review']['seller_kyc'] = {
                    'status': verification.status if verification else None,
                    'submitted_at': verification.submitted_at.isoformat() if verification and verification.submitted_at else None,
                    'reviewed_at': verification.reviewed_at.isoformat() if verification and verification.reviewed_at else None,
                    'reviewed_by': verification.reviewed_by.username if verification and verification.reviewed_by else None,
                    'rejection_reason': verification.rejection_reason if verification else None,
                    'has_id_front': bool(verification and verification.government_id_front),
                    'has_id_back': bool(verification and verification.government_id_back),
                    'has_selfie_with_id': bool(verification and verification.selfie_with_id),
                }
            except Seller.DoesNotExist:
                user_data['seller'] = None
        
        elif user.role == 'BUYER':
            from apps.orders.models import Order
            from .models import BuyerAddress
            
            orders = Order.objects.filter(buyer=user)
            user_data['buyer'] = {
                'total_orders': orders.count(),
                'completed_orders': orders.filter(status='DELIVERED').count(),
                'pending_orders': orders.filter(status='PENDING').count(),
                'active_orders': orders.filter(status__in=['PAID', 'READY_FOR_DELIVERY', 'IN_TRANSIT']).count(),
                'address_count': BuyerAddress.objects.filter(user=user).count(),
                'total_spent': float(sum(order.total_amount for order in orders)),
            }
        
        elif user.role == 'COURIER':
            from apps.logistics.models import Delivery, DeliveryPartner
            
            try:
                courier = DeliveryPartner.objects.get(user=user)
                user_data['courier'] = {
                    'id': courier.pk,
                    'name': courier.name,
                    'phone': courier.phone,
                    'email': courier.email,
                    'partner_type': courier.partner_type,
                    'service_area': courier.service_area,
                    'vehicle_type': courier.vehicle_type,
                    'id_number': courier.id_number,
                    'verified': courier.verified,
                    'is_active': courier.is_active,
                    'total_deliveries': Delivery.objects.filter(partner=courier).count(),
                }
            except DeliveryPartner.DoesNotExist:
                user_data['courier'] = None
        
        return Response(user_data, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def suspend_user(request, user_id):
    """
    Suspend a user account.
    POST /api/admin/users/{user_id}/suspend/
    """
    try:
        user = User.objects.get(pk=user_id)
        user.is_active = False
        user.save()
        
        return Response({
            'message': f'User {user.username} has been suspended',
            'user': {
                'id': user.pk,
                'username': user.username,
                'is_active': user.is_active
            }
        }, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def activate_user(request, user_id):
    """
    Activate a suspended user account.
    POST /api/admin/users/{user_id}/activate/
    """
    try:
        user = User.objects.get(pk=user_id)
        user.is_active = True
        user.save()
        
        return Response({
            'message': f'User {user.username} has been activated',
            'user': {
                'id': user.pk,
                'username': user.username,
                'is_active': user.is_active
            }
        }, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
