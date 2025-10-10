# coupons/views.py
from rest_framework import generics, status, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Count, Sum, Avg, F
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from decimal import Decimal
import logging

from .models import Coupon, CouponUsage
from .serializers import (
    AdminCouponSerializer,
    UserCouponSerializer,
    AdminCouponUsageSerializer,
    UserCouponUsageSerializer,
    CouponApplySerializer,
    CouponValidationSerializer,
    BulkCouponCreateSerializer
)
from ecommerce.permissions import IsAdmin, IsAdminOrReadOnly
from accounts.models import User

logger = logging.getLogger(__name__)


# ============ ADMIN VIEWS ============

class AdminCouponViewSet(viewsets.ModelViewSet):
    """
    Complete CRUD operations for coupons - Admin only
    
    Provides:
    - List all coupons with filtering and search
    - Create new coupons
    - Retrieve specific coupon details
    - Update existing coupons
    - Delete coupons
    - Bulk operations
    - Analytics and reporting
    """
    queryset = Coupon.objects.all()
    serializer_class = AdminCouponSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'coupon_type',
        'is_active',
        'applicable_to',
        'assigned_to_all',
        'created_by'
    ]
    search_fields = ['code', 'description']
    ordering_fields = ['valid_from', 'valid_to', 'created_at', 'used_count', 'discount_value']
    ordering = ['-created_at']

    def get_queryset(self):
        """Enhanced queryset with advanced filtering"""
        queryset = super().get_queryset()
        
        # Filter by validity status
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
        elif valid == 'expired':
            queryset = queryset.filter(valid_to__lt=now)
        elif valid == 'future':
            queryset = queryset.filter(valid_from__gt=now)
        
        # Filter by usage status
        usage_status = self.request.query_params.get('usage_status', None)
        if usage_status == 'unused':
            queryset = queryset.filter(used_count=0)
        elif usage_status == 'partially_used':
            queryset = queryset.filter(used_count__gt=0, used_count__lt=F('max_uses'))
        elif usage_status == 'fully_used':
            queryset = queryset.filter(used_count__gte=F('max_uses'))
        
        # Filter by date range
        date_from = self.request.query_params.get('created_from')
        date_to = self.request.query_params.get('created_to')
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset.select_related('created_by').prefetch_related('assigned_users')

    def perform_create(self, serializer):
        """Set created_by field during creation"""
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        """Soft delete or prevent deletion if coupon has been used"""
        if instance.used_count > 0:
            # Instead of deleting, deactivate the coupon
            instance.is_active = False
            instance.save()
            logger.info(f"Deactivated coupon {instance.code} instead of deletion due to usage history")
        else:
            # Safe to delete unused coupons
            super().perform_destroy(instance)
            logger.info(f"Deleted unused coupon {instance.code}")

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Bulk create coupons with sequential codes"""
        serializer = BulkCouponCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        base_code = validated_data.pop('base_code')
        quantity = validated_data.pop('quantity')
        
        created_coupons = []
        
        with transaction.atomic():
            for i in range(1, quantity + 1):
                code = f"{base_code}{i:03d}"  # e.g., WELCOME001, WELCOME002
                
                # Check if code already exists
                if Coupon.objects.filter(code=code).exists():
                    return Response({
                        'error': f'Coupon code {code} already exists'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                coupon_data = validated_data.copy()
                coupon_data['code'] = code
                coupon_data['created_by'] = request.user
                
                coupon = Coupon.objects.create(**coupon_data)
                created_coupons.append(coupon)
        
        serializer = AdminCouponSerializer(created_coupons, many=True, context={'request': request})
        return Response({
            'message': f'Successfully created {quantity} coupons',
            'coupons': serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get coupon analytics and statistics"""
        queryset = self.get_queryset()
        
        # Basic statistics
        total_coupons = queryset.count()
        active_coupons = queryset.filter(is_active=True).count()
        expired_coupons = queryset.filter(valid_to__lt=timezone.now()).count()
        
        # Usage statistics
        total_usage = CouponUsage.objects.count()
        total_discount_given = CouponUsage.objects.aggregate(
            total=Sum('discount_amount')
        )['total'] or Decimal('0')
        
        # Top performing coupons
        top_used_coupons = queryset.annotate(
            usage_count=Count('usages')
        ).order_by('-usage_count')[:5]
        
        # Coupon type distribution
        type_distribution = queryset.values('coupon_type').annotate(
            count=Count('id')
        )
        
        analytics_data = {
            'overview': {
                'total_coupons': total_coupons,
                'active_coupons': active_coupons,
                'expired_coupons': expired_coupons,
                'usage_rate': round((total_usage / total_coupons * 100), 2) if total_coupons > 0 else 0
            },
            'financial': {
                'total_discount_given': total_discount_given,
                'average_discount_per_usage': round(total_discount_given / total_usage, 2) if total_usage > 0 else 0
            },
            'top_performers': AdminCouponSerializer(
                top_used_coupons, many=True, context={'request': request}
            ).data,
            'type_distribution': list(type_distribution)
        }
        
        return Response(analytics_data)

    @action(detail=True, methods=['get'])
    def usage_history(self, request, pk=None):
        """Get detailed usage history for a specific coupon"""
        coupon = self.get_object()
        usages = CouponUsage.objects.filter(coupon=coupon).select_related('user')
        
        serializer = AdminCouponUsageSerializer(usages, many=True, context={'request': request})
        return Response({
            'coupon_code': coupon.code,
            'total_usages': usages.count(),
            'usages': serializer.data
        })

    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """Toggle coupon active/inactive status"""
        coupon = self.get_object()
        coupon.is_active = not coupon.is_active
        coupon.save()
        
        serializer = AdminCouponSerializer(coupon, context={'request': request})
        return Response({
            'message': f'Coupon {coupon.code} {"activated" if coupon.is_active else "deactivated"}',
            'coupon': serializer.data
        })


