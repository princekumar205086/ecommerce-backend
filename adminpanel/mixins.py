# adminpanel/mixins.py
from rest_framework import permissions
from .utils import log_admin_action


class AdminActionMixin:
    """
    Mixin to log admin actions automatically
    """

    def perform_create(self, serializer):
        instance = serializer.save()
        log_admin_action(
            user=self.request.user,
            action_type='create',
            model_name=instance.__class__.__name__,
            object_id=instance.pk,
            ip_address=self._get_client_ip()
        )
        return instance

    def perform_update(self, serializer):
        instance = serializer.save()
        log_admin_action(
            user=self.request.user,
            action_type='update',
            model_name=instance.__class__.__name__,
            object_id=instance.pk,
            ip_address=self._get_client_ip()
        )
        return instance

    def perform_destroy(self, instance):
        log_admin_action(
            user=self.request.user,
            action_type='delete',
            model_name=instance.__class__.__name__,
            object_id=instance.pk,
            ip_address=self._get_client_ip()
        )
        instance.delete()

    def _get_client_ip(self):
        request = self.request
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AdminPermissionMixin:
    """
    Mixin to ensure only admin users can access the view
    """
    permission_classes = [permissions.IsAdminUser]