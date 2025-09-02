from django.urls import path, include
from rest_framework.routers import DefaultRouter
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
    MarkDeliveredView,
    AdminOrderViewSet
)
from .supplier_views import (
    SupplierOrderViewSet,
    SupplierOrderStatsView
)
from .shiprocket_views import (
    ShipRocketServiceabilityView,
    ShipRocketRatesView,
    CreateShipRocketOrderView,
    TrackShipmentView,
    GenerateInvoiceView
)

# Router for ViewSets
router = DefaultRouter()
router.register(r'admin/manage', AdminOrderViewSet, basename='admin-order-manage')
router.register(r'supplier', SupplierOrderViewSet, basename='supplier-orders')

urlpatterns = [
    # Basic order endpoints
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
    
    # Supplier endpoints
    path('supplier/stats/', SupplierOrderStatsView.as_view(), name='supplier-order-stats'),
    
    # ShipRocket integration endpoints
    path('shiprocket/serviceability/', ShipRocketServiceabilityView.as_view(), name='shiprocket-serviceability'),
    path('shiprocket/rates/', ShipRocketRatesView.as_view(), name='shiprocket-rates'),
    path('shiprocket/create/', CreateShipRocketOrderView.as_view(), name='shiprocket-create-order'),
    path('shiprocket/track/<int:shipment_id>/', TrackShipmentView.as_view(), name='shiprocket-track'),
    path('shiprocket/invoice/', GenerateInvoiceView.as_view(), name='shiprocket-invoice'),
    
    # Include router URLs
    path('', include(router.urls)),
]
