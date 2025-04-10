from django.db import models

PRODUCT_TYPE_CHOICES = (
    ('pathology', 'Pathology Product'),
    ('doctor', 'Doctor Product'),
    ('medical', 'Medical Product'),
)

class ProductCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
