"""
Role-based permissions for API access control.
"""
from rest_framework.permissions import BasePermission


class IsSeller(BasePermission):
    """
    Permission: User must be authenticated and have SELLER role.
    
    Usage: Seller-only endpoints (create products, view dashboard)
    
    How it works:
    1. DRF calls has_permission() before view executes
    2. We check request.user.role == 'SELLER'
    3. Return True = access granted, False = 403 Forbidden
    
    Why custom permission?
    - Built-in DjangoModelPermissions don't understand our role system
    - Cleaner than checking role in every view
    - Reusable across all seller endpoints
    
    Example:
        class SellerViewSet(viewsets.ModelViewSet):
            permission_classes = [IsAuthenticated, IsSeller]
            # Only authenticated sellers can access
    """
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role == 'SELLER'
        )


class IsVerifiedSeller(BasePermission):
    """
    Permission: User must be a verified seller.
    
    Usage: Publishing products, marking orders as shipped
    
    Difference from IsSeller:
    - IsSeller: Has seller role (can view dashboard, edit drafts)
    - IsVerifiedSeller: Seller + verified=True (can publish products)
    
    Trust Layer:
    - Unverified sellers can prepare products (drafts)
    - But cannot make products visible to public
    - Admin must verify seller first
    
    Implementation:
    1. Check if user is seller (has role)
    2. Check if seller profile exists (hasattr check)
    3. Check if seller.verified == True
    
    Example:
        @action(detail=True, methods=['post'])
        def publish(self, request, pk=None):
            permission_classes = [IsVerifiedSeller]
            # Only verified sellers can publish
    """
    def has_permission(self, request, view) -> bool:  # type: ignore[override]
        return bool(
            request.user 
            and request.user.is_authenticated 
            and request.user.role == 'SELLER'
            and hasattr(request.user, 'seller')
            and request.user.seller.verified
        )


class IsBuyer(BasePermission):
    """
    Permission: User must be authenticated and have BUYER role.
    """
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role == 'BUYER'
        )


class IsAdmin(BasePermission):
    """
    Permission: User must be admin or superuser.
    """
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and (request.user.role == 'ADMIN' or request.user.is_superuser)
        )


class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission: Owner can edit, others can only read.
    """
    def has_object_permission(self, request, view, obj) -> bool:  # type: ignore[override]
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # For products, check seller ownership
        if hasattr(obj, 'seller'):
            return bool(obj.seller.user == request.user)
        
        # For sellers, check user ownership
        if hasattr(obj, 'user'):
            return bool(obj.user == request.user)
        
        return False


class IsCourier(BasePermission):
    """
    Permission: User must be authenticated and have COURIER role.
    
    Usage: Courier-only endpoints (update delivery status, view assigned deliveries)
    
    Separation of Concerns:
    - Couriers cannot place orders
    - Couriers cannot manage products
    - Couriers only interact with delivery entities
    """
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role == 'COURIER'
        )


class IsVerifiedCourier(BasePermission):
    """
    Permission: User must be a verified courier.
    
    Usage: Update delivery status, upload proof of delivery
    
    Trust Layer:
    - Unverified couriers can view their profile
    - But cannot be assigned deliveries
    - Admin must verify courier first
    
    Implementation:
    1. Check if user is courier (has role)
    2. Check if delivery partner profile exists
    3. Check if delivery_partner_profile.verified == True
    """
    def has_permission(self, request, view) -> bool:  # type: ignore[override]
        return bool(
            request.user 
            and request.user.is_authenticated 
            and request.user.role == 'COURIER'
            and hasattr(request.user, 'delivery_partner')
            and request.user.delivery_partner.verified
        )


class CanManageEscrow(BasePermission):
    """Permission: Only admins can manage escrow (freeze/release funds)."""
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.is_admin()
        )


class CanResolveDisputes(BasePermission):
    """Permission: Only admins can resolve disputes (final arbitration)."""
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.is_admin()
        )


class CanViewAuditLogs(BasePermission):
    """Permission: Only admins can view audit logs (immutable records)."""
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.is_admin()
        )


class CanSuspendUsers(BasePermission):
    """Permission: Only admins can suspend/reinstate users."""
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.is_admin()
        )
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role == 'COURIER'
            and hasattr(request.user, 'delivery_partner_profile')
            and request.user.delivery_partner_profile.verified
        )

