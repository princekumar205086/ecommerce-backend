import os
from io import BytesIO
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
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
        max_length=40,
        unique=True,
        editable=False
    )
    status = models.CharField(
        max_length=20,
        choices=INVOICE_STATUS,
        default='draft'
    )
    issued_date = models.DateField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)
    payment_terms = models.CharField(
        max_length=20,
        choices=PAYMENT_TERMS,
        default='due_on_receipt'
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    shipping_charge = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    balance_due = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
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
            try:
                seq = int(last_invoice.invoice_number.split('-')[-1]) + 1
            except Exception:
                seq = 1
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
        try:
            self.subtotal = Decimal(self.order.subtotal)
            self.tax_amount = Decimal(self.order.tax)
            self.shipping_charge = Decimal(self.order.shipping_charge)
            self.discount_amount = Decimal(str(self.order.discount)) + Decimal(str(self.order.coupon_discount))
            self.total_amount = Decimal(self.order.total)
        except Exception:
            # Keep defaults if order doesn't provide these
            pass

        # Calculate balance due
        self.balance_due = (self.total_amount - Decimal(str(self.amount_paid)))

    def is_overdue(self):
        """Check if invoice is overdue"""
        return self.balance_due > 0 and timezone.now().date() > self.due_date

    def mark_as_paid(self, amount, save=True):
        """Mark invoice as paid (fully or partially)"""
        if amount <= 0:
            raise ValidationError("Payment amount must be positive")

        self.amount_paid += Decimal(amount)
        if self.amount_paid >= self.total_amount:
            self.status = 'paid'
            self.amount_paid = self.total_amount  # Prevent overpayment

        self.balance_due = self.total_amount - self.amount_paid

        if save:
            self.save()

    def generate_pdf(self):
        """Generate a professional PDF invoice using ReportLab Platypus.

        Returns PDF bytes or None on failure. Also attempts to save to `pdf_file`.
        """
        try:
            # Import inside function to avoid import-time failures
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
            from reportlab.lib.units import mm
            from django.conf import settings

            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4,
                                    rightMargin=20*mm, leftMargin=20*mm,
                                    topMargin=20*mm, bottomMargin=20*mm)

            styles = getSampleStyleSheet()
            normal = styles['Normal']
            heading = ParagraphStyle('heading', parent=styles['Heading1'], alignment=0, fontSize=16)
            small = ParagraphStyle('small', parent=styles['Normal'], fontSize=9)

            elements = []

            # Header: logo + company info
            company_name = getattr(settings, 'APP_NAME', 'MedixMall')
            company_contact = getattr(settings, 'DEFAULT_FROM_EMAIL', '')
            logo_path = getattr(settings, 'INVOICE_LOGO_PATH', None)

            header_data = []
            if logo_path and os.path.exists(logo_path):
                try:
                    img = Image(logo_path, width=40*mm, height=20*mm)
                    header_data.append([img, Paragraph(f"<b>{company_name}</b><br/>{company_contact}", normal)])
                except Exception:
                    header_data.append([Paragraph(f"<b>{company_name}</b>", heading), Paragraph(company_contact, small)])
            else:
                header_data.append([Paragraph(f"<b>{company_name}</b>", heading), Paragraph(company_contact, small)])

            header_table = Table(header_data, colWidths=[60*mm, 100*mm])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ]))
            elements.append(header_table)
            elements.append(Spacer(1, 8))

            # Invoice metadata
            meta = [[Paragraph(f"<b>Invoice:</b> {self.invoice_number}", normal), Paragraph(f"<b>Date:</b> {self.issued_date.strftime('%Y-%m-%d')}", normal)],
                    [Paragraph(f"<b>Order:</b> {self.order.order_number}", normal), Paragraph(f"<b>Due:</b> {self.due_date.strftime('%Y-%m-%d')}", normal)]]
            meta_table = Table(meta, colWidths=[95*mm, 65*mm])
            meta_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ]))
            elements.append(meta_table)
            elements.append(Spacer(1, 12))

            # Billing and shipping addresses
            billing = self.order.billing_address or {}
            shipping = self.order.shipping_address or {}
            addr_data = [[Paragraph('<b>Bill To</b>', normal), Paragraph('<b>Ship To</b>', normal)],
                         [Paragraph(billing.get('full_name',''), small), Paragraph(shipping.get('full_name',''), small)],
                         [Paragraph(billing.get('address_line_1',''), small), Paragraph(shipping.get('address_line_1',''), small)],
                         [Paragraph(f"{billing.get('city','')} {billing.get('postal_code','')}", small), Paragraph(f"{shipping.get('city','')} {shipping.get('postal_code','')}", small)]]
            addr_table = Table(addr_data, colWidths=[80*mm, 80*mm])
            addr_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('INNERGRID', (0,0), (-1,-1), 0.25, colors.white),
                ('BOX', (0,0), (-1,-1), 0.25, colors.white),
            ]))
            elements.append(addr_table)
            elements.append(Spacer(1, 12))

            # Line items table
            data = [[Paragraph('<b>Item</b>', normal), Paragraph('<b>Qty</b>', normal), Paragraph('<b>Unit</b>', normal), Paragraph('<b>Total</b>', normal)]]
            for item in self.order.items.select_related('product').all():
                name = item.product.name
                qty = str(item.quantity)
                unit = f"₹{float(item.price):.2f}"
                total = f"₹{float(item.total_price):.2f}"
                data.append([Paragraph(name, small), Paragraph(qty, small), Paragraph(unit, small), Paragraph(total, small)])

            table = Table(data, colWidths=[90*mm, 25*mm, 30*mm, 30*mm])
            table.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f2f4f7')),
                ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
                ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 12))

            # Totals box
            totals_data = []
            totals_data.append(['Subtotal', f"₹{float(self.subtotal):.2f}"])
            totals_data.append(['Tax', f"₹{float(self.tax_amount):.2f}"])
            totals_data.append(['Shipping', f"₹{float(self.shipping_charge):.2f}"])
            totals_data.append(['Discount', f"- ₹{float(self.discount_amount):.2f}"])
            totals_data.append(['Total', f"₹{float(self.total_amount):.2f}"])

            totals_table = Table(totals_data, colWidths=[100*mm, 75*mm], hAlign='RIGHT')
            totals_table.setStyle(TableStyle([
                ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
                ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
                ('LINEABOVE', (0,-1), (-1,-1), 1, colors.black),
            ]))
            elements.append(totals_table)
            elements.append(Spacer(1, 18))

            # Notes & footer
            if self.notes:
                elements.append(Paragraph('<b>Notes</b>', normal))
                elements.append(Paragraph(self.notes, small))
                elements.append(Spacer(1, 12))

            footer_text = f"{company_name} • {company_contact}"
            elements.append(Spacer(1, 30))
            elements.append(Paragraph(footer_text, small))

            doc.build(elements)

            pdf = buffer.getvalue()
            buffer.close()

            # save to filefield if possible
            try:
                filename = f'INV-{self.issued_date.strftime("%Y%m%d")}-{self.invoice_number}.pdf'
                self.pdf_file.save(filename, ContentFile(pdf), save=True)
            except Exception:
                # swallow save errors in generate
                pass

            return pdf

        except Exception as e:
            try:
                import logging
                logging.getLogger(__name__).exception(f"Invoice PDF generation failed: {e}")
            except Exception:
                pass
            return None

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
        try:
            self.invoice.mark_as_paid(self.amount)
        except Exception:
            pass