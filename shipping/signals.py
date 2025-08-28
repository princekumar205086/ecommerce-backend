"""
Shipping Signals
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Shipment, ShippingEvent
import logging

logger = logging.getLogger(__name__)

@receiver(pre_save, sender=Shipment)
def shipment_status_changed(sender, instance, **kwargs):
    """Handle shipment status changes"""
    if instance.pk:  # Only for existing shipments
        try:
            old_instance = Shipment.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                # Status has changed, create an event
                ShippingEvent.objects.create(
                    shipment=instance,
                    event_type='status_change',
                    status=instance.status,
                    location=instance.current_location or '',
                    description=f'Status changed from {old_instance.status} to {instance.status}',
                    event_time=timezone.now(),
                    source='system'
                )
                
                # Set timestamps for specific statuses
                if instance.status == 'delivered' and not instance.delivered_at:
                    instance.delivered_at = timezone.now()
                elif instance.status in ['dispatched', 'manifested'] and not instance.shipped_at:
                    instance.shipped_at = timezone.now()
                    
                logger.info(f"Shipment {instance.order_id} status changed to {instance.status}")
                
        except Shipment.DoesNotExist:
            pass

@receiver(post_save, sender=Shipment)
def shipment_created(sender, instance, created, **kwargs):
    """Handle new shipment creation"""
    if created:
        # Create initial event
        ShippingEvent.objects.create(
            shipment=instance,
            event_type='shipment_created',
            status=instance.status,
            location='',
            description='Shipment created',
            event_time=instance.created_at,
            source='system'
        )
        logger.info(f"New shipment created: {instance.order_id}")

@receiver(post_save, sender=ShippingEvent)
def shipping_event_created(sender, instance, created, **kwargs):
    """Handle new shipping events"""
    if created:
        # Update shipment's current location if event has location
        if instance.location:
            instance.shipment.current_location = instance.location
            instance.shipment.save(update_fields=['current_location'])
        
        logger.info(f"New shipping event: {instance.shipment.order_id} - {instance.status}")