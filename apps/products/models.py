from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal


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
    attributes = models.JSONField(
        default=dict,
        blank=True,
        help_text='Category-specific attributes (e.g., RAM, storage, size, material).'
    )
    
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
    reserved_stock = models.PositiveIntegerField(
        default=0,
        help_text='Units temporarily reserved by active checkouts.'
    )
    weight_kg = models.DecimalField(max_digits=8, decimal_places=3, default=Decimal('0.000'))
    length_cm = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    width_cm = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    height_cm = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    shipping_class = models.CharField(max_length=30, default='STANDARD')
    tax_category = models.CharField(max_length=30, default='STANDARD')

    @property
    def available_stock(self):
        """Units available to new checkouts; stock remains physical on-hand."""
        return max(self.stock - self.reserved_stock, 0)

    def dimensional_weight_kg(self, divisor=Decimal('5000')):
        return (self.length_cm * self.width_cm * self.height_cm / divisor).quantize(Decimal('0.001'))

    def chargeable_weight_kg(self, divisor=Decimal('5000')):
        return max(self.weight_kg, self.dimensional_weight_kg(divisor))
    
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

    def submit_for_approval(self):
        """Seller action: submit draft product for admin review."""
        if self.status != 'DRAFT':
            raise ValidationError(f'Can only submit DRAFT products. Current status: {self.status}')
        self.status = 'PENDING_APPROVAL'
        self.save(update_fields=['status', 'updated_at'])

    def approve(self):
        """Admin action: approve product and make it public."""
        if self.status != 'PENDING_APPROVAL':
            raise ValidationError(f'Can only approve PENDING_APPROVAL products. Current status: {self.status}')
        self.status = 'ACTIVE'
        self.save(update_fields=['status', 'updated_at'])

    def suspend(self, reason=''):
        """Admin action: suspend active product."""
        if self.status != 'ACTIVE':
            raise ValidationError(f'Can only suspend ACTIVE products. Current status: {self.status}')
        self.status = 'SUSPENDED'
        self.save(update_fields=['status', 'updated_at'])

    def archive(self):
        """Admin/seller action: archive product."""
        self.status = 'ARCHIVED'
        self.save(update_fields=['status', 'updated_at'])

    def can_edit(self):
        return self.status in ['DRAFT', 'ACTIVE']

    def can_delete(self):
        return self.status == 'DRAFT'

    def soft_delete(self):
        # Keep order history intact while hiding product from default manager.
        from apps.orders.models import OrderItem
        active_orders = OrderItem.objects.filter(
            product=self,
            order__status__in=['PENDING', 'PAID', 'READY_FOR_DELIVERY', 'IN_TRANSIT']
        ).exists()
        if active_orders:
            raise ValidationError('Cannot delete product with active orders. Archive instead.')

        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at', 'updated_at'])

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=['deleted_at', 'updated_at'])

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
        if self.reserved_stock < 0 or self.reserved_stock > self.stock:
            raise ValidationError('Reserved stock must be between zero and physical stock.')
        
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
