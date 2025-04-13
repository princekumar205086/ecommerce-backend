from .models import Coupon
from django.utils import timezone

def apply_coupon(code, total):
    try:
        coupon = Coupon.objects.get(code=code, active=True, valid_until__gte=timezone.now())
        discount = total * (coupon.discount_percent / 100)
        return total - discount, discount
    except Coupon.DoesNotExist:
        return total, 0
