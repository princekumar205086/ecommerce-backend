# notifications/serializers.py
from rest_framework import serializers
from .models import Notification, NotificationPreference
from django.contrib.auth import get_user_model

User = get_user_model()

class NotificationSerializer(serializers.ModelSerializer):
    notification_type_display = serializers.CharField(
        source='get_notification_type_display',
        read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'notification_type_display',
            'title',
            'message',
            'is_read',
            'priority',
            'priority_display',
            'related_object_id',
            'related_content_type',
            'created_at',
            'read_at',
            'expires_at',
            'is_expired'
        ]
        read_only_fields = [
            'id',
            'created_at',
            'read_at',
            'is_expired'
        ]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            'email_enabled',
            'push_enabled',
            'sms_enabled',
            'order_updates',
            'payment_updates',
            'inventory_alerts',
            'prescription_updates',
            'promotional',
            'security_alerts'
        ]


class MarkAsReadSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )

    def validate_ids(self, value):
        user = self.context['request'].user
        notifications = Notification.objects.filter(
            id__in=value,
            user=user
        )
        if len(notifications) != len(value):
            raise serializers.ValidationError(
                "Some notification IDs are invalid or don't belong to you."
            )
        return value


class NotificationCountSerializer(serializers.Serializer):
    unread_count = serializers.IntegerField()
    total_count = serializers.IntegerField()