"""
Shipping App Configuration
"""

from django.apps import AppConfig


class ShippingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shipping'
    verbose_name = 'Shipping Management'
    
    def ready(self):
        import shipping.signals