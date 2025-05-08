from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Sum, F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, permissions
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from coupon.models import Coupon
from ecommerce.permissions import IsAdmin, IsOwnerOrAdmin
from . import serializers
from .models import Order, OrderStatusChange, OrderItem
from .serializers import (
    OrderSerializer,
    CreateOrderSerializer,
    UpdateOrderStatusSerializer
)


class OrderListView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'payment_status', 'payment_method']
    search_fields = ['order_number', 'user__email']
    ordering_fields = ['created_at', 'total']
    ordering = ['-created_at']

    def get_queryset(self):
        # Add this check for schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()

        user = self.request.user
        if user.role == 'admin':  # Check if the user is an admin
            return Order.objects.all()
        return Order.objects.filter(user=user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateOrderSerializer
        return OrderSerializer


# In views.py
class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        # Add this check for schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UpdateOrderStatusSerializer
        return OrderSerializer

    def perform_update(self, serializer):
        """Handle order status updates with change tracking"""
        if not self.request.user.is_staff:
            raise PermissionDenied("You do not have permission to update the status.")

        order = self.get_object()
        old_status = order.status
        new_status = serializer.validated_data.get('status', old_status)

        if old_status != new_status:
            OrderStatusChange.objects.create(
                order=order,
                status=new_status,
                changed_by=self.request.user,
                notes=serializer.validated_data.get('notes', '')
            )

        serializer.save()


class CartCheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Create an order from cart contents"""
        serializer = CreateOrderSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        try:
            order = serializer.save()
            return Response(
                OrderSerializer(order).data,
                status=status.HTTP_201_CREATED
            )
        except serializers.ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': 'An error occurred during checkout'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ApplyCouponView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):
        """Apply coupon to an existing order"""
        order = get_object_or_404(Order, pk=order_id, user=request.user)
        coupon_code = request.data.get('coupon_code')

        try:
            with transaction.atomic():
                order.coupon = Coupon.objects.get(code=coupon_code)
                is_valid, message = order.coupon.is_valid(request.user, order.subtotal)

                if not is_valid:
                    raise ValidationError(message)

                order.coupon_discount = order.coupon.apply_discount(order.subtotal)
                order.calculate_totals()
                order.save()

                return Response(
                    OrderSerializer(order).data,
                    status=status.HTTP_200_OK
                )
        except Coupon.DoesNotExist:
            return Response(
                {'error': 'Invalid coupon code'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class OrderStatsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        """Get order statistics for admin dashboard"""
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)

        total_revenue = Order.objects.aggregate(
            total=Sum('total')
        )['total'] or Decimal('0.00')

        stats = {
            'total_orders': Order.objects.count(),
            'total_revenue': f"{total_revenue:.2f}",
            'recent_orders': Order.objects.filter(
                created_at__gte=thirty_days_ago
            ).count(),
            'status_distribution': Order.objects.values('status').annotate(
                count=Count('id')
            ),
            'top_products': OrderItem.objects.values(
                'product__name'
            ).annotate(
                total_sold=Sum('quantity'),
                revenue=Sum(F('price') * F('quantity'))
            ).order_by('-revenue')[:10]
        }

        return Response(stats)
