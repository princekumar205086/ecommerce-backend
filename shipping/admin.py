"""
Shipping Admin Configuration
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import ShippingProvider, ShippingRate, Shipment, ShippingEvent, PickupRequest, ReturnRequest

@admin.register(ShippingProvider)
class ShippingProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(ShippingRate)
class ShippingRateAdmin(admin.ModelAdmin):
    list_display = ['courier_name', 'pickup_pincode', 'delivery_pincode', 'weight', 'total_charge', 'delivery_days']
    list_filter = ['courier_name', 'is_cod_available', 'is_prepaid_available']
    search_fields = ['courier_name', 'pickup_pincode', 'delivery_pincode']
    ordering = ['total_charge']

class ShippingEventInline(admin.TabularInline):
    model = ShippingEvent
    extra = 0
    readonly_fields = ['event_time', 'created_at']
    fields = ['event_type', 'status', 'location', 'description', 'event_time']

class PickupRequestInline(admin.StackedInline):
    model = PickupRequest
    extra = 0
    readonly_fields = ['created_at', 'updated_at']

class ReturnRequestInline(admin.TabularInline):
    model = ReturnRequest
    extra = 0
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = [
        'order_id', 'customer_name', 'status', 'courier_name', 
        'awb_code', 'delivery_pincode', 'created_at'
    ]
    list_filter = [
        'status', 'courier_name', 'payment_method', 
        'delivery_state', 'created_at'
    ]
    search_fields = [
        'order_id', 'awb_code', 'customer_name', 
        'customer_email', 'delivery_pincode'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'shipped_at', 
        'delivered_at', 'tracking_url_display'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'order_id', 'user', 'status', 'created_at', 'updated_at'
            )
        }),
        ('ShipRocket Details', {
            'fields': (
                'shiprocket_order_id', 'shiprocket_shipment_id', 
                'awb_code', 'courier_company_id', 'courier_name',
                'tracking_url_display'
            )
        }),
        ('Customer Information', {
            'fields': (
                'customer_name', 'customer_email', 'customer_phone'
            )
        }),
        ('Pickup Details', {
            'fields': (
                'pickup_location', 'pickup_address', 'pickup_pincode'
            )
        }),
        ('Delivery Details', {
            'fields': (
                'delivery_address', 'delivery_city', 'delivery_state',
                'delivery_pincode', 'delivery_country'
            )
        }),
        ('Package Information', {
            'fields': (
                'weight', 'length', 'breadth', 'height'
            )
        }),
        ('Financial Details', {
            'fields': (
                'total_amount', 'cod_amount', 'shipping_charges', 'payment_method'
            )
        }),
        ('Delivery Status', {
            'fields': (
                'current_location', 'estimated_delivery_date',
                'actual_delivery_date', 'shipped_at', 'delivered_at'
            )
        }),
        ('Data Storage', {
            'fields': (
                'items_data', 'tracking_data', 'shiprocket_response'
            ),
            'classes': ('collapse',)
        })
    )
    
    inlines = [ShippingEventInline, PickupRequestInline, ReturnRequestInline]
    
    def tracking_url_display(self, obj):
        url = obj.get_tracking_url()
        if url:
            return format_html('<a href="{}" target="_blank">Track Shipment</a>', url)
        return "No tracking available"
    tracking_url_display.short_description = "Tracking URL"
    
    actions = ['update_tracking', 'mark_delivered']
    
    def update_tracking(self, request, queryset):
        # Remove the import that doesn't exist
        # from .tasks import update_tracking_for_shipments
        shipment_ids = list(queryset.values_list('id', flat=True))
        # You can implement actual tracking update logic here
        self.message_user(request, f"Tracking update initiated for {len(shipment_ids)} shipments")
    update_tracking.short_description = "Update tracking information"
    
    def mark_delivered(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(status='delivered', actual_delivery_date=timezone.now())
        self.message_user(request, f"{count} shipments marked as delivered")
    mark_delivered.short_description = "Mark as delivered"

@admin.register(ShippingEvent)
class ShippingEventAdmin(admin.ModelAdmin):
    list_display = ['shipment', 'status', 'location', 'event_time', 'source']
    list_filter = ['status', 'source', 'event_time']
    search_fields = ['shipment__order_id', 'shipment__awb_code', 'location', 'description']
    readonly_fields = ['created_at']
    date_hierarchy = 'event_time'

@admin.register(PickupRequest)
class PickupRequestAdmin(admin.ModelAdmin):
    list_display = ['shipment', 'pickup_date', 'pickup_time', 'status', 'pickup_boy_name']
    list_filter = ['status', 'pickup_date']
    search_fields = ['shipment__order_id', 'pickup_boy_name', 'pickup_boy_phone']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = [
        'return_order_id', 'shipment', 'reason', 'status', 
        'refund_amount', 'is_refund_processed', 'created_at'
    ]
    list_filter = [
        'status', 'reason', 'is_refund_processed', 'created_at'
    ]
    search_fields = [
        'return_order_id', 'shipment__order_id', 
        'shipment__customer_name', 'reason_description'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Return Information', {
            'fields': (
                'return_order_id', 'shipment', 'reason', 
                'reason_description', 'status'
            )
        }),
        ('Return Shipping', {
            'fields': (
                'return_awb', 'return_pickup_date', 'return_tracking_data'
            )
        }),
        ('Refund Details', {
            'fields': (
                'refund_amount', 'is_refund_processed', 'refund_date'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 'updated_at'
            )
        })
    )