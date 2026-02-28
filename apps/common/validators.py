"""
Data Integrity Validators - Enforce database constraints and business rules.

Purpose: Centralized validation logic to maintain data consistency.

Categories:
1. Unique constraints (username, email, product names)
2. Reference integrity (prevent orphaned records)
3. Business rule validation (stock, price, status transitions)
4. Cascade protection (prevent critical data deletion)

Design Philosophy:
- Fail fast: Catch violations early in request lifecycle
- Clear errors: Return specific, actionable error messages
- Database-level: Use DB constraints where possible
- Application-level: Complex rules in Python
"""

from django.core.exceptions import ValidationError
from django.db import models


def validate_positive_price(value):
    """
    Ensure product price is non-negative.
    
    Business Rule: Cannot sell products with negative prices.
    
    Usage: Add to Product.price field validators
    """
    if value < 0:
        raise ValidationError('Price cannot be negative.')


def validate_stock_availability(value):
    """
    Ensure stock is non-negative.
    
    Business Rule: Cannot have negative inventory.
    
    Usage: Add to Product.stock field validators
    """
    if value < 0:
        raise ValidationError('Stock cannot be negative.')


def validate_order_total(value):
    """
    Ensure order total is positive.
    
    Business Rule: Orders must have positive value.
    
    Usage: Add to Order.total_amount field validators
    """
    if value <= 0:
        raise ValidationError('Order total must be greater than zero.')


def validate_rating(value):
    """
    Ensure rating is between 1 and 5.
    
    Business Rule: 5-star rating system.
    
    Usage: Add to Review.rating field validators
    """
    if not 1 <= value <= 5:
        raise ValidationError('Rating must be between 1 and 5.')


def validate_phone_number(value):
    """
    Validate Zambian phone number format.
    
    Accepted formats:
    - +260977123456 (international)
    - 0977123456 (local)
    - 260977123456 (without +)
    
    Business Rule: Only Zambian numbers (+260)
    
    Usage: Add to Seller.phone field validators
    """
    import re
    
    # Remove spaces and dashes
    clean_number = re.sub(r'[\s\-]', '', value)
    
    # Check formats
    patterns = [
        r'^\+260\d{9}$',   # +260977123456
        r'^0\d{9}$',       # 0977123456
        r'^260\d{9}$',     # 260977123456
    ]
    
    if not any(re.match(pattern, clean_number) for pattern in patterns):
        raise ValidationError(
            'Invalid phone number. Use format: +260977123456 or 0977123456'
        )


class ProductModelValidator:
    """
    Product model business logic validator.
    
    Enforces:
    1. Verified sellers only create products
    2. Unique product names per seller
    3. Valid status transitions
    4. Cannot delete products with orders
    """
    
    @staticmethod
    def validate_seller_verified(seller):
        """
        Ensure only verified sellers can publish products.
        
        Business Rule: Trust gate - unverified sellers cannot list.
        """
        if not seller.verified:
            raise ValidationError(
                'Only verified sellers can publish products. '
                'Please wait for seller verification.'
            )
    
    @staticmethod
    def validate_unique_product_name(seller, name, product_id=None):
        """
        Ensure product name is unique per seller.
        
        Business Rule: Seller cannot have duplicate product names.
        
        Why? Prevents confusion in seller dashboard.
        """
        from apps.products.models import Product
        
        query = Product.objects.filter(seller=seller, name=name)
        if product_id:
            query = query.exclude(id=product_id)
        
        if query.exists():
            raise ValidationError(
                f'You already have a product named "{name}". '
                'Please use a different name.'
            )
    
    @staticmethod
    def validate_status_transition(old_status, new_status):
        """
        Validate product status transitions.
        
        Valid Transitions:
        - DRAFT → PENDING_APPROVAL (seller submits)
        - PENDING_APPROVAL → ACTIVE (admin approves)
        - PENDING_APPROVAL → DRAFT (admin rejects)
        - ACTIVE → SUSPENDED (admin suspends)
        - SUSPENDED → ACTIVE (admin reinstates)
        - ANY → ARCHIVED (permanent archive)
        
        Invalid Transitions:
        - DRAFT → ACTIVE (must go through approval)
        - SUSPENDED → DRAFT (cannot edit while suspended)
        """
        valid_transitions = {
            'DRAFT': ['PENDING_APPROVAL', 'ARCHIVED'],
            'PENDING_APPROVAL': ['ACTIVE', 'DRAFT', 'ARCHIVED'],
            'ACTIVE': ['SUSPENDED', 'ARCHIVED'],
            'SUSPENDED': ['ACTIVE', 'ARCHIVED'],
            'ARCHIVED': []  # Final state, no transitions
        }
        
        if new_status not in valid_transitions.get(old_status, []):
            raise ValidationError(
                f'Invalid status transition: {old_status} → {new_status}. '
                f'Valid transitions from {old_status}: {", ".join(valid_transitions.get(old_status, []))}'
            )
    
    @staticmethod
    def validate_can_delete(product):
        """
        Check if product can be deleted.
        
        Business Rule: Cannot delete products with orders.
        Alternative: Archive instead.
        """
        # TODO: Check OrderItem when implemented
        # if product.orderitems.exists():
        #     raise ValidationError(
        #         'Cannot delete products with orders. '
        #         'Use archive instead to preserve order history.'
        #     )
        
        if product.status != 'DRAFT':
            raise ValidationError(
                'Can only delete DRAFT products. '
                'Use archive for published products.'
            )


