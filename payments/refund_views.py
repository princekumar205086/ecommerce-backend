# payments/refund_views.py
import razorpay
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from .models import Payment
from .serializers import PaymentSerializer


class RefundPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, payment_id):
        payment = get_object_or_404(Payment, id=payment_id)
        
        # Check permissions
        if request.user.role != 'admin' and payment.order.user != request.user:
            raise permissions.PermissionDenied(
                "You don't have permission to refund this payment"
            )
        
        if payment.status != 'successful':
            return Response({
                'error': 'Only successful payments can be refunded'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if payment.status == 'refunded':
            return Response({
                'error': 'Payment has already been refunded'
            }, status=status.HTTP_400_BAD_REQUEST)

        refund_amount = request.data.get('amount')
        refund_reason = request.data.get('reason', 'Customer requested refund')
        
        if not refund_amount:
            refund_amount = int(float(payment.amount) * 100)  # Full refund in paise
        else:
            refund_amount = int(float(refund_amount) * 100)  # Convert to paise

        try:
            # Initialize Razorpay client
            client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))
            
            # Create refund
            refund = client.payment.refund(payment.razorpay_payment_id, {
                'amount': refund_amount,
                'speed': 'normal',
                'notes': {
                    'reason': refund_reason,
                    'order_id': payment.order.order_number
                }
            })
            
            # Update payment status
            payment.status = 'refunded'
            payment.save()
            
            # Update order status
            payment.order.payment_status = 'refunded'
            payment.order.status = 'refunded'
            payment.order.save()
            
            return Response({
                'message': 'Refund initiated successfully',
                'refund_id': refund['id'],
                'refund_amount': refund['amount'] / 100,  # Convert back to rupees
                'status': refund['status'],
                'estimated_processing_time': refund.get('speed_processed', 'normal')
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Refund failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_refund_status(request, payment_id):
    """Check the status of a refund"""
    payment = get_object_or_404(Payment, id=payment_id)
    
    # Check permissions
    if request.user.role != 'admin' and payment.order.user != request.user:
        raise permissions.PermissionDenied(
            "You don't have permission to check this payment"
        )
    
    try:
        client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))
        
        # Get all refunds for this payment
        refunds = client.payment.refund.all({'payment_id': payment.razorpay_payment_id})
        
        return Response({
            'payment_id': payment.razorpay_payment_id,
            'refunds': refunds['items']
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to check refund status: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
