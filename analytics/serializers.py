# analytics/serializers.py
from rest_framework import serializers
from .models import (
    AnalyticsEvent, ProductView, SalesReport,
    UserActivity, InventoryAlert
)
from products.serializers import BaseProductSerializer
from accounts.serializers import UserSerializer
from orders.serializers import OrderSerializer

class AnalyticsEventSerializer(serializers.ModelSerializer):
    event_type_display = serializers.CharField(
        source='get_event_type_display',
        read_only=True
    )
    user = UserSerializer(read_only=True)

    class Meta:
        model = AnalyticsEvent
        fields = [
            'id',
            'event_type',
            'event_type_display',
            'user',
            'session_key',
            'ip_address',
            'user_agent',
            'referrer',
            'path',
            'data',
            'created_at'
        ]
        read_only_fields = fields


class ProductViewSerializer(serializers.ModelSerializer):
    product = BaseProductSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = ProductView
        fields = [
            'id',
            'product',
            'user',
            'session_key',
            'created_at'
        ]
        read_only_fields = fields


class SalesReportSerializer(serializers.ModelSerializer):
    period_type_display = serializers.CharField(
        source='get_period_type_display',
        read_only=True
    )

    class Meta:
        model = SalesReport
        fields = [
            'id',
            'period_type',
            'period_type_display',
            'start_date',
            'end_date',
            'total_orders',
            'total_revenue',
            'total_products_sold',
            'new_customers',
            'returning_customers',
            'average_order_value',
            'data',
            'created_at',
            'updated_at'
        ]
        read_only_fields = fields


class UserActivitySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    last_order = serializers.SerializerMethodField()
    favorite_categories = serializers.SerializerMethodField()

    class Meta:
        model = UserActivity
        fields = [
            'id',
            'user',
            'last_login',
            'last_activity',
            'total_logins',
            'total_orders',
            'total_spent',
            'favorite_categories',
            'last_order',
            'data',
            'created_at',
            'updated_at'
        ]
        read_only_fields = fields

    def get_last_order(self, obj):
        last_order = obj.user.orders.order_by('-created_at').first()
        if last_order:
            return OrderSerializer(last_order).data
        return None

    def get_favorite_categories(self, obj):
        from products.serializers import ProductCategorySerializer
        return ProductCategorySerializer(
            obj.favorite_categories.all(),
            many=True
        ).data


class InventoryAlertSerializer(serializers.ModelSerializer):
    alert_type_display = serializers.CharField(
        source='get_alert_type_display',
        read_only=True
    )
    product = BaseProductSerializer(read_only=True)
    resolved_by = UserSerializer(read_only=True)

    class Meta:
        model = InventoryAlert
        fields = [
            'id',
            'product',
            'alert_type',
            'alert_type_display',
            'current_quantity',
            'threshold',
            'message',
            'is_resolved',
            'resolved_at',
            'resolved_by',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'product',
            'alert_type',
            'alert_type_display',
            'current_quantity',
            'threshold',
            'message',
            'created_at',
            'updated_at'
        ]


class DateRangeSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)

    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("End date must be after start date")
        return data


class ProductAnalyticsSerializer(serializers.Serializer):
    product = BaseProductSerializer()
    total_views = serializers.IntegerField()
    total_adds_to_cart = serializers.IntegerField()
    total_purchases = serializers.IntegerField()
    conversion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)


class CategoryAnalyticsSerializer(serializers.Serializer):
    category = serializers.CharField()
    total_views = serializers.IntegerField()
    total_products = serializers.IntegerField()
    total_sales = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)