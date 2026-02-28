from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class Review(models.Model):
    """
    Product and seller reviews - the trust foundation.
    
    Design Principles:
    - Buyer-only: Only buyers can review (prevents seller self-reviews)
    - Order-linked: Must have purchased to review (verified purchase)
    - Permanent: Reviews cannot be deleted (prevents censorship)
    - Immutable: Once posted, cannot be edited (prevents manipulation)
    
    Trust Mechanics:
    - unique_together: One review per order per reviewer
    - Prevents spam (can't review same order 100 times)
    - Forces honest feedback (can't delete bad review)
    - Order link proves purchase (not fake reviews)
    
    Why Three ForeignKeys?
    - order: Links to purchase (verified purchase badge)
    - product: What is being reviewed (product page displays these)
    - seller: Who sold it (seller reputation)
    - reviewer: Who wrote review (accountability)
    
    Rating Scale: 1-5 stars
    - 1 star: Terrible, major issues
    - 2 stars: Poor, disappointed  
    - 3 stars: Okay, met basic expectations
    - 4 stars: Good, happy with purchase
    - 5 stars: Excellent, exceeded expectations
    
    Future Enhancements:
    - Helpful votes (upvote/downvote reviews)
    - Review images (photo proof)
    - Seller responses (engage with feedback)
    - Verified purchase badge (show in UI)
    """
    
    # Order link: Proves this is a verified purchase
    # CASCADE: If order deleted, reviews deleted too
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    
    # Product link: What is being reviewed?
    # CASCADE: If product deleted, reviews deleted too
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    
    # Seller link: Who sold this product?
    # CASCADE: If seller deleted, reviews deleted too
    # Used for seller reputation calculations
    seller = models.ForeignKey(
        'sellers.Seller',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    
    # Reviewer: Who wrote this review?
    # CASCADE: If user deleted, reviews stay (for data integrity)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_given'
    )

    # Rating: 1-5 stars (validated by MinValueValidator/MaxValueValidator)
    # IntegerField instead of PositiveSmallIntegerField for validator support
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1-5 stars: 1=terrible, 5=excellent"
    )
    
    # Comment: Detailed feedback (required, not optional)
    # Buyers must explain their rating
    comment = models.TextField(
        help_text="Explain your rating: What was good or bad?"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
        unique_together = ['order', 'reviewer']  # One review per order

    def __str__(self):
        return f"Review by {self.reviewer.username} - {self.rating}⭐"
    
    def clean(self):
        """
        Business logic validation - enforces review rules.
        
        Rules Enforced:
        1. Can only review DELIVERED orders
        2. Cannot review own products (buyer ≠ seller)
        3. Must be the buyer of the order
        
        Called automatically by Django Admin and serializers.
        """
        super().clean()
        
        # Rule 1: Can only review DELIVERED orders
        if self.order.status != 'DELIVERED':
            raise ValidationError({
                'order': f'Can only review delivered orders. Current status: {self.order.get_status_display()}'
            })
        
        # Rule 2: Cannot review own products
        if self.product.seller.user == self.reviewer:
            raise ValidationError({
                'product': 'Cannot review your own products.'
            })
        
        # Rule 3: Must be the buyer of the order
        if self.order.buyer != self.reviewer:
            raise ValidationError({
                'order': 'Can only review your own orders.'
            })
    
    def save(self, *args, **kwargs):
        """
        Override save to prevent updates after creation.
        
        Business Rule: Reviews are immutable (cannot be edited).
        
        Why?
        - Prevents manipulation after posting
        - Maintains trust and transparency
        - Historical accuracy
        
        Exception: Admin can delete offensive reviews via Django Admin.
        """
        if self.pk:
            raise ValidationError('Reviews cannot be edited once posted. This maintains trust and transparency.')
        
        # Run validation before saving
        self.full_clean()
        super().save(*args, **kwargs)


class Report(models.Model):
    """
    Trust enforcement - flag problematic content.
    
    Purpose: Let users report issues for admin review
    
    What Can Be Reported? Products, Sellers, Reviews
    
    Report Flow:
    1. User finds problem (fake product, spam review)
    2. User clicks 'Report', selects reason, explains
    3. Report created (status=OPEN)
    4. Admin reviews in Django Admin (status=REVIEWING)
    5. Admin takes action (suspend, delete) (status=ACTIONED)
    6. Or dismisses if not a violation (status=DISMISSED)
    
    Trust Mechanics:
    - Reporter accountability (reporter FK)
    - Admin final authority (not mob rule)
    - Action log (admin_notes tracks what was done)
    - Polymorphic reference (target_type + target_id)
    
    Polymorphic Pattern:
    - target_type: 'PRODUCT', 'SELLER', or 'REVIEW'
    - target_id: ID of the reported item
    - Frontend: /report?type=PRODUCT&id=5
    - Admin: Looks up product #5 and reviews report
    
    Reason Categories:
    - FAKE: Counterfeit, not as described
    - SCAM: Fraudulent, never delivered
    - MISLEADING: False claims, wrong info
    - SPAM: Repetitive, promotional
    - INAPPROPRIATE: Offensive, harmful
    - OTHER: Doesn't fit above (explain in description)
    
    Actions Admin Can Take:
    - Suspend product (ACTIVE → SUSPENDED)
    - Unverify seller (verified → False)
    - Delete spam review
    - Ban user (is_active → False)
    - Nothing (false report)
    
    Future: Auto-suspend threshold, appeal process, analytics
    """
    TARGET_TYPE_CHOICES = (
        ('PRODUCT', 'Product'),
        ('SELLER', 'Seller'),
        ('REVIEW', 'Review'),
    )

    REASON_CHOICES = (
        ('FAKE', 'Fake Product'),
        ('SCAM', 'Scam/Fraud'),
        ('MISLEADING', 'Misleading Information'),
        ('SPAM', 'Spam'),
        ('INAPPROPRIATE', 'Inappropriate Content'),
        ('OTHER', 'Other'),
    )

    STATUS_CHOICES = (
        ('OPEN', 'Open'),              # Newly filed
        ('REVIEWING', 'Under Review'), # Admin investigating
        ('ACTIONED', 'Action Taken'),  # Admin took action
        ('DISMISSED', 'Dismissed'),    # Not a violation
    )

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports_made'
    )

    target_type = models.CharField(max_length=10, choices=TARGET_TYPE_CHOICES)
    target_id = models.IntegerField(help_text='ID of reported item')

    reason = models.CharField(max_length=15, choices=REASON_CHOICES)
    description = models.TextField()

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPEN')
    admin_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'
        ordering = ['-created_at']

    def __str__(self):
        return f"Report: {self.get_target_type_display()} #{self.target_id} - {self.get_status_display()}"
