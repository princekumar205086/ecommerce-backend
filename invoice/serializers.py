# invoice/serializers.py
from rest_framework import serializers
from .models import Invoice, InvoiceLineItem, InvoicePayment
from orders.models import Order
from orders.serializers import OrderSerializer

class InvoiceLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLineItem
        fields = [
            'id',
            'product_name',
            'product_description',
            'quantity',
            'unit_price',
            'tax_rate',
            'discount',
            'total_price'
        ]
        read_only_fields = ['total_price']

class InvoicePaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoicePayment
        fields = [
            'id',
            'amount',
            'payment_method',
            'transaction_id',
            'payment_date',
            'notes',
            'created_at'
        ]

class InvoiceSerializer(serializers.ModelSerializer):
    line_items = InvoiceLineItemSerializer(many=True, read_only=True)
    payments = InvoicePaymentSerializer(many=True, read_only=True)
    order = OrderSerializer(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    payment_terms_display = serializers.CharField(
        source='get_payment_terms_display',
        read_only=True
    )

    class Meta:
        model = Invoice
        fields = [
            'id',
            'invoice_number',
            'order',
            'status',
            'status_display',
            'issued_date',
            'due_date',
            'payment_terms',
            'payment_terms_display',
            'subtotal',
            'tax_amount',
            'shipping_charge',
            'discount_amount',
            'total_amount',
            'amount_paid',
            'balance_due',
            'is_overdue',
            'notes',
            'terms_conditions',
            'pdf_file',
            'line_items',
            'payments',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'invoice_number',
            'subtotal',
            'tax_amount',
            'shipping_charge',
            'discount_amount',
            'total_amount',
            'balance_due',
            'is_overdue',
            'pdf_file'
        ]

class CreateInvoiceSerializer(serializers.ModelSerializer):
    order_id = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(),
        source='order',
        write_only=True
    )

    class Meta:
        model = Invoice
        fields = [
            'order_id',
            'payment_terms',
            'notes',
            'terms_conditions'
        ]

    def validate_order_id(self, value):
        if hasattr(value, 'invoice'):
            raise serializers.ValidationError("This order already has an invoice")
        return value

class RecordPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoicePayment
        fields = [
            'amount',
            'payment_method',
            'transaction_id',
            'payment_date',
            'notes'
        ]

    def validate_amount(self, value):
        invoice = self.context['invoice']
        if value > invoice.balance_due:
            raise serializers.ValidationError(
                f"Payment amount cannot exceed balance due of {invoice.balance_due}"
            )
        return value