# invoice/admin.py
from django.contrib import admin
from .models import Invoice, InvoiceLineItem, InvoicePayment
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

class InvoiceLineItemInline(admin.TabularInline):
    model = InvoiceLineItem
    extra = 0
    readonly_fields = ['total_price']
    fields = [
        'product_name',
        'product_description',
        'quantity',
        'unit_price',
        'tax_rate',
        'discount',
        'total_price'
    ]

class InvoicePaymentInline(admin.TabularInline):
    model = InvoicePayment
    extra = 0
    readonly_fields = ['created_at']
    fields = [
        'amount',
        'payment_method',
        'transaction_id',
        'payment_date',
        'notes',
        'created_at'
    ]

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number',
        'order_link',
        'status',
        'issued_date',
        'due_date',
        'total_amount',
        'balance_due',
        'is_overdue',
        'pdf_link'
    ]
    list_filter = ['status', 'payment_terms', 'issued_date']
    search_fields = ['invoice_number', 'order__order_number']
    readonly_fields = [
        'invoice_number',
        'subtotal',
        'tax_amount',
        'shipping_charge',
        'discount_amount',
        'total_amount',
        'balance_due',
        'created_at',
        'updated_at'
    ]
    inlines = [InvoiceLineItemInline, InvoicePaymentInline]
    fieldsets = (
        (None, {
            'fields': (
                'invoice_number',
                'order',
                'status',
                'issued_date',
                'due_date',
                'payment_terms'
            )
        }),
        ('Financials', {
            'fields': (
                'subtotal',
                'tax_amount',
                'shipping_charge',
                'discount_amount',
                'total_amount',
                'amount_paid',
                'balance_due'
            )
        }),
        ('Document', {
            'fields': ('pdf_file',)
        }),
        ('Metadata', {
            'fields': ('notes', 'terms_conditions', 'created_at', 'updated_at')
        })
    )
    actions = ['mark_as_sent', 'generate_pdfs']

    def order_link(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html('<a href="{}">{}</a>', url, obj.order.order_number)
    order_link.short_description = 'Order'

    def pdf_link(self, obj):
        if obj.pdf_file:
            return format_html(
                '<a href="{}" target="_blank">Download PDF</a>',
                obj.pdf_file.url
            )
        return "-"
    pdf_link.short_description = 'PDF'

    def is_overdue(self, obj):
        return obj.is_overdue()
    is_overdue.boolean = True

    def mark_as_sent(self, request, queryset):
        updated = queryset.filter(status='draft').update(status='sent')
        self.message_user(
            request,
            f"{updated} invoices marked as sent."
        )
    mark_as_sent.short_description = "Mark selected invoices as sent"

    def generate_pdfs(self, request, queryset):
        # This would call your PDF generation service
        self.message_user(
            request,
            "PDF generation would be implemented here."
        )
    generate_pdfs.short_description = "Generate PDFs for selected invoices"

@admin.register(InvoicePayment)
class InvoicePaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'invoice_link',
        'amount',
        'payment_method',
        'payment_date'
    ]
    list_filter = ['payment_method', 'payment_date']
    search_fields = ['invoice__invoice_number', 'transaction_id']
    readonly_fields = ['created_at']

    def invoice_link(self, obj):
        url = reverse('admin:invoice_invoice_change', args=[obj.invoice.id])
        return format_html('<a href="{}">{}</a>', url, obj.invoice.invoice_number)
    invoice_link.short_description = 'Invoice'