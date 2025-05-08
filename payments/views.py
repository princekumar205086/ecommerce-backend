from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import razorpay
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Payment
from orders.models import Order
from .serializers import PaymentSerializer, CreatePaymentSerializer, VerifyPaymentSerializer
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))


class CreatePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = get_object_or_404(Order, id=serializer.validated_data['order_id'], user=request.user)

        try:
            # Create Razorpay order
            razorpay_order = client.order.create({
                'amount': int(float(serializer.validated_data['amount']) * 100),  # Convert to paise
                'currency': serializer.validated_data['currency'],
                'payment_capture': 1  # Auto-capture payment
            })

            # Create payment record
            payment = Payment.objects.create(
                order=order,
                razorpay_order_id=razorpay_order['id'],
                amount=serializer.validated_data['amount'],
                currency=serializer.validated_data['currency']
            )

            return Response({
                'order_id': razorpay_order['id'],
                'amount': razorpay_order['amount'],
                'currency': razorpay_order['currency'],
                'key': settings.RAZORPAY_API_KEY,
                'name': settings.APP_NAME,
                'description': f'Payment for Order #{order.order_number}',
                'prefill': {
                    'name': request.user.full_name,
                    'email': request.user.email
                },
                'notes': {
                    'order_id': order.id
                }
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VerifyPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = get_object_or_404(
            Payment,
            razorpay_order_id=serializer.validated_data['razorpay_order_id'],
            order__user=request.user
        )

        try:
            if payment.verify_payment(serializer.validated_data['razorpay_signature']):
                payment.razorpay_payment_id = serializer.validated_data['razorpay_payment_id']
                payment.razorpay_signature = serializer.validated_data['razorpay_signature']
                payment.status = 'successful'
                payment.save()

                # Update order status
                payment.order.payment_status = 'paid'
                payment.order.save()

                return Response({'status': 'Payment successful'}, status=status.HTTP_200_OK)
            else:
                payment.status = 'failed'
                payment.save()
                return Response({'error': 'Payment verification failed'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class RazorpayWebhookView(APIView):
    def post(self, request):
        payload = request.body.decode('utf-8')
        signature = request.headers.get('X-Razorpay-Signature', '')

        try:
            # Verify webhook signature
            client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))
            client.utility.verify_webhook_signature(
                payload,
                signature,
                settings.RAZORPAY_WEBHOOK_SECRET
            )

            data = json.loads(payload)
            event = data.get('event')

            if event == 'payment.captured':
                payment_id = data['payload']['payment']['entity']['id']
                order_id = data['payload']['payment']['entity']['order_id']

                try:
                    payment = Payment.objects.get(razorpay_order_id=order_id)
                    payment.razorpay_payment_id = payment_id
                    payment.status = 'successful'
                    payment.webhook_verified = True
                    payment.save()

                    # Update order status
                    payment.order.payment_status = 'paid'
                    payment.order.save()

                except Payment.DoesNotExist:
                    pass

            elif event == 'payment.failed':
                order_id = data['payload']['payment']['entity']['order_id']

                try:
                    payment = Payment.objects.get(razorpay_order_id=order_id)
                    payment.status = 'failed'
                    payment.webhook_verified = True
                    payment.save()
                except Payment.DoesNotExist:
                    pass

            return HttpResponse(status=200)
        except:
            return HttpResponse(status=400)


class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Payment.objects.none()
        return Payment.objects.filter(order__user=self.request.user).order_by('-created_at')


class PaymentDetailView(generics.RetrieveAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Payment.objects.none()
        self.filter = Payment.objects.filter(order__user=self.request.user)
        return self.filter