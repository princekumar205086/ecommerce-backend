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
from cart.models import Cart
from .serializers import PaymentSerializer, CreatePaymentSerializer, CreatePaymentFromCartSerializer, VerifyPaymentSerializer, ConfirmCODSerializer
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from decimal import Decimal

client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))


class CreatePaymentFromCartView(APIView):
    """NEW: Create payment directly from cart (payment-first flow) with COD support"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreatePaymentFromCartSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        # Get cart and calculate totals
        # Get cart - either from cart_id or user's active cart
        cart_id = serializer.validated_data.get('cart_id')
        if cart_id:
            cart = get_object_or_404(Cart, id=cart_id, user=request.user)
        else:
            # Get user's active cart
            try:
                cart = Cart.objects.get(user=request.user)
            except Cart.DoesNotExist:
                return Response({'error': 'No active cart found'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate order totals (same logic as Order.create_from_cart)
        subtotal = Decimal(str(sum(item.total_price for item in cart.items.all())))
        tax_rate = Decimal('0.18')  # 18% GST
        tax = subtotal * tax_rate
        shipping_charge = Decimal('50.00')  # Flat shipping
        total = subtotal + tax + shipping_charge
        
        # Apply coupon if provided
        coupon_discount = Decimal('0.00')
        if serializer.validated_data.get('coupon_code'):
            from coupon.models import Coupon
            try:
                coupon = Coupon.objects.get(code=serializer.validated_data['coupon_code'])
                is_valid, _ = coupon.is_valid(request.user, subtotal)
                if is_valid:
                    coupon_discount = Decimal(str(coupon.apply_discount(subtotal)))
                    total -= coupon_discount
            except Coupon.DoesNotExist:
                pass

        # Save address to user profile if requested
        if serializer.validated_data.get('save_address', True):
            request.user.update_address(serializer.validated_data['shipping_address'])

        payment_method = serializer.validated_data['payment_method']
        
        # Handle COD payments differently
        if payment_method == 'cod':
            # Store cart data for later order creation
            cart_data = {
                'cart_id': cart.id,
                'items': [
                    {
                        'product_id': item.product.id,
                        'variant_id': item.variant.id if item.variant else None,
                        'quantity': item.quantity,
                        'price': str(item.total_price)
                    }
                    for item in cart.items.all()
                ],
                'subtotal': str(subtotal),
                'tax': str(tax),
                'shipping_charge': str(shipping_charge),
                'coupon_discount': str(coupon_discount),
                'total': str(total)
            }

            # Create COD payment record (no Razorpay order needed)
            payment = Payment.objects.create(
                user=request.user,
                amount=total,
                currency=serializer.validated_data['currency'],
                cart_data=cart_data,
                shipping_address=serializer.validated_data['shipping_address'],
                billing_address=serializer.validated_data['billing_address'],
                payment_method='cod',
                coupon_code=serializer.validated_data.get('coupon_code'),
                cod_notes=serializer.validated_data.get('cod_notes', ''),
                status='pending'
            )

            return Response({
                'payment_method': 'cod',
                'payment_id': payment.id,
                'amount': float(total),
                'currency': serializer.validated_data['currency'],
                'message': 'COD order created. Please confirm to proceed.',
                'next_step': f'/api/payments/confirm-cod/',
                'order_summary': {
                    'subtotal': float(subtotal),
                    'tax': float(tax),
                    'shipping': float(shipping_charge),
                    'discount': float(coupon_discount),
                    'total': float(total)
                }
            })

        # Handle Pathlog Wallet payments
        if payment_method == 'pathlog_wallet':
            # Store cart data for later order creation
            cart_data = {
                'cart_id': cart.id,
                'items': [
                    {
                        'product_id': item.product.id,
                        'variant_id': item.variant.id if item.variant else None,
                        'quantity': item.quantity,
                        'price': str(item.total_price)
                    }
                    for item in cart.items.all()
                ],
                'subtotal': str(subtotal),
                'tax': str(tax),
                'shipping_charge': str(shipping_charge),
                'coupon_discount': str(coupon_discount),
                'total': str(total)
            }

            # Create Pathlog Wallet payment record
            payment = Payment.objects.create(
                user=request.user,
                amount=total,
                currency=serializer.validated_data['currency'],
                cart_data=cart_data,
                shipping_address=serializer.validated_data['shipping_address'],
                billing_address=serializer.validated_data['billing_address'],
                payment_method='pathlog_wallet',
                coupon_code=serializer.validated_data.get('coupon_code'),
                status='pending'
            )

            return Response({
                'payment_method': 'pathlog_wallet',
                'payment_id': payment.id,
                'amount': float(total),
                'currency': serializer.validated_data['currency'],
                'message': 'Pathlog Wallet payment created. Please verify your wallet to proceed.',
                'next_step': f'/api/payments/pathlog-wallet/verify/',
                'verification_required': True,
                'order_summary': {
                    'subtotal': float(subtotal),
                    'tax': float(tax),
                    'shipping': float(shipping_charge),
                    'discount': float(coupon_discount),
                    'total': float(total)
                }
            })

        # Handle online payments (existing Razorpay flow)
        try:
            # Create Razorpay order
            razorpay_order = client.order.create({
                'amount': int(total * 100),  # Convert to paise
                'currency': serializer.validated_data['currency'],
                'payment_capture': 1  # Auto-capture payment
            })

            # Store cart data for later order creation
            cart_data = {
                'cart_id': cart.id,
                'items': [
                    {
                        'product_id': item.product.id,
                        'variant_id': item.variant.id if item.variant else None,
                        'quantity': item.quantity,
                        'price': str(item.total_price)
                    }
                    for item in cart.items.all()
                ],
                'subtotal': str(subtotal),
                'tax': str(tax),
                'shipping_charge': str(shipping_charge),
                'coupon_discount': str(coupon_discount),
                'total': str(total)
            }

            # Create payment record without order
            payment = Payment.objects.create(
                user=request.user,
                razorpay_order_id=razorpay_order['id'],
                amount=total,
                currency=serializer.validated_data['currency'],
                cart_data=cart_data,
                shipping_address=serializer.validated_data['shipping_address'],
                billing_address=serializer.validated_data['billing_address'],
                payment_method=serializer.validated_data['payment_method'],
                coupon_code=serializer.validated_data.get('coupon_code')
            )

            return Response({
                'payment_method': 'razorpay',
                'payment_id': payment.id,
                'amount': float(total),
                'currency': serializer.validated_data['currency'],
                'razorpay_order_id': razorpay_order['id'],
                'razorpay_key': settings.RAZORPAY_API_KEY,
                'key': settings.RAZORPAY_API_KEY,  # For backward compatibility
                'message': 'Razorpay order created successfully',
                'app_name': settings.APP_NAME,
                'description': f'Payment for Cart {cart.id}',
                'prefill': {
                    'name': request.user.full_name,
                    'email': request.user.email
                },
                'notes': {
                    'cart_id': cart.id,
                    'payment_id': payment.id
                },
                'order_summary': {
                    'subtotal': float(subtotal),
                    'tax': float(tax),
                    'shipping': float(shipping_charge),
                    'discount': float(coupon_discount),
                    'total': float(total)
                }
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreatePaymentView(APIView):
    """LEGACY: Create payment from existing order"""
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
                user=request.user,
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
            user=request.user
        )

        try:
            if payment.verify_payment(serializer.validated_data['razorpay_signature']):
                payment.razorpay_payment_id = serializer.validated_data['razorpay_payment_id']
                payment.razorpay_signature = serializer.validated_data['razorpay_signature']
                payment.status = 'successful'
                payment.save()

                # Create order if this was a cart-first payment
                if payment.cart_data and not payment.order:
                    order = payment.create_order_from_cart_data()
                    if order:
                        return Response({
                            'status': 'Payment successful',
                            'order_created': True,
                            'order_id': order.id,
                            'order_number': order.order_number
                        }, status=status.HTTP_200_OK)
                    else:
                        return Response({
                            'status': 'Payment successful but order creation failed',
                            'order_created': False
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                # Update existing order status (legacy flow)
                elif payment.order:
                    payment.order.payment_status = 'paid'
                    payment.order.save()
                    return Response({
                        'status': 'Payment successful',
                        'order_updated': True,
                        'order_id': payment.order.id
                    }, status=status.HTTP_200_OK)
                
                return Response({'status': 'Payment successful'}, status=status.HTTP_200_OK)
            else:
                payment.status = 'failed'
                payment.save()
                return Response({'error': 'Payment verification failed'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ConfirmRazorpayView(APIView):
    """Confirm Razorpay payment and create order"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from .serializers import ConfirmRazorpaySerializer
        
        serializer = ConfirmRazorpaySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                payment_id = serializer.validated_data['payment_id']
                payment = Payment.objects.get(id=payment_id, user=request.user)
                
                # First update payment with Razorpay data so verification can work
                payment.razorpay_payment_id = serializer.validated_data['razorpay_payment_id']
                payment.razorpay_signature = serializer.validated_data['razorpay_signature']
                
                # Verify the signature
                if payment.verify_payment(serializer.validated_data['razorpay_signature']):
                    # Mark payment as successful
                    payment.status = 'successful'
                    payment.save()

                    # Create order if this was a cart-first payment
                    if payment.cart_data and not payment.order:
                        order = payment.create_order_from_cart_data()
                        if order:
                            return Response({
                                'status': 'Payment successful',
                                'message': f'Payment successful. Order created: #{order.order_number}',
                                'order_created': True,
                                'order_id': order.id,
                                'order_number': order.order_number,
                                'payment': {
                                    'id': payment.id,
                                    'status': payment.status,
                                    'amount': str(payment.amount),
                                    'razorpay_payment_id': payment.razorpay_payment_id
                                }
                            }, status=status.HTTP_200_OK)
                        else:
                            return Response({
                                'status': 'Payment successful but order creation failed',
                                'order_created': False
                            }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Update existing order status (legacy flow)
                    elif payment.order:
                        payment.order.payment_status = 'paid'
                        payment.order.save()
                        return Response({
                            'status': 'Payment successful',
                            'order_updated': True,
                            'order_id': payment.order.id
                        }, status=status.HTTP_200_OK)
                    
                    return Response({
                        'status': 'Payment successful',
                        'payment_id': payment.id
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'error': 'Payment verification failed'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except Payment.DoesNotExist:
                return Response({
                    'error': 'Payment not found'
                }, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({
                    'error': f'Payment confirmation failed: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

                    # Create order if this was a cart-first payment
                    if payment.cart_data and not payment.order:
                        payment.create_order_from_cart_data()
                    
                    # Update existing order status (legacy flow)
                    elif payment.order:
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
        return Payment.objects.filter(user=self.request.user).order_by('-created_at')


class PaymentDetailView(generics.RetrieveAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Payment.objects.none()
        return Payment.objects.filter(user=self.request.user)


class ConfirmCODView(APIView):
    """Confirm COD payment and create order"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ConfirmCODSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        payment_id = serializer.validated_data['payment_id']
        cod_notes = serializer.validated_data.get('cod_notes', '')

        try:
            payment = get_object_or_404(Payment, id=payment_id, user=request.user)
            
            # Confirm COD payment
            success, message = payment.confirm_cod(cod_notes)
            
            if success:
                # Return order details if created
                if payment.order:
                    return Response({
                        'status': 'COD confirmed',
                        'message': message,
                        'order_created': True,
                        'order': {
                            'id': payment.order.id,
                            'order_number': payment.order.order_number,
                            'status': payment.order.status,
                            'payment_status': payment.order.payment_status,
                            'total': str(payment.order.total),
                            'items_count': payment.order.items.count()
                        },
                        'payment': {
                            'id': payment.id,
                            'status': payment.status,
                            'amount': str(payment.amount),
                            'method': payment.payment_method
                        }
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'status': 'COD confirmed',
                        'message': message,
                        'order_created': False
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'error': f'Failed to confirm COD: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PathlogWalletVerifyView(APIView):
    """Verify Pathlog Wallet with mobile number and send OTP"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        from .serializers import PathlogWalletVerifySerializer
        
        serializer = PathlogWalletVerifySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                payment_id = serializer.validated_data['payment_id']
                mobile_number = serializer.validated_data['mobile_number']
                
                payment = Payment.objects.get(id=payment_id, user=request.user)
                
                # Store mobile number temporarily
                payment.pathlog_wallet_mobile = mobile_number
                payment.save()
                
                # Demo: Send OTP (replace with actual Pathlog API)
                return Response({
                    'status': 'OTP Sent',
                    'message': f'OTP sent to +91 {mobile_number}',
                    'mobile_number': mobile_number,
                    'demo_otp': '123456'  # Remove in production
                }, status=status.HTTP_200_OK)
                
            except Payment.DoesNotExist:
                return Response({
                    'error': 'Payment not found'
                }, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({
                    'error': f'Failed to verify wallet: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PathlogWalletOTPView(APIView):
    """Verify OTP for Pathlog Wallet"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        from .serializers import PathlogWalletOTPSerializer
        
        serializer = PathlogWalletOTPSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                payment_id = serializer.validated_data['payment_id']
                otp = serializer.validated_data['otp']
                
                payment = Payment.objects.get(id=payment_id, user=request.user)
                
                success, message = payment.verify_pathlog_wallet(payment.pathlog_wallet_mobile, otp)
                
                if success:
                    # Convert both to float for calculation
                    wallet_balance = float(payment.pathlog_wallet_balance)
                    payment_amount = float(payment.amount)
                    
                    return Response({
                        'status': 'Wallet Verified Successfully',
                        'account_details': {
                            'name': 'Pathlog User',
                            'phone': f'+91 {payment.pathlog_wallet_mobile}',
                            'pathlog_id': f'PL{payment.pathlog_wallet_mobile[-6:]}'
                        },
                        'available_balance': wallet_balance,
                        'payment_amount': payment_amount,
                        'remaining_balance': wallet_balance - payment_amount,
                        'can_proceed': wallet_balance >= payment_amount
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'error': message
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except Payment.DoesNotExist:
                return Response({
                    'error': 'Payment not found'
                }, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({
                    'error': f'Failed to verify OTP: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PathlogWalletPaymentView(APIView):
    """Process payment through Pathlog Wallet"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        from .serializers import PathlogWalletPaymentSerializer
        
        serializer = PathlogWalletPaymentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                payment_id = serializer.validated_data['payment_id']
                payment = Payment.objects.get(id=payment_id, user=request.user)
                
                success, message = payment.process_pathlog_wallet_payment()
                
                if success:
                    # Return success response similar to COD
                    if 'Order created:' in message:
                        order_number = message.split('Order created: #')[1]
                        order = Order.objects.get(order_number=order_number)
                        
                        return Response({
                            'status': 'Payment Successful',
                            'message': message,
                            'transaction_id': payment.pathlog_transaction_id,
                            'order_created': True,
                            'order': {
                                'id': order.id,
                                'order_number': order.order_number,
                                'status': order.status,
                                'payment_status': order.payment_status,
                                'total': str(order.total),
                                'items_count': order.items.count()
                            },
                            'payment': {
                                'id': payment.id,
                                'status': payment.status,
                                'amount': str(payment.amount),
                                'method': payment.payment_method,
                                'transaction_id': payment.pathlog_transaction_id
                            }
                        }, status=status.HTTP_200_OK)
                    else:
                        return Response({
                            'status': 'Payment Successful',
                            'message': message,
                            'transaction_id': payment.pathlog_transaction_id,
                            'order_created': False
                        }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'error': message
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except Payment.DoesNotExist:
                return Response({
                    'error': 'Payment not found'
                }, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({
                    'error': f'Failed to process payment: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)