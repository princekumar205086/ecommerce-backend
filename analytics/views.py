# analytics/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Sum, Q, F
from django.db.models.functions import TruncDate, TruncMonth, TruncYear
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import get_object_or_404

from .models import (
    AnalyticsEvent, ProductView, SalesReport,
    UserActivity, InventoryAlert
)
from .serializers import (
    AnalyticsEventSerializer, ProductViewSerializer,
    SalesReportSerializer, UserActivitySerializer,
    InventoryAlertSerializer, DateRangeSerializer,
    ProductAnalyticsSerializer, CategoryAnalyticsSerializer
)
from products.models import Product, ProductCategory
from orders.models import Order
from accounts.models import User


class TrackEventView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        event_type = request.data.get('event_type')
        if not event_type or event_type not in dict(AnalyticsEvent.EVENT_TYPES).keys():
            return Response(
                {'error': 'Invalid event type'},
                status=status.HTTP_400_BAD_REQUEST
            )

        event = AnalyticsEvent.objects.create(
            event_type=event_type,
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            referrer=request.META.get('HTTP_REFERER', ''),
            path=request.data.get('path', ''),
            data=request.data.get('data', {})
        )

        # Special handling for product views
        if event_type == 'product_view' and 'product_id' in request.data:
            product = get_object_or_404(Product, pk=request.data['product_id'])
            ProductView.objects.create(
                product=product,
                user=request.user if request.user.is_authenticated else None,
                session_key=request.session.session_key
            )

        return Response(
            {'status': 'success', 'event_id': str(event.id)},
            status=status.HTTP_201_CREATED
        )

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AnalyticsDashboardView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, *args, **kwargs):
        # Time ranges
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        year_ago = today - timedelta(days=365)

        # Basic metrics
        total_users = User.objects.count()
        new_users = User.objects.filter(date_joined__date__gte=month_ago).count()

        total_orders = Order.objects.count()
        recent_orders = Order.objects.filter(created_at__date__gte=week_ago).count()

        total_revenue = Order.objects.filter(payment_status='paid').aggregate(
            total=Sum('total')
        )['total'] or 0
        recent_revenue = Order.objects.filter(
            payment_status='paid',
            created_at__date__gte=month_ago
        ).aggregate(
            total=Sum('total')
        )['total'] or 0

        # Activity metrics
        active_users = User.objects.filter(
            last_login__date__gte=month_ago
        ).count()

        # Product metrics
        top_products = Product.objects.annotate(
            view_count=Count('analytics_views'),
            order_count=Count('order_items')
        ).order_by('-order_count')[:5]

        # Sales trends
        sales_trends = list(
            Order.objects.filter(
                created_at__date__gte=year_ago,
                payment_status='paid'
            )
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(
                total_orders=Count('id'),
                total_revenue=Sum('total')
            )
            .order_by('month')
        )

        data = {
            'metrics': {
                'total_users': total_users,
                'new_users': new_users,
                'total_orders': total_orders,
                'recent_orders': recent_orders,
                'total_revenue': total_revenue,
                'recent_revenue': recent_revenue,
                'active_users': active_users,
            },
            'top_products': ProductSerializer(top_products, many=True).data,
            'sales_trends': sales_trends,
        }

        return Response(data)


class SalesReportListView(generics.ListAPIView):
    serializer_class = SalesReportSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = SalesReport.objects.all().order_by('-start_date')
    filter_backends = []
    pagination_class = None


class GenerateSalesReportView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, *args, **kwargs):
        serializer = DateRangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        start_date = serializer.validated_data['start_date']
        end_date = serializer.validated_data['end_date']

        # Determine period type
        delta = end_date - start_date
        if delta.days == 0:
            period_type = 'daily'
        elif delta.days <= 7:
            period_type = 'weekly'
        elif delta.days <= 31:
            period_type = 'monthly'
        elif delta.days <= 93:
            period_type = 'quarterly'
        elif delta.days <= 366:
            period_type = 'yearly'
        else:
            period_type = 'custom'

        # Create or update report
        report, created = SalesReport.objects.get_or_create(
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
            defaults={
                'period_type': period_type,
                'start_date': start_date,
                'end_date': end_date,
            }
        )

        # Calculate metrics
        report.calculate_metrics()
        report.save()

        return Response(
            SalesReportSerializer(report).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class ProductAnalyticsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, *args, **kwargs):
        # Get date range from query params
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Base querysets
        products = Product.objects.all()
        if start_date and end_date:
            date_filter = Q(created_at__date__gte=start_date) & Q(created_at__date__lte=end_date)
            products = products.filter(date_filter)

        # Annotate with analytics data
        products = products.annotate(
            total_views=Count('analytics_views'),
            total_adds_to_cart=Count(
                'analytics_events',
                filter=Q(analytics_events__event_type='add_to_cart')
            ),
            total_purchases=Count(
                'order_items',
                filter=Q(order_items__order__payment_status='paid')
            ),
        )

        # Calculate conversion rates
        results = []
        for product in products:
            conversion_rate = 0
            if product.total_views > 0:
                conversion_rate = (product.total_purchases / product.total_views) * 100

            results.append({
                'product': product,
                'total_views': product.total_views,
                'total_adds_to_cart': product.total_adds_to_cart,
                'total_purchases': product.total_purchases,
                'conversion_rate': round(conversion_rate, 2)
            })

        # Serialize and return
        serializer = ProductAnalyticsSerializer(results, many=True)
        return Response(serializer.data)


class CategoryAnalyticsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, *args, **kwargs):
        # Get date range from query params
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Base queryset
        categories = ProductCategory.objects.all()

        # Annotate with analytics data
        categories = categories.annotate(
            total_views=Count('products__analytics_views'),
            total_products=Count('products'),
            total_sales=Sum('products__order_items__quantity'),
            total_revenue=Sum(
                F('products__order_items__price') * F('products__order_items__quantity')
            )
        )

        # Filter by date if provided
        if start_date and end_date:
            categories = categories.filter(
                products__order_items__order__created_at__date__gte=start_date,
                products__order_items__order__created_at__date__lte=end_date
            )

        # Prepare results
        results = []
        for category in categories:
            results.append({
                'category': category.name,
                'total_views': category.total_views or 0,
                'total_products': category.total_products or 0,
                'total_sales': category.total_sales or 0,
                'total_revenue': category.total_revenue or 0
            })

        # Serialize and return
        serializer = CategoryAnalyticsSerializer(results, many=True)
        return Response(serializer.data)


class UserActivityView(generics.RetrieveAPIView):
    serializer_class = UserActivitySerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = UserActivity.objects.all()
    lookup_field = 'user__id'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.update_activity()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class InventoryAlertsView(generics.ListAPIView):
    serializer_class = InventoryAlertSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = InventoryAlert.objects.filter(is_resolved=False).order_by('-created_at')


class ResolveInventoryAlertView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk, *args, **kwargs):
        alert = get_object_or_404(InventoryAlert, pk=pk)
        alert.resolve(request.user)
        return Response(
            InventoryAlertSerializer(alert).data,
            status=status.HTTP_200_OK
        )


class EventLogView(generics.ListAPIView):
    serializer_class = AnalyticsEventSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = []
    pagination_class = None

    def get_queryset(self):
        queryset = AnalyticsEvent.objects.all().order_by('-created_at')

        # Filter by event type if provided
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        # Filter by date if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            )

        return queryset[:100]  # Limit to 100 most recent by default