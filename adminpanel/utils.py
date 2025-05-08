# adminpanel/utils.py
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


def log_admin_action(user, action_type, model_name, object_id=None, message="", ip_address=None):
    """
    Log an admin action for audit purposes

    Args:
        user: The admin user performing the action
        action_type: One of 'create', 'update', 'delete', 'login', 'logout'
        model_name: The name of the model being acted upon
        object_id: The ID of the object being acted upon (optional)
        message: Additional details about the action (optional)
        ip_address: The IP address of the admin user (optional)
    """
    from .models import AdminLog

    AdminLog.objects.create(
        user=user,
        action_type=action_type,
        model_name=model_name,
        object_id=str(object_id) if object_id else "",
        message=message,
        ip_address=ip_address
    )


def notify_admin(user, notification_type, title, message, related_object=None):
    """
    Send a notification to an admin user

    Args:
        user: The admin user to notify
        notification_type: One of 'system', 'order', 'user', 'inventory', 'payment'
        title: The notification title
        message: The notification message
        related_object: The related object (optional)
    """
    from .models import AdminNotification

    notification = AdminNotification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message
    )

    if related_object:
        notification.related_object_id = related_object.pk
        notification.related_content_type = related_object.__class__.__name__
        notification.save()

    return notification


def get_system_setting(key, default=None):
    """
    Get a system setting value by key

    Args:
        key: The setting key
        default: Default value if setting doesn't exist
    """
    from .models import SystemSetting

    try:
        setting = SystemSetting.objects.get(key=key)
        return setting.get_typed_value()
    except SystemSetting.DoesNotExist:
        return default


def set_system_setting(key, value, setting_type='string', description="", is_public=False):
    """
    Set a system setting value

    Args:
        key: The setting key
        value: The setting value
        setting_type: One of 'string', 'number', 'boolean', 'json'
        description: Description of the setting (optional)
        is_public: Whether the setting is publicly accessible (optional)
    """
    from .models import SystemSetting

    if setting_type == 'json':
        import json
        value = json.dumps(value)
    elif setting_type == 'boolean':
        value = str(value).lower()

    setting, created = SystemSetting.objects.update_or_create(
        key=key,
        defaults={
            'value': str(value),
            'setting_type': setting_type,
            'description': description,
            'is_public': is_public
        }
    )

    return setting