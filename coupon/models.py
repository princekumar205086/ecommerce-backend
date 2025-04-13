from django.db import models
from django.core.exceptions import ValidationError
from django.utils.timezone import now

class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_percent = models.PositiveIntegerField()
    active = models.BooleanField(default=True)
    valid_until = models.DateTimeField()

    def clean(self):
        if not (0 <= self.discount_percent <= 100):
            raise ValidationError("Discount percent must be between 0 and 100.")
        if self.valid_until <= now():
            raise ValidationError("The valid until date must be in the future.")

    def __str__(self):
        return self.code

    class Meta:
        ordering = ['valid_until']