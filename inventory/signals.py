from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import InventoryItem
from django.utils.timezone import now
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=InventoryItem)
def check_low_stock(sender, instance, created, **kwargs):
    """
    Signal to handle stock threshold notifications/logging.
    Triggered when inventory item is saved.
    """
    if instance.is_low_stock:
        message = f"[LOW STOCK] Product: {instance.product.name} | Variant: {instance.variant or 'default'} | Stock: {instance.quantity} | Warehouse: {instance.warehouse.name}"
        # Logging instead of printing in production
        logger.warning(message)

        # Optionally, trigger notification via email, Slack, SMS, etc.
        # send_low_stock_alert(instance)
    else:
        # Log for audit trail
        logger.info(f"[STOCK OK] Product: {instance.product.name} | Qty: {instance.quantity} | {now().strftime('%Y-%m-%d %H:%M:%S')}")
