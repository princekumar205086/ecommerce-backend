# coupons/urls.py
from django.urls import path
from .views import (
    CouponListCreateView,
    CouponDetailView,
    CouponUsageListView,
    CouponApplyView
)

urlpatterns = [
    path('', CouponListCreateView.as_view(), name='coupon-list-create'),
    path('<int:pk>/', CouponDetailView.as_view(), name='coupon-detail'),
    path('<int:coupon_id>/usages/', CouponUsageListView.as_view(), name='coupon-usage-list'),
    path('apply/', CouponApplyView.as_view(), name='coupon-apply'),
]