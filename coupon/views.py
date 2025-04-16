# coupons/views.py
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Coupon, CouponUsage
from .serializers import (
    CouponSerializer,
    CouponUsageSerializer,
    CouponApplySerializer
)
from ecommerce.permissions import IsAdmin
from django.utils import timezone
from django.db.models import Q


class CouponListCreateView(generics.ListCreateAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'coupon_type',
        'is_active',
        'applicable_to',
        'assigned_to_all'
    ]
    search_fields = ['code', 'description']
    ordering_fields = ['valid_from', 'valid_to', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by validity
        valid = self.request.query_params.get('valid', None)
        now = timezone.now()

        if valid == 'true':
            queryset = queryset.filter(
                valid_from__lte=now,
                valid_to__gte=now,
                is_active=True
            )
        elif valid == 'false':
            queryset = queryset.filter(
                Q(valid_from__gt=now) |
                Q(valid_to__lt=now) |
                Q(is_active=False)
            )

        return queryset


class CouponDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsAdmin]


class CouponUsageListView(generics.ListAPIView):
    serializer_class = CouponUsageSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['coupon', 'user']
    ordering_fields = ['applied_at']
    ordering = ['-applied_at']

    def get_queryset(self):
        coupon_id = self.kwargs.get('coupon_id')
        if coupon_id:
            return CouponUsage.objects.filter(coupon_id=coupon_id)
        return CouponUsage.objects.all()


class CouponApplyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = CouponApplySerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        coupon = serializer.validated_data['coupon']
        cart_total = serializer.validated_data['cart_total']

        discount_amount = coupon.apply_discount(cart_total)

        return Response({
            'success': True,
            'coupon_code': coupon.code,
            'discount_amount': discount_amount,
            'discount_type': coupon.get_coupon_type_display(),
            'new_total': cart_total - discount_amount
        }, status=status.HTTP_200_OK)