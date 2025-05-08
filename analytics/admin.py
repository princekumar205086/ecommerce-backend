# analytics/admin.py
from django.contrib import admin
from django.utils.html import format_html
from rest_framework.utils import timezone

from .models import (
    AnalyticsEvent, ProductView, SalesReport,
    UserActivity, InventoryAlert
)

@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = [
        'event_type',
        'user',
        'path',
        'created_at'
    ]
    list_filter = ['event_type', 'created_at']
    search_fields = ['user__email', 'path', 'data']
    readonly_fields = ['created_at', 'data_prettified']
    date_hierarchy = 'created_at'

    def data_prettified(self, instance):
        import json
        return format_html(
            '<pre>{}</pre>',
            json.dumps(instance.data, indent=2)
        )
    data_prettified.short_description = 'Data'


@admin.register(ProductView)
class ProductViewAdmin(admin.ModelAdmin):
    list_display = [
        'product',
        'user',
        'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['product__name', 'user__email']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(SalesReport)
class SalesReportAdmin(admin.ModelAdmin):
    list_display = [
        'period_type',
        'start_date',
        'end_date',
        'total_orders',
        'total_revenue',
        'created_at'
    ]
    list_filter = ['period_type', 'created_at']
    search_fields = ['data']
    readonly_fields = [
        'created_at',
        'updated_at',
        'data_prettified'
    ]
    date_hierarchy = 'start_date'

    def data_prettified(self, instance):
        import json
        return format_html(
            '<pre>{}</pre>',
            json.dumps(instance.data, indent=2)
        )
    data_prettified.short_description = 'Data'

    actions = ['regenerate_report']

    def regenerate_report(self, request, queryset):
        for report in queryset:
            report.calculate_metrics()
            report.save()
        self.message_user(
            request,
            f"{queryset.count()} reports regenerated successfully."
        )
    regenerate_report.short_description = "Regenerate selected reports"


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'last_login',
        'last_activity',
        'total_orders',
        'total_spent',
        'updated_at'
    ]
    list_filter = ['last_login', 'last_activity']
    search_fields = ['user__email']
    readonly_fields = [
        'created_at',
        'updated_at',
        'data_prettified'
    ]
    filter_horizontal = ['favorite_categories']

    def data_prettified(self, instance):
        import json
        return format_html(
            '<pre>{}</pre>',
            json.dumps(instance.data, indent=2)
        )
    data_prettified.short_description = 'Data'

    actions = ['update_activity']

    def update_activity(self, request, queryset):
        for activity in queryset:
            activity.update_activity()
        self.message_user(
            request,
            f"{queryset.count()} user activities updated."
        )
    update_activity.short_description = "Update selected user activities"


@admin.register(InventoryAlert)
class InventoryAlertAdmin(admin.ModelAdmin):
    list_display = [
        'product',
        'alert_type',
        'current_quantity',
        'threshold',
        'is_resolved',
        'created_at'
    ]
    list_filter = ['alert_type', 'is_resolved', 'created_at']
    search_fields = ['product__name', 'message']
    readonly_fields = [
        'created_at',
        'updated_at',
        'resolved_at',
        'resolved_by'
    ]
    date_hierarchy = 'created_at'
    actions = ['resolve_alerts']

    def resolve_alerts(self, request, queryset):
        updated = queryset.update(
            is_resolved=True,
            resolved_at=timezone.now(),
            resolved_by=request.user
        )
        self.message_user(
            request,
            f"{updated} inventory alerts resolved."
        )
    resolve_alerts.short_description = "Mark selected alerts as resolved"