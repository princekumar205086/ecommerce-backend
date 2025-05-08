# invoice/views.py
from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.utils import timezone
from rest_framework.views import APIView

from .models import Invoice
from .serializers import (
    InvoiceSerializer,
    CreateInvoiceSerializer,
    InvoicePaymentSerializer,
    RecordPaymentSerializer
)


class InvoiceListView(generics.ListAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'payment_terms']
    search_fields = ['invoice_number', 'order__order_number']
    ordering_fields = ['issued_date', 'due_date', 'total_amount']

    def get_queryset(self):
        user = self.request.user
        queryset = Invoice.objects.select_related('order').prefetch_related(
            'line_items', 'payments'
        )

        # Admins can see all invoices, others only their own
        if user.role != 'admin':
            queryset = queryset.filter(order__user=user)

        return queryset.order_by('-issued_date')


class InvoiceCreateView(generics.CreateAPIView):
    serializer_class = CreateInvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        order = serializer.validated_data['order']

        # Only admin or order owner can create invoice
        if self.request.user.role != 'admin' and order.user != self.request.user:
            raise permissions.PermissionDenied(
                "You don't have permission to create an invoice for this order"
            )

        with transaction.atomic():
            invoice = serializer.save()

            # Create line items from order items
            for order_item in order.items.all():
                product = order_item.product
                invoice.line_items.create(
                    product_name=product.name,
                    product_description=product.description,
                    quantity=order_item.quantity,
                    unit_price=order_item.price,
                    total_price=order_item.total_price
                )

            # Update invoice totals
            invoice.calculate_totals()
            invoice.save()


class InvoiceDetailView(generics.RetrieveAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):  # Bypass for schema generation
            return Invoice.objects.none()

        user = self.request.user
        if user.role != 'admin':
            raise PermissionDenied("You do not have permission to view this.")
        return Invoice.objects.filter(user=user)


class InvoicePDFView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)

        # Check permissions
        if request.user.role != 'admin' and invoice.order.user != request.user:
            raise permissions.PermissionDenied(
                "You don't have permission to view this invoice"
            )

        if not invoice.pdf_file:
            return Response(
                {'detail': 'PDF not yet generated'},
                status=status.HTTP_404_NOT_FOUND
            )

        response = FileResponse(invoice.pdf_file.open('rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number}.pdf"'
        return response


class RecordPaymentView(generics.CreateAPIView):
    serializer_class = RecordPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Invoice.objects.none()  # Default queryset for schema generation

    def get_invoice(self):
        if getattr(self, 'swagger_fake_view', False):  # Bypass for schema generation
            return None
        return get_object_or_404(Invoice, pk=self.kwargs.get('pk'))

    def perform_create(self, serializer):
        invoice = self.get_invoice()

        if not invoice:  # Skip logic if schema generation
            return

        # Check permissions
        if self.request.user.role != 'admin' and invoice.order.user != self.request.user:
            raise permissions.PermissionDenied(
                "You don't have permission to record payment for this invoice"
            )

        with transaction.atomic():
            payment = serializer.save(invoice=invoice)

            # Update invoice payment status
            invoice.mark_as_paid(payment.amount)

            # Update order payment status if fully paid
            if invoice.balance_due <= 0:
                invoice.order.payment_status = 'paid'
                invoice.order.save()

class InvoicePaymentListView(generics.ListAPIView):
    serializer_class = InvoicePaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = []
    pagination_class = None

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):  # Bypass for schema generation
            return Invoice.objects.none()

        invoice = get_object_or_404(Invoice, pk=self.kwargs.get('pk'))
        return invoice.payments.all()


class OverdueInvoicesView(generics.ListAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Invoice.objects.filter(
            status__in=['sent', 'draft'],
            balance_due__gt=0,
            due_date__lt=timezone.now().date()
        ).select_related('order')

        if user.role != 'admin':
            queryset = queryset.filter(order__user=user)

        return queryset.order_by('due_date')
