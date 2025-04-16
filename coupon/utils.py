# coupon/utils.py
from .models import Coupon
from django.core.exceptions import ValidationError

def apply_coupon(code, user, cart_total):
    """
    Apply coupon to cart and return discount amount
    """
    try:
        coupon = Coupon.objects.get(code=code)
    except Coupon.DoesNotExist:
        raise ValidationError("Invalid coupon code")

    is_valid, message = coupon.is_valid(user, cart_total)
    if not is_valid:
        raise ValidationError(message)

    return coupon.apply_discount(cart_total)