from django.contrib import admin
from django.utils import timezone
from .models import DeliveryPartner, Delivery


@admin.register(DeliveryPartner)
class DeliveryPartnerAdmin(admin.ModelAdmin):
    """
    Delivery partner admin.
    """
    list_display = ['name', 'partner_type', 'service_area', 'is_active', 'phone']
    list_filter = ['partner_type', 'is_active']
    search_fields = ['name', 'phone', 'service_area']

    fieldsets = (
        ('Partner Information', {
            'fields': ('name', 'phone', 'partner_type', 'service_area')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    """
    Delivery management admin.
    Admin assigns partners and updates delivery status.
    """
    list_display = ['order', 'status', 'partner', 'delivery_fee', 'created_at', 'delivered_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order__id', 'delivery_address']
    readonly_fields = ['created_at', 'assigned_at', 'picked_up_at', 'delivered_at']

    actions = ['assign_delivery', 'mark_picked_up', 'mark_in_transit', 'mark_delivered']

    def assign_delivery(self, request, queryset):
        """Mark deliveries as assigned."""
        count = queryset.filter(status='REQUESTED').update(
            status='ASSIGNED',
            assigned_at=timezone.now()
        )
        self.message_user(request, f'{count} delivery(ies) assigned.')
    assign_delivery.short_description = 'Assign to partner'

    def mark_picked_up(self, request, queryset):
        """Mark as picked up."""
        count = queryset.update(status='PICKED_UP', picked_up_at=timezone.now())
        self.message_user(request, f'{count} delivery(ies) picked up.')
    mark_picked_up.short_description = 'Mark as picked up'

    def mark_in_transit(self, request, queryset):
        """Mark as in transit."""
        count = queryset.update(status='IN_TRANSIT')
        self.message_user(request, f'{count} delivery(ies) in transit.')
    mark_in_transit.short_description = 'Mark as in transit'

    def mark_delivered(self, request, queryset):
        """Mark as delivered."""
        count = queryset.update(status='DELIVERED', delivered_at=timezone.now())
        self.message_user(request, f'{count} delivery(ies) delivered.')
    mark_delivered.short_description = 'Mark as delivered'

    fieldsets = (
        ('Order Information', {
            'fields': ('order',)
        }),
        ('Delivery Partner', {
            'fields': ('partner',),
            'description': 'Assign a delivery partner (rider, courier, bus station, etc.)'
        }),
        ('Addresses', {
            'fields': ('pickup_address', 'delivery_address')
        }),
        ('Pricing', {
            'fields': ('delivery_fee',)
        }),
        ('Status', {
            'fields': ('status', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'assigned_at', 'picked_up_at', 'delivered_at')
        }),
    )
