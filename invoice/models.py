# invoice/models.py
import os
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.db.models import Sum, F, DecimalField
from django.db import transaction
from decimal import Decimal
from django.core.exceptions import ValidationError
from accounts.models import User
from orders.models import Order


def invoice_file_path(instance, filename):
    """Generate file path for invoice PDF"""
    date_str = timezone.now().strftime('%Y/%m/%d')
    return f'invoices/{date_str}/{instance.invoice_number}.pdf'


class Invoice(models.Model):
    INVOICE_STATUS = (
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )

    PAYMENT_TERMS = (
        ('net_7', 'Net 7 days'),
        ('net_15', 'Net 15 days'),
        ('net_30', 'Net 30 days'),
        ('due_on_receipt', 'Due on Receipt'),
    )

    order = models.OneToOneField(
        Order,
        on_delete=models.PROTECT,
        related_name='invoice'
    )
    invoice_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False
    )
    status = models.CharField(
        max_length=20,
        choices=INVOICE_STATUS,
        default='draft'
    )
    issued_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    payment_terms = models.CharField(
        max_length=20,
        choices=PAYMENT_TERMS,
        default='due_on_receipt'
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    shipping_charge = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    balance_due = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    notes = models.TextField(blank=True)
    terms_conditions = models.TextField(
        blank=True,
        default="Payment due upon receipt. Late payments subject to fees."
    )
    pdf_file = models.FileField(
        upload_to=invoice_file_path,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issued_date']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['order']),
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
        ]
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"

    def __str__(self):
        return f"Invoice #{self.invoice_number} for Order #{self.order.order_number}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        if not self.due_date:
            self.set_due_date()
        self.calculate_totals()
        super().save(*args, **kwargs)

    def generate_invoice_number(self):
        """Generate sequential invoice number with prefix INV-YYYYMMDD-XXXX"""
        date_str = timezone.now().strftime('%Y%m%d')
        last_invoice = Invoice.objects.filter(
            invoice_number__startswith=f'INV-{date_str}'
        ).order_by('invoice_number').last()

        if last_invoice:
            seq = int(last_invoice.invoice_number[-4:]) + 1
        else:
            seq = 1

        return f"INV-{date_str}-{seq:04d}"

    def set_due_date(self):
        """Set due date based on payment terms"""
        if self.payment_terms == 'net_7':
            self.due_date = self.issued_date + timezone.timedelta(days=7)
        elif self.payment_terms == 'net_15':
            self.due_date = self.issued_date + timezone.timedelta(days=15)
        elif self.payment_terms == 'net_30':
            self.due_date = self.issued_date + timezone.timedelta(days=30)
        else:  # due_on_receipt
            self.due_date = self.issued_date

    def calculate_totals(self):
        """Calculate all financial fields from the order"""
        self.subtotal = self.order.subtotal
        self.tax_amount = self.order.tax
        self.shipping_charge = self.order.shipping_charge
        self.discount_amount = self.order.discount + self.order.coupon_discount
        self.total_amount = self.order.total

        # Calculate balance due
        self.balance_due = self.total_amount - self.amount_paid

    def is_overdue(self):
        """Check if invoice is overdue"""
        return self.balance_due > 0 and timezone.now().date() > self.due_date

    def mark_as_paid(self, amount, save=True):
        """Mark invoice as paid (fully or partially)"""
        if amount <= 0:
            raise ValidationError("Payment amount must be positive")

        self.amount_paid += amount
        if self.amount_paid >= self.total_amount:
            self.status = 'paid'
            self.amount_paid = self.total_amount  # Prevent overpayment

        self.balance_due = self.total_amount - self.amount_paid

        if save:
            self.save()

    def generate_pdf(self):
        """Generate PDF invoice (to be implemented with reportlab/weasyprint)"""
        # This would be implemented in a separate service
        pass

    @classmethod
    def create_from_order(cls, order):
        """Create an invoice from an order"""
        if hasattr(order, 'invoice'):
            raise ValidationError("This order already has an invoice")

        invoice = cls(order=order)
        invoice.save()
        return invoice


class InvoiceLineItem(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='line_items'
    )
    product_name = models.CharField(max_length=200)
    product_description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('10.00')  # Default 10% tax
    )
    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    class Meta:
        verbose_name = "Invoice Line Item"
        verbose_name_plural = "Invoice Line Items"

    def __str__(self):
        return f"{self.quantity} x {self.product_name} (Invoice #{self.invoice.invoice_number})"

    def save(self, *args, **kwargs):
        self.calculate_total()
        super().save(*args, **kwargs)

    def calculate_total(self):
        """Calculate total price for line item"""
        subtotal = self.unit_price * self.quantity
        discounted = subtotal - self.discount
        tax_amount = discounted * (self.tax_rate / Decimal('100.00'))
        self.total_price = (discounted + tax_amount).quantize(Decimal('0.00'))


class InvoicePayment(models.Model):
    PAYMENT_METHODS = (
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('net_banking', 'Net Banking'),
        ('upi', 'UPI'),
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
    )

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name='payments'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS
    )
    transaction_id = models.CharField(
        max_length=100,
        blank=True
    )
    payment_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date']
        verbose_name = "Invoice Payment"
        verbose_name_plural = "Invoice Payments"

    def __str__(self):
        return f"Payment of {self.amount} for Invoice #{self.invoice.invoice_number}"

    def clean(self):
        if self.amount > self.invoice.balance_due:
            raise ValidationError(
                f"Payment amount cannot exceed balance due of {self.invoice.balance_due}"
            )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update invoice payment status
        self.invoice.mark_as_paid(self.amount)