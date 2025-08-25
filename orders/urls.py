from django.urls import path
from .views import (
    OrderListView,
    OrderDetailView,
    CartCheckoutView,
    ApplyCouponView,
    OrderStatsView
)
from .admin_views import (
    AcceptOrderView,
    RejectOrderView,
    AssignShippingView,
    MarkDeliveredView
)

urlpatterns = [
    path('checkout/', CartCheckoutView.as_view(), name='cart-checkout'),
    path('', OrderListView.as_view(), name='order-list'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('<int:order_id>/apply-coupon/', ApplyCouponView.as_view(), name='apply-coupon'),
    path('stats/', OrderStatsView.as_view(), name='order-stats'),
    
    # Admin endpoints
    path('admin/accept/', AcceptOrderView.as_view(), name='admin-accept-order'),
    path('admin/reject/', RejectOrderView.as_view(), name='admin-reject-order'),
    path('admin/assign-shipping/', AssignShippingView.as_view(), name='admin-assign-shipping'),
    path('admin/mark-delivered/', MarkDeliveredView.as_view(), name='admin-mark-delivered'),
]