class OrderModelValidator:
    """
    Order model business logic validator.
    
    Enforces:
    1. Valid status transitions
    2. Inventory availability
    3. Cannot delete orders (only cancel)
    """
    
    @staticmethod
    def validate_status_transition(old_status, new_status):
        """
        Validate order status transitions.
        
        Valid Transitions:
        - PENDING → PAID (payment successful)
        - PENDING → CANCELLED (buyer cancels)
        - PAID → READY_FOR_DELIVERY (seller confirms)
        - PAID → CANCELLED (buyer cancels before shipping)
        - READY_FOR_DELIVERY → IN_TRANSIT (delivery partner picks up)
        - IN_TRANSIT → DELIVERED (buyer confirms)
        - IN_TRANSIT → DELIVERED (system auto-confirms)
        
        Invalid Transitions:
        - IN_TRANSIT → CANCELLED (too late, already shipped)
        - DELIVERED → anything (final state)
        - CANCELLED → anything (final state)
        """
        valid_transitions = {
            'PENDING': ['PAID', 'CANCELLED'],
            'PAID': ['READY_FOR_DELIVERY', 'CANCELLED'],
            'READY_FOR_DELIVERY': ['IN_TRANSIT'],
            'IN_TRANSIT': ['DELIVERED'],
            'DELIVERED': [],  # Final state
            'CANCELLED': []   # Final state
        }
        
        if new_status not in valid_transitions.get(old_status, []):
            raise ValidationError(
                f'Invalid status transition: {old_status} → {new_status}. '
                f'Valid transitions from {old_status}: {", ".join(valid_transitions.get(old_status, []))}'
            )
    
    @staticmethod
    def validate_inventory_availability(order):
        """
        Check if products have sufficient stock.
        
        Business Rule: Cannot fulfill orders without inventory.
        
        TODO: Implement when OrderItem model is ready.
        """
        # for item in order.items.all():
        #     if item.product.stock < item.quantity:
        #         raise ValidationError(
        #             f'Insufficient stock for {item.product.name}. '
        #             f'Available: {item.product.stock}, Requested: {item.quantity}'
        #         )
        pass
    
    @staticmethod
    def validate_can_delete(order):
        """
        Check if order can be deleted.
        
        Business Rule: Orders cannot be deleted, only cancelled.
        Why? Financial audit trail, historical record.
        """
        raise ValidationError(
            'Orders cannot be deleted. Use cancel() instead to maintain audit trail.'
        )


class ReviewModelValidator:
    """
    Review model business logic validator.
    
    Enforces:
    1. Only DELIVERED orders can be reviewed
    2. One review per order
    3. Cannot review own products
    4. Reviews are immutable
    """
    
    @staticmethod
    def validate_order_delivered(order):
        """
        Ensure order is delivered before review.
        
        Business Rule: Can only review after receiving product.
        """
        if order.status != 'DELIVERED':
            raise ValidationError(
                f'Can only review delivered orders. '
                f'Current status: {order.get_status_display()}'
            )
    
    @staticmethod
    def validate_unique_review(order, reviewer):
        """
        Ensure one review per order.
        
        Business Rule: Prevent spam reviews.
        """
        from apps.reviews.models import Review
        
        if Review.objects.filter(order=order, reviewer=reviewer).exists():
            raise ValidationError(
                'You have already reviewed this order.'
            )
    
    @staticmethod
    def validate_not_own_product(product, reviewer):
        """
        Ensure user is not reviewing own product.
        
        Business Rule: Sellers cannot review own products.
        """
        if product.seller.user == reviewer:
            raise ValidationError(
                'Cannot review your own products.'
            )
    
    @staticmethod
    def validate_immutable(review):
        """
        Ensure reviews cannot be edited after creation.
        
        Business Rule: Reviews are permanent for trust.
        """
        if review.pk:
            raise ValidationError(
                'Reviews cannot be edited once posted. '
                'This maintains trust and transparency.'
            )


# Database-level constraints (for migrations)
class UniqueConstraints:
    """
    Database unique constraints to enforce in migrations.
    
    Usage in models:
        class Meta:
            constraints = [
                models.UniqueConstraint(
                    fields=['seller', 'name'],
                    name='unique_product_name_per_seller'
                )
            ]
    """
    
    PRODUCT_UNIQUE_NAME_PER_SELLER = models.UniqueConstraint(
        fields=['seller', 'name'],
        name='unique_product_name_per_seller'
    )
    
    REVIEW_ONE_PER_ORDER = models.UniqueConstraint(
        fields=['order', 'reviewer'],
        name='one_review_per_order'
    )
    
    USER_UNIQUE_EMAIL = models.UniqueConstraint(
        fields=['email'],
        name='unique_user_email'
    )
    
    USER_UNIQUE_USERNAME = models.UniqueConstraint(
        fields=['username'],
        name='unique_user_username'
    )