class AdminCouponUsageListView(generics.ListAPIView):
    """List all coupon usages - Admin only"""
    serializer_class = AdminCouponUsageSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['coupon', 'user', 'coupon__coupon_type']
    search_fields = ['coupon__code', 'user__email', 'order_id']
    ordering_fields = ['applied_at', 'discount_amount']
    ordering = ['-applied_at']

    def get_queryset(self):
        queryset = CouponUsage.objects.select_related('coupon', 'user')
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(applied_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(applied_at__lte=date_to)
        
        return queryset


# ============ USER VIEWS ============

class UserCouponListView(generics.ListAPIView):
    """
    List coupons available to the authenticated user
    Shows both assigned coupons and public coupons
    """
    serializer_class = UserCouponSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['coupon_type', 'applicable_to']
    search_fields = ['code', 'description']
    ordering_fields = ['valid_to', 'discount_value']
    ordering = ['valid_to']  # Show expiring soon first

    def get_queryset(self):
        """Get coupons available to current user"""
        user = self.request.user
        now = timezone.now()
        
        # Get both public coupons and user-assigned coupons
        queryset = Coupon.objects.filter(
            Q(assigned_to_all=True) | Q(assigned_users=user),
            is_active=True,
            valid_from__lte=now,
            valid_to__gte=now
        ).distinct()
        
        # Filter by usage availability
        available_only = self.request.query_params.get('available_only', 'true')
        if available_only.lower() == 'true':
            # Only show coupons that can still be used
            from django.db.models import F
            queryset = queryset.filter(used_count__lt=F('max_uses'))
        
        return queryset

    def list(self, request, *args, **kwargs):
        """Enhanced list response with user context"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        # Always return custom format, regardless of pagination
        response_data = {
            'count': queryset.count(),
            'available_coupons': serializer.data,
            'summary': {
                'total_available': queryset.count(),
                'expiring_soon': queryset.filter(
                    valid_to__lte=timezone.now() + timezone.timedelta(days=7)
                ).count(),
                'percentage_coupons': queryset.filter(coupon_type='percentage').count(),
                'fixed_amount_coupons': queryset.filter(coupon_type='fixed_amount').count()
            }
        }
        
        return Response(response_data)


class UserCouponDetailView(generics.RetrieveAPIView):
    """Get details of a specific coupon if available to user"""
    serializer_class = UserCouponSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Coupon.objects.filter(
            Q(assigned_to_all=True) | Q(assigned_users=user),
            is_active=True
        ).distinct()


class UserCouponUsageListView(generics.ListAPIView):
    """List user's own coupon usage history"""
    serializer_class = UserCouponUsageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['coupon__coupon_type']
    ordering_fields = ['applied_at']
    ordering = ['-applied_at']

    def get_queryset(self):
        return CouponUsage.objects.filter(
            user=self.request.user
        ).select_related('coupon')


# ============ APPLICATION VIEWS ============

class CouponValidateView(APIView):
    """Validate a coupon without applying it"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CouponValidationSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        coupon = serializer.validated_data['coupon']
        is_valid = serializer.validated_data['is_valid']
        message = serializer.validated_data['message']
        cart_total = serializer.validated_data.get('cart_total', 0)
        
        response_data = {
            'coupon_code': coupon.code,
            'is_valid': is_valid,
            'message': message,
            'coupon_details': {
                'description': coupon.description,
                'coupon_type': coupon.get_coupon_type_display(),
                'discount_value': coupon.discount_value,
                'min_order_amount': coupon.min_order_amount,
                'applicable_to': coupon.get_applicable_to_display(),
                'valid_until': coupon.valid_to,
                'max_discount': coupon.max_discount if coupon.coupon_type == 'percentage' else None
            }
        }
        
        if is_valid and cart_total > 0:
            discount_amount = coupon.apply_discount(cart_total)
            response_data['preview'] = {
                'cart_total': cart_total,
                'discount_amount': discount_amount,
                'final_total': cart_total - discount_amount,
                'savings_percentage': round((discount_amount / cart_total) * 100, 2)
            }
        
        return Response(response_data)


class CouponApplyView(APIView):
    """Apply a coupon to cart and calculate discount"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CouponApplySerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        coupon = serializer.validated_data['coupon']
        cart_total = serializer.validated_data['cart_total']
        
        try:
            discount_amount = coupon.apply_discount(cart_total)
            new_total = cart_total - discount_amount
            
            # Log the application attempt
            logger.info(
                f"Coupon {coupon.code} applied by user {request.user.email}. "
                f"Cart: ₹{cart_total}, Discount: ₹{discount_amount}, New Total: ₹{new_total}"
            )
            
            response_data = {
                'success': True,
                'message': 'Coupon applied successfully',
                'coupon_code': coupon.code,
                'coupon_description': coupon.description,
                'discount_amount': discount_amount,
                'discount_type': coupon.get_coupon_type_display(),
                'original_total': cart_total,
                'new_total': new_total,
                'savings_percentage': round((discount_amount / cart_total) * 100, 2) if cart_total > 0 else 0,
                'applicable_to': coupon.get_applicable_to_display(),
                'coupon_details': {
                    'id': coupon.id,
                    'min_order_amount': coupon.min_order_amount,
                    'max_discount': coupon.max_discount,
                    'valid_until': coupon.valid_to,
                    'remaining_uses': max(0, coupon.max_uses - coupon.used_count)
                }
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error applying coupon {coupon.code}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Failed to apply coupon. Please try again.',
                'error': str(e) if settings.DEBUG else None
            }, status=status.HTTP_400_BAD_REQUEST)


