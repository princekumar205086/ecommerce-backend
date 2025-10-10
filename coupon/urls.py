# coupons/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # Admin Views
    AdminCouponViewSet,
    AdminCouponUsageListView,
    
    # User Views
    UserCouponListView,
    UserCouponDetailView,
    UserCouponUsageListView,
    
    # Application Views
    CouponValidateView,
    CouponApplyView,
    CouponRecordUsageView,
    
    # Public Views
    PublicCouponListView,
)

# Create router for ViewSet
router = DefaultRouter()
router.register(r'admin/coupons', AdminCouponViewSet, basename='admin-coupon')

urlpatterns = [
    # ============ ADMIN ROUTES ============
    # ViewSet routes (admin/coupons/)
    path('', include(router.urls)),
    
    # Additional admin routes
    path('admin/usages/', AdminCouponUsageListView.as_view(), name='admin-coupon-usage-list'),
    
    # ============ USER ROUTES ============
    # User coupon management
    path('my-coupons/', UserCouponListView.as_view(), name='user-coupon-list'),
    path('my-coupons/<int:pk>/', UserCouponDetailView.as_view(), name='user-coupon-detail'),
    path('my-usage/', UserCouponUsageListView.as_view(), name='user-coupon-usage'),
    
    # ============ APPLICATION ROUTES ============
    # Coupon application and validation
    path('validate/', CouponValidateView.as_view(), name='coupon-validate'),
    path('apply/', CouponApplyView.as_view(), name='coupon-apply'),
    path('record-usage/', CouponRecordUsageView.as_view(), name='coupon-record-usage'),
    
    # ============ PUBLIC ROUTES ============
    # Public promotional coupons
    path('public/', PublicCouponListView.as_view(), name='public-coupon-list'),
]

"""
URL Structure Documentation:

ADMIN ENDPOINTS (Requires admin role):
- GET/POST    /api/coupons/admin/                    - List/Create coupons
- GET/PUT/DEL /api/coupons/admin/{id}/               - Coupon detail operations
- POST        /api/coupons/admin/bulk_create/        - Bulk create coupons
- GET         /api/coupons/admin/analytics/          - Coupon analytics
- GET         /api/coupons/admin/{id}/usage_history/ - Coupon usage history
- POST        /api/coupons/admin/{id}/toggle_status/ - Toggle coupon status
- GET         /api/coupons/admin/usages/             - All coupon usages

USER ENDPOINTS (Requires authentication):
- GET         /api/coupons/my-coupons/               - User's available coupons
- GET         /api/coupons/my-coupons/{id}/          - Specific coupon details
- GET         /api/coupons/my-usage/                 - User's coupon usage history

APPLICATION ENDPOINTS (Requires authentication):
- POST        /api/coupons/validate/                 - Validate coupon
- POST        /api/coupons/apply/                    - Apply coupon to cart
- POST        /api/coupons/record-usage/             - Record coupon usage

PUBLIC ENDPOINTS (No authentication required):
- GET         /api/coupons/public/                   - Public promotional coupons
"""