from django.urls import path
from .views import (
    OrderListView,
    OrderDetailView,
    CartCheckoutView,
    ApplyCouponView,
    OrderStatsView
)

urlpatterns = [
    path('checkout/', CartCheckoutView.as_view(), name='cart-checkout'),
    path('', OrderListView.as_view(), name='order-list'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('<int:order_id>/apply-coupon/', ApplyCouponView.as_view(), name='apply-coupon'),
    path('stats/', OrderStatsView.as_view(), name='order-stats'),
]
