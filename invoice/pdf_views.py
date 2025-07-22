# invoice/pdf_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from .models import Invoice
from .services import generate_invoice_pdf


class GenerateInvoicePDFView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)

        # Check permissions
        if request.user.role != 'admin' and invoice.order.user != request.user:
            raise permissions.PermissionDenied(
                "You don't have permission to generate PDF for this invoice"
            )

        try:
            pdf_path = generate_invoice_pdf(invoice)
            return Response({
                'message': 'PDF generated successfully',
                'pdf_path': pdf_path,
                'download_url': f'/api/invoice/{invoice.id}/pdf/'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': f'Failed to generate PDF: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
