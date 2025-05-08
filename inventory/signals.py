from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import InventoryItem

@receiver(post_save, sender=InventoryItem)
def check_low_stock(sender, instance, **kwargs):
    if instance.is_low_stock:
        # send a notification or log warning
        print(f"Stock low for {instance}")