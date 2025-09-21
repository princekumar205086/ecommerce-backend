from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import uuid

from .models import Address, CheckoutSession
from .serializers import (
    AddressSerializer,
    CheckoutSessionSerializer,
    InitiateCheckoutSerializer,
    UpdateCheckoutAddressSerializer,
    UpdatePaymentMethodSerializer,
    ApplyCouponSerializer,
    CreateOrderSerializer,
    CheckoutSummarySerializer
)
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem
from coupon.models import Coupon


class IsUserOrSupplier(IsAuthenticated):
    """Custom permission for users and suppliers only"""
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.role in ['user', 'supplier']


# Address Management Views
class AddressListCreateView(generics.ListCreateAPIView):
    """List and create user addresses"""
    serializer_class = AddressSerializer
    permission_classes = [IsUserOrSupplier]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user, is_active=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, and delete user address"""
    serializer_class = AddressSerializer
    permission_classes = [IsUserOrSupplier]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user, is_active=True)

    def perform_destroy(self, instance):
        # Soft delete
        instance.is_active = False
        instance.save()


# Checkout Flow Views
class InitiateCheckoutView(APIView):
    """Initiate checkout process and create checkout session"""
    permission_classes = [IsUserOrSupplier]

    def post(self, request):
        serializer = InitiateCheckoutSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors,
                'message': 'Checkout validation failed'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Get user's cart
                cart = Cart.objects.get(user=request.user)
                
                # Create cart snapshot
                cart_items_data = []
                for item in cart.items.all():
                    cart_items_data.append({
                        'id': item.id,
                        'product_id': item.product.id,
                        'product_name': item.product.name,
                        'variant_id': item.variant.id if item.variant else None,
                        'variant_display': f"{item.variant.size} - {item.variant.color}" if item.variant else "Default",
                        'quantity': item.quantity,
                        'unit_price': float(item.total_price / item.quantity),
                        'total_price': float(item.total_price),
                        'available_stock': item.variant.stock if item.variant else item.product.stock
                    })

                # Create checkout session
                session_id = f"checkout_{uuid.uuid4().hex[:16]}"
                checkout_session = CheckoutSession.objects.create(
                    user=request.user,
                    session_id=session_id,
                    cart_items_snapshot={'items': cart_items_data},
                    subtotal=cart.total_price
                )

                return Response({
                    'success': True,
                    'message': 'Checkout session initiated successfully',
                    'session': CheckoutSessionSerializer(checkout_session).data
                }, status=status.HTTP_201_CREATED)

        except Cart.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Cart not found or empty'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Failed to initiate checkout',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CheckoutSessionDetailView(APIView):
    """Get checkout session details"""
    permission_classes = [IsUserOrSupplier]

    def get(self, request, session_id):
        try:
            checkout_session = CheckoutSession.objects.get(
                session_id=session_id,
                user=request.user
            )
            
            if checkout_session.is_expired:
                return Response({
                    'success': False,
                    'message': 'Checkout session has expired'
                }, status=status.HTTP_410_GONE)

            return Response({
                'success': True,
                'session': CheckoutSessionSerializer(checkout_session).data
            })

        except CheckoutSession.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Checkout session not found'
            }, status=status.HTTP_404_NOT_FOUND)


class UpdateCheckoutAddressView(APIView):
    """Update shipping and billing addresses for checkout"""
    permission_classes = [IsUserOrSupplier]

    def put(self, request, session_id):
        try:
            checkout_session = CheckoutSession.objects.get(
                session_id=session_id,
                user=request.user
            )
            
            if checkout_session.is_expired:
                return Response({
                    'success': False,
                    'message': 'Checkout session has expired'
                }, status=status.HTTP_410_GONE)

            serializer = UpdateCheckoutAddressSerializer(
                data=request.data,
                context={'request': request}
            )
            
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors,
                    'message': 'Invalid address data'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Update addresses
            shipping_address = Address.objects.get(
                id=serializer.validated_data['shipping_address_id'],
                user=request.user
            )
            checkout_session.shipping_address = shipping_address

            if serializer.validated_data.get('same_as_shipping', False):
                checkout_session.billing_address = shipping_address
            else:
                billing_address = Address.objects.get(
                    id=serializer.validated_data['billing_address_id'],
                    user=request.user
                )
                checkout_session.billing_address = billing_address

            checkout_session.status = 'address_selected'
            checkout_session.save()

            return Response({
                'success': True,
                'message': 'Addresses updated successfully',
                'session': CheckoutSessionSerializer(checkout_session).data
            })

        except CheckoutSession.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Checkout session not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Address.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Address not found'
            }, status=status.HTTP_404_NOT_FOUND)


class UpdatePaymentMethodView(APIView):
    """Update payment method for checkout"""
    permission_classes = [IsUserOrSupplier]

    def put(self, request, session_id):
        try:
            checkout_session = CheckoutSession.objects.get(
                session_id=session_id,
                user=request.user
            )
            
            if checkout_session.is_expired:
                return Response({
                    'success': False,
                    'message': 'Checkout session has expired'
                }, status=status.HTTP_410_GONE)

            serializer = UpdatePaymentMethodSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors,
                    'message': 'Invalid payment method'
                }, status=status.HTTP_400_BAD_REQUEST)

            checkout_session.payment_method = serializer.validated_data['payment_method']
            checkout_session.status = 'payment_method_selected'
            checkout_session.save()

            return Response({
                'success': True,
                'message': 'Payment method updated successfully',
                'session': CheckoutSessionSerializer(checkout_session).data
            })

        except CheckoutSession.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Checkout session not found'
            }, status=status.HTTP_404_NOT_FOUND)


class ApplyCouponView(APIView):
    """Apply coupon to checkout session"""
    permission_classes = [IsUserOrSupplier]

    def post(self, request, session_id):
        try:
            checkout_session = CheckoutSession.objects.get(
                session_id=session_id,
                user=request.user
            )
            
            if checkout_session.is_expired:
                return Response({
                    'success': False,
                    'message': 'Checkout session has expired'
                }, status=status.HTTP_410_GONE)

            serializer = ApplyCouponSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors,
                    'message': 'Invalid coupon code'
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                coupon = Coupon.objects.get(
                    code=serializer.validated_data['coupon_code'],
                    is_active=True
                )
                
                # Calculate discount
                if coupon.discount_type == 'percentage':
                    discount = checkout_session.subtotal * (coupon.discount_value / 100)
                    if coupon.max_discount_amount:
                        discount = min(discount, coupon.max_discount_amount)
                else:
                    discount = coupon.discount_value

                # Apply minimum order amount check
                if coupon.min_order_amount and checkout_session.subtotal < coupon.min_order_amount:
                    return Response({
                        'success': False,
                        'message': f'Minimum order amount of ₹{coupon.min_order_amount} required for this coupon'
                    }, status=status.HTTP_400_BAD_REQUEST)

                checkout_session.coupon_code = coupon.code
                checkout_session.coupon_discount = discount
                checkout_session.save()

                return Response({
                    'success': True,
                    'message': f'Coupon applied successfully. Discount: ₹{discount}',
                    'discount_amount': discount,
                    'session': CheckoutSessionSerializer(checkout_session).data
                })

            except Coupon.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Invalid or expired coupon code'
                }, status=status.HTTP_400_BAD_REQUEST)

        except CheckoutSession.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Checkout session not found'
            }, status=status.HTTP_404_NOT_FOUND)


class RemoveCouponView(APIView):
    """Remove coupon from checkout session"""
    permission_classes = [IsUserOrSupplier]

    def delete(self, request, session_id):
        try:
            checkout_session = CheckoutSession.objects.get(
                session_id=session_id,
                user=request.user
            )
            
            if checkout_session.is_expired:
                return Response({
                    'success': False,
                    'message': 'Checkout session has expired'
                }, status=status.HTTP_410_GONE)

            checkout_session.coupon_code = None
            checkout_session.coupon_discount = Decimal('0.00')
            checkout_session.save()

            return Response({
                'success': True,
                'message': 'Coupon removed successfully',
                'session': CheckoutSessionSerializer(checkout_session).data
            })

        except CheckoutSession.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Checkout session not found'
            }, status=status.HTTP_404_NOT_FOUND)


class CreateOrderView(APIView):
    """Create order from checkout session"""
    permission_classes = [IsUserOrSupplier]

    def post(self, request, session_id):
        try:
            checkout_session = CheckoutSession.objects.get(
                session_id=session_id,
                user=request.user
            )
            
            if checkout_session.is_expired:
                return Response({
                    'success': False,
                    'message': 'Checkout session has expired'
                }, status=status.HTTP_410_GONE)

            serializer = CreateOrderSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors,
                    'message': 'Invalid order data'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validate checkout session is ready for order
            if not checkout_session.shipping_address:
                return Response({
                    'success': False,
                    'message': 'Shipping address is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            if not checkout_session.payment_method:
                return Response({
                    'success': False,
                    'message': 'Payment method is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                with transaction.atomic():
                    # Create order
                    order = Order.objects.create(
                        user=request.user,
                        payment_method=checkout_session.payment_method,
                        subtotal=checkout_session.subtotal,
                        tax=checkout_session.tax_amount,
                        shipping_charge=checkout_session.shipping_charge,
                        discount=checkout_session.discount_amount,
                        total=checkout_session.total_amount,
                        coupon_discount=checkout_session.coupon_discount
                    )

                    # If coupon was used, increment usage count
                    if checkout_session.coupon_code:
                        try:
                            coupon = Coupon.objects.get(code=checkout_session.coupon_code)
                            order.coupon = coupon
                            coupon.used_count += 1
                            coupon.save()
                        except Coupon.DoesNotExist:
                            pass

                    # Create order items from cart snapshot
                    cart_items = checkout_session.cart_items_snapshot.get('items', [])
                    for item_data in cart_items:
                        OrderItem.objects.create(
                            order=order,
                            product_id=item_data['product_id'],
                            variant_id=item_data['variant_id'],
                            quantity=item_data['quantity'],
                            price=Decimal(str(item_data['unit_price']))
                        )

                    # Update checkout session
                    checkout_session.order = order
                    checkout_session.status = 'order_created'
                    checkout_session.save()

                    # Clear user's cart
                    cart = Cart.objects.filter(user=request.user).first()
                    if cart:
                        cart.items.all().delete()

                    return Response({
                        'success': True,
                        'message': 'Order created successfully',
                        'order': {
                            'id': order.id,
                            'order_number': order.order_number,
                            'total': order.total,
                            'status': order.status,
                            'payment_method': order.payment_method
                        }
                    }, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({
                    'success': False,
                    'message': 'Failed to create order',
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except CheckoutSession.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Checkout session not found'
            }, status=status.HTTP_404_NOT_FOUND)


class CheckoutSummaryView(APIView):
    """Get checkout summary"""
    permission_classes = [IsUserOrSupplier]

    def get(self, request, session_id):
        try:
            checkout_session = CheckoutSession.objects.get(
                session_id=session_id,
                user=request.user
            )
            
            if checkout_session.is_expired:
                return Response({
                    'success': False,
                    'message': 'Checkout session has expired'
                }, status=status.HTTP_410_GONE)

            summary_data = {
                'items_count': len(checkout_session.cart_items_snapshot.get('items', [])),
                'subtotal': checkout_session.subtotal,
                'shipping_charge': checkout_session.shipping_charge,
                'tax_amount': checkout_session.tax_amount,
                'discount_amount': checkout_session.discount_amount,
                'coupon_discount': checkout_session.coupon_discount,
                'total_amount': checkout_session.total_amount,
                'payment_method': checkout_session.payment_method,
                'has_shipping_address': checkout_session.shipping_address is not None,
                'has_billing_address': checkout_session.billing_address is not None,
                'is_ready_for_order': (
                    checkout_session.shipping_address is not None and
                    checkout_session.payment_method is not None
                )
            }

            return Response({
                'success': True,
                'summary': summary_data
            })

        except CheckoutSession.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Checkout session not found'
            }, status=status.HTTP_404_NOT_FOUND)
