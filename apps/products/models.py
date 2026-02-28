from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    """
    Custom manager that excludes soft-deleted objects by default.
    
    Usage:
        Product.objects.all()  # Excludes deleted
        Product.all_objects.all()  # Includes deleted
        Product.objects.deleted()  # Only deleted
    """
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)
    
    def deleted(self):
        """Return only soft-deleted objects."""
        return super().get_queryset().filter(deleted_at__isnull=False)
    
    def with_deleted(self):
        """Return all objects including soft-deleted."""
        return super().get_queryset()


class Category(models.Model):
    """
    Product categories - organize the marketplace.
    
    Purpose: Group similar products for easy browsing
    
    Design: Flat structure (no nested categories for MVP)
    - Simpler to implement
    - Easier UI rendering
    - Can add parent FK later (backward compatible)
    
    Examples: Electronics, Fashion, Food, Home & Garden
    
    Features:
    - is_active: Hide without deleting (products stay linked)
    - Slug: SEO-friendly URLs (/category/electronics/)
    - Unique names: No duplicate categories
    
    Admin Workflow:
    1. Create categories before products
    2. Set is_active=False to hide temporarily
    3. Reactivate anytime without losing products
    
    Future: Nested categories, images, ordering, per-category commissions
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name
    
    def approve(self):
        """
        Admin action: Approve product and make it visible to buyers.
        
        Transition: PENDING_APPROVAL → ACTIVE
        
        Business Rule: Only admins can approve.
        Trigger: Notification sent to seller.
        """
        if self.status != 'PENDING_APPROVAL':
            raise ValidationError(f'Can only approve PENDING_APPROVAL products. Current status: {self.status}')
        
        self.status = 'ACTIVE'
        self.save()
    
    def suspend(self, reason=''):
        """
        Admin action: Suspend product for policy violations.
        
        Transition: ACTIVE → SUSPENDED
        
        Business Rule: Only admins can suspend.
        Trigger: Notification sent to seller with reason.
        """
        if self.status != 'ACTIVE':
            raise ValidationError(f'Can only suspend ACTIVE products. Current status: {self.status}')
        
        self.status = 'SUSPENDED'
        self.save()
    
    def archive(self):
        """
        Admin/Seller action: Archive product permanently.
        
        Transition: ANY → ARCHIVED
        
        Business Rule: Cannot delete products with orders; archive instead.
        Effect: Not visible in searches, historical reference only.
        """
        self.status = 'ARCHIVED'
        self.save()
    
    def can_edit(self):
        """
        Check if product can be edited by seller.
        
        Rules:
        - DRAFT: Fully editable
        - PENDING_APPROVAL: Cannot edit (revert to DRAFT first)
        - ACTIVE: Limited edits (price, stock) - full edit requires admin re-approval
        - SUSPENDED: Cannot edit (appeal required)
        - ARCHIVED: Cannot edit (historical record)
        """
        return self.status in ['DRAFT', 'ACTIVE']
    
    def can_delete(self):
        """
        Check if product can be deleted.
        
        Rule: Cannot delete products referenced in orders.
        Alternative: Archive instead.
        """
        # Check if product has any orders (via OrderItem when implemented)
        # For now, allow deletion of DRAFT only
        return self.status == 'DRAFT'
    
    def soft_delete(self):
        """
        Soft delete product (mark as deleted without removing from database).
        
        Use Case: Remove product while preserving order history
        Rule: Cannot soft delete products with active orders
        """
        # Check for active orders
        from apps.orders.models import OrderItem
        active_orders = OrderItem.objects.filter(
            product=self,
            order__status__in=['PENDING', 'PAID', 'READY_FOR_DELIVERY', 'IN_TRANSIT']
        ).exists()
        if active_orders:
            raise ValidationError('Cannot delete product with active orders. Archive instead.')
        
        self.deleted_at = timezone.now()
        self.save()
    
    def restore(self):
        """Restore soft-deleted product."""
        self.deleted_at = None
        self.save()


class Product(models.Model):
    """
    Product catalog entry - the core of the marketplace.
    
    Product Lifecycle:
    1. Seller creates product → status=DRAFT (not visible to public)
    2. Admin reviews and approves → status=ACTIVE (public can see)
    3. If issues found → status=SUSPENDED (removed from public view)
    
    Business Rules (Enforced):
    - Only verified sellers can publish (checked in clean())
    - Price must be ≥ 0 (validated in clean() and serializer)
    - Stock must be ≥ 0 (PositiveIntegerField enforces this)
    - Public can only see ACTIVE products (filtered in views)
    
    Why This Status Flow?
    - Prevents scam products from going live automatically
    - Admin has quality control gate
    - Allows sellers to prepare products before publishing
    - Platform maintains trust through moderation
    """
    
    # Status workflow: Controls product visibility and lifecycle
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),                  # Seller is still working on it
        ('PENDING_APPROVAL', 'Pending Approval'),  # Submitted for admin review
        ('ACTIVE', 'Active'),                # Live and visible to buyers
        ('SUSPENDED', 'Suspended'),          # Hidden by admin (policy violation)
        ('ARCHIVED', 'Archived'),            # Historical, not visible in searches
    )

    # Seller relationship: Who owns this product?
    # CASCADE: If seller deleted, all their products deleted too
    # related_name='products': Access via seller.products.all()
    seller = models.ForeignKey(
        'sellers.Seller',
        on_delete=models.CASCADE,
        related_name='products'
    )
    
    # Category relationship: What type of product is this?
    # SET_NULL: If category deleted, product stays but category=None
    # null=True: Products can exist without category (temporary)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products'
    )
    
    # Product information fields
    name = models.CharField(max_length=150, help_text="Product title visible to buyers", db_index=True)
    description = models.TextField(help_text="Detailed product description")
    
    # Pricing: max_digits=10, decimal_places=2 means max 99,999,999.99 ZMW
    # Enough for anything from K5 (cheap item) to K50,000,000 (real estate)
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Price in Zambian Kwacha (ZMW)",
        db_index=True
    )
    
    # Stock: PositiveIntegerField automatically prevents negative values
    # 0 stock = out of stock (still visible but can't order)
    stock = models.PositiveIntegerField(
        default=0,
        help_text="Available quantity"
    )
    
    # Status: Controls visibility (DRAFT=hidden, ACTIVE=visible, SUSPENDED=hidden)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='DRAFT',
        help_text="Only ACTIVE products are visible to buyers",
        db_index=True
    )
    
    # Timestamps: Track creation and modifications
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)  # Set once, never changes
    updated_at = models.DateTimeField(auto_now=True)      # Updates on every save()
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Soft delete timestamp (preserves product history for orders)'
    )
    
    # Managers
    objects = SoftDeleteManager()  # Default: excludes deleted
    all_objects = models.Manager()  # Includes deleted

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']

    def clean(self):
        """
        Model-level validation (Django calls this before saving).
        
        Why validate here and not just in the form/serializer?
        - Forms/serializers can be bypassed (Django shell, management commands)
        - Model is the single source of truth
        - Database integrity is paramount
        
        Validation order:
        1. Django validates field types (DecimalField, PositiveIntegerField)
        2. This clean() method runs custom business logic
        3. Database constraints run last (unique, foreign key, etc.)
        """
        # Price validation: Prevent negative prices
        # Note: PositiveIntegerField doesn't exist for DecimalField
        if self.price < 0:
            raise ValidationError("Price cannot be negative")
        
        # Stock validation: Although PositiveIntegerField helps, double-check
        if self.stock < 0:
            raise ValidationError("Stock cannot be negative")
        
        # Critical business rule: Only verified sellers can have ACTIVE products
        # This prevents unverified sellers from bypassing the approval process
        if self.status == 'ACTIVE' and not self.seller.verified:
            raise ValidationError(
                "Only verified sellers can publish products. "
                "Please wait for admin verification."
            )

    def __str__(self) -> str:
        return f"{self.name} - {self.status}"


class ProductImage(models.Model):
    """
    Product images - multiple images per product (max 6).
    
    Business Rules:
    - Each product can have 1-6 images
    - One image must be marked as primary
    - Primary image is used for thumbnails/listings
    - Validation enforces max 6 images
    """
    MAX_IMAGES_PER_PRODUCT = 6
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='products/')
    is_primary = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'
    
    def clean(self):
        """Validate max images per product before saving."""
        if not self.pk:  # Only check on creation
            existing_count = ProductImage.objects.filter(product=self.product).count()
            if existing_count >= self.MAX_IMAGES_PER_PRODUCT:
                raise ValidationError(
                    f'Product can have maximum {self.MAX_IMAGES_PER_PRODUCT} images. '
                    f'Please delete an existing image before uploading a new one.'
                )
    
    def save(self, *args, **kwargs):
        """Run validation before saving."""
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.product.name}"
