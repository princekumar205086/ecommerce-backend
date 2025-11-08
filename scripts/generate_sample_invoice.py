"""Generate a sample invoice PDF for manual inspection.

Run: python scripts/generate_sample_invoice.py

This script creates a sample user, product, order and generates an Invoice PDF
using the project's `Invoice.generate_pdf()` and writes the PDF to the repo root
as `sample_invoice_<invoice_number>.pdf`.
"""
import os
import sys
import django
from decimal import Decimal

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.conf import settings
from accounts.models import User
from products.models import ProductCategory, Brand, Product
from orders.models import Order, OrderItem
from invoice.models import Invoice

OUT_DIR = os.path.join(PROJECT_ROOT, 'generated_invoices')
os.makedirs(OUT_DIR, exist_ok=True)

def create_sample_user():
    email = 'sample-invoice@example.com'
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'full_name': 'Sample Customer',
            'contact': '9999999999'
        }
    )
    if created:
        user.set_password('password')
        user.save()
    return user


def create_sample_product(user):
    cat, _ = ProductCategory.objects.get_or_create(name='Sample Category', defaults={'created_by': user})
    brand, _ = Brand.objects.get_or_create(name='Sample Brand', defaults={'created_by': user})
    product, _ = Product.objects.get_or_create(
        name='Sample Product',
        defaults={
            'category': cat,
            'brand': brand,
            'created_by': user,
            'price': Decimal('199.00'),
            'mrp': Decimal('249.00'),
            'stock': 100,
            'is_publish': True,
            'status': 'published'
        }
    )
    return product


def create_sample_order(user, product):
    shipping_address = {
        'full_name': user.full_name or 'Sample Customer',
        'address_line_1': '123 Sample St',
        'city': 'Sample City',
        'postal_code': '123456',
        'state': 'Sample State',
        'country': 'India'
    }
    billing_address = shipping_address.copy()

    order = Order.objects.create(
        user=user,
        shipping_address=shipping_address,
        billing_address=billing_address,
        payment_method='upi'
    )

    # Create order item
    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=2,
        price=product.price
    )

    # Recalculate totals and save
    order.calculate_totals()
    order.save()
    return order


def main():
    user = create_sample_user()
    product = create_sample_product(user)
    order = create_sample_order(user, product)

    print(f"Created Order #{order.order_number} with total {order.total}")

    invoice = Invoice.create_from_order(order)
    print(f"Created Invoice #{invoice.invoice_number} (id={invoice.pk})")

    pdf_bytes = invoice.generate_pdf()
    if not pdf_bytes:
        print("Invoice PDF generation returned None. Check logs for errors.")
        return

    out_path = os.path.join(OUT_DIR, f'sample_invoice_{invoice.invoice_number}.pdf')
    with open(out_path, 'wb') as f:
        f.write(pdf_bytes)

    print(f"Wrote PDF to: {out_path}")


if __name__ == '__main__':
    main()
