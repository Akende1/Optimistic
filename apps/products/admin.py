from django.contrib import admin
from .models import Category, Product, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Category admin.
    """
    list_display = ['name', 'slug', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


class ProductImageInline(admin.TabularInline):
    """
    Inline admin for product images.
    """
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Product admin - the moderation control center.
    
    Purpose: Give admins tools to manage the marketplace catalog
    
    Admin Powers:
    - Approve products (DRAFT → ACTIVE) - make visible to public
    - Suspend products (ACTIVE → SUSPENDED) - remove from marketplace
    - Bulk actions for mass moderation
    - Filter by status, category, seller
    - Search by name, description, seller name
    
    Workflow:
    1. Seller creates product → status=DRAFT (not visible)
    2. Admin reviews product in this interface
    3. Admin selects product(s) and chooses action:
       - 'Approve selected products' → ACTIVE (public can see)
       - 'Suspend selected products' → SUSPENDED (hidden)
    
    Why This Workflow?
    - Quality control: Prevent scam/inappropriate products
    - Trust building: Buyers know products are vetted
    - Policy enforcement: Remove violations quickly
    - Seller accountability: Cannot bypass approval
    
    List Display: What columns show in product list
    - name: Product title
    - seller: Who is selling
    - category: Product type
    - price: How much it costs
    - stock: Inventory level
    - status: Current lifecycle stage
    - created_at: When listed
    """
    list_display = ['name', 'seller', 'category', 'price', 'stock', 'status', 'created_at']
    list_filter = ['status', 'category', 'created_at']  # Sidebar filters
    search_fields = ['name', 'description', 'seller__store_name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ProductImageInline]
    
    actions = ['approve_products', 'suspend_products', 'draft_products']
    
    def approve_products(self, request, queryset):
        """Approve products (set to ACTIVE)."""
        # Only approve products from verified sellers
        verified_products = queryset.filter(seller__verified=True)
        count = verified_products.update(status='ACTIVE')
        
        unverified = queryset.filter(seller__verified=False).count()
        if unverified > 0:
            self.message_user(
                request, 
                f'{unverified} product(s) not approved (seller not verified).',
                level='warning'
            )
        
        self.message_user(request, f'{count} product(s) approved successfully.')
    approve_products.short_description = 'Approve selected products'
    
    def suspend_products(self, request, queryset):
        """Suspend products."""
        count = queryset.update(status='SUSPENDED')
        self.message_user(request, f'{count} product(s) suspended.')
    suspend_products.short_description = 'Suspend selected products'
    
    def draft_products(self, request, queryset):
        """Set products to draft."""
        count = queryset.update(status='DRAFT')
        self.message_user(request, f'{count} product(s) set to draft.')
    draft_products.short_description = 'Set to draft'
    
    fieldsets = (
        ('Product Information', {
            'fields': ('seller', 'category', 'name', 'description')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'stock')
        }),
        ('Status', {
            'fields': ('status',),
            'description': 'Products must be ACTIVE to be visible to buyers.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    """
    Product image admin.
    """
    list_display = ['product', 'is_primary', 'image']
    list_filter = ['is_primary']
    search_fields = ['product__name']