class CouponRecordUsageView(APIView):
    """Record actual coupon usage after successful order"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Record coupon usage after order completion
        Expected payload: {
            'coupon_code': 'WELCOME10',
            'order_id': 'ORD123456',
            'discount_amount': '50.00'
        }
        """
        coupon_code = request.data.get('coupon_code')
        order_id = request.data.get('order_id')
        discount_amount = request.data.get('discount_amount')
        
        if not all([coupon_code, order_id, discount_amount]):
            return Response({
                'error': 'coupon_code, order_id, and discount_amount are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            coupon = Coupon.objects.get(code=coupon_code, is_active=True)
        except Coupon.DoesNotExist:
            return Response({
                'error': 'Invalid coupon code'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Record the usage
            coupon.record_usage(
                user=request.user,
                order_id=order_id,
                discount_amount=Decimal(str(discount_amount))
            )
            
            logger.info(
                f"Recorded coupon usage: {coupon_code} by {request.user.email} "
                f"for order {order_id} with discount ₹{discount_amount}"
            )
            
            return Response({
                'success': True,
                'message': 'Coupon usage recorded successfully',
                'coupon_code': coupon_code,
                'remaining_uses': max(0, coupon.max_uses - coupon.used_count)
            }, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error recording coupon usage: {str(e)}")
            return Response({
                'error': 'Failed to record coupon usage'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============ PUBLIC VIEWS ============

class PublicCouponListView(generics.ListAPIView):
    """
    List public coupons that are available to all users
    Accessible without authentication for promotional purposes
    """
    serializer_class = UserCouponSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['coupon_type', 'applicable_to']
    ordering_fields = ['valid_to', 'discount_value']
    ordering = ['valid_to']

    def get_queryset(self):
        """Get only public coupons that are currently valid"""
        now = timezone.now()
        return Coupon.objects.filter(
            assigned_to_all=True,
            is_active=True,
            valid_from__lte=now,
            valid_to__gte=now
        ).exclude(
            # Exclude fully used coupons
            used_count__gte=F('max_uses')
        )

    def list(self, request, *args, **kwargs):
        """Limited information for public view"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Limit public exposure - only show basic info
        limited_data = []
        for coupon in queryset:
            discount_display = f"{coupon.discount_value}% off" if coupon.coupon_type == 'percentage' else f"₹{coupon.discount_value} off"
            if coupon.coupon_type == 'percentage' and coupon.max_discount:
                discount_display += f" (max ₹{coupon.max_discount})"
            
            limited_data.append({
                'code': coupon.code,
                'description': coupon.description,
                'discount_display': discount_display,
                'min_order_amount': coupon.min_order_amount,
                'applicable_to': coupon.get_applicable_to_display(),
                'valid_until': coupon.valid_to,
                'days_remaining': (coupon.valid_to - now).days
            })
        
        return Response({
            'count': len(limited_data),
            'promotional_coupons': limited_data
        })