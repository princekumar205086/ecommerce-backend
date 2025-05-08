import razorpay
from django.conf import settings
from django.db import models
from django.utils import timezone

from orders.models import Order


class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_order_id = models.CharField(max_length=100)
    razorpay_signature = models.CharField(max_length=200, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    webhook_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.razorpay_payment_id or 'pending'} for Order {self.order.order_number}"

    def verify_payment(self, signature):
        client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))
        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': self.razorpay_order_id,
                'razorpay_payment_id': self.razorpay_payment_id,
                'razorpay_signature': signature
            })
            return True
        except:
            return False

    def verify_webhook(self, payload, signature):
        client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))
        try:
            client.utility.verify_webhook_signature(
                payload,
                signature,
                settings.RAZORPAY_WEBHOOK_SECRET
            )
            return True
        except:
            return False

    def process_webhook(self, event, payload):
        if event == 'payment.captured':
            self.razorpay_payment_id = payload['payment']['entity']['id']
            self.status = 'successful'
            self.webhook_verified = True
            self.save()

            # Update order status
            self.order.payment_status = 'paid'
            self.order.save()
        elif event == 'payment.failed':
            self.status = 'failed'
            self.webhook_verified = True
            self.save()
