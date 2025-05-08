# adminpanel/serializers.py
from rest_framework import serializers
from .models import AdminLog, SystemSetting, AdminNotification
from accounts.serializers import UserSerializer

class AdminLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    action_type_display = serializers.CharField(
        source='get_action_type_display',
        read_only=True
    )

    class Meta:
        model = AdminLog
        fields = [
            'id',
            'user',
            'action_type',
            'action_type_display',
            'model_name',
            'object_id',
            'message',
            'ip_address',
            'created_at'
        ]
        read_only_fields = fields


class SystemSettingSerializer(serializers.ModelSerializer):
    setting_type_display = serializers.CharField(
        source='get_setting_type_display',
        read_only=True
    )
    typed_value = serializers.SerializerMethodField()

    class Meta:
        model = SystemSetting
        fields = [
            'id',
            'key',
            'value',
            'typed_value',
            'setting_type',
            'setting_type_display',
            'description',
            'is_public',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_typed_value(self, obj):
        return obj.get_typed_value()

    def validate(self, data):
        if 'value' in data and 'setting_type' in data:
            try:
                self._validate_typed_value(data['value'], data['setting_type'])
            except ValueError as e:
                raise serializers.ValidationError(str(e))
        return data

    def _validate_typed_value(self, value, setting_type):
        if setting_type == 'number':
            try:
                float(value)
            except ValueError:
                raise ValueError("Value must be a valid number")
        elif setting_type == 'boolean':
            if value.lower() not in ('true', 'false', '1', '0', 'yes', 'no'):
                raise ValueError("Value must be a valid boolean")
        elif setting_type == 'json':
            import json
            try:
                json.loads(value)
            except ValueError:
                raise ValueError("Value must be valid JSON")


class AdminNotificationSerializer(serializers.ModelSerializer):
    notification_type_display = serializers.CharField(
        source='get_notification_type_display',
        read_only=True
    )

    class Meta:
        model = AdminNotification
        fields = [
            'id',
            'user',
            'notification_type',
            'notification_type_display',
            'title',
            'message',
            'is_read',
            'related_object_id',
            'related_content_type',
            'created_at',
            'read_at'
        ]
        read_only_fields = [
            'created_at',
            'read_at'
        ]


class MarkNotificationReadSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )

    def validate_ids(self, value):
        user = self.context['request'].user
        notifications = AdminNotification.objects.filter(
            id__in=value,
            user=user
        )
        if len(notifications) != len(value):
            raise serializers.ValidationError(
                "Some notification IDs are invalid or don't belong to you."
            )
        return value


class ExportDataSerializer(serializers.Serializer):
    model_name = serializers.CharField(required=True)
    format = serializers.ChoiceField(
        choices=[('json', 'JSON'), ('csv', 'CSV'), ('xlsx', 'Excel')],
        default='json'
    )
    filters = serializers.JSONField(required=False, default=dict)


class ImportDataSerializer(serializers.Serializer):
    model_name = serializers.CharField(required=True)
    file = serializers.FileField(required=True)
    format = serializers.ChoiceField(
        choices=[('json', 'JSON'), ('csv', 'CSV')],
        default='json'
    )
    update_existing = serializers.BooleanField(default=False)