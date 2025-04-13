from django.urls import path
from .views import CouponListCreateView, ApplyCouponView

urlpatterns = [
    path('', CouponListCreateView.as_view(), name='coupon-list-create'),
    path('apply/', ApplyCouponView.as_view(), name='apply-coupon'),
]
