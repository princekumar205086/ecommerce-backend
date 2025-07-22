# inventory/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WarehouseListCreateView,
    SupplierListCreateView,
    InventoryItemListCreateView,
    InventoryItemDetailView,
    InventoryTransactionListCreateView,
    InventoryItemViewSet,
)
from .offline_views import (
    CreateOfflineSaleView,
    OfflineSaleListView,
    OfflineSaleDetailView,
    CancelOfflineSaleView,
    VendorInventoryView,
    OfflineSalesReportView,
    real_time_stock_check,
    vendor_dashboard_stats,
)

# Use DRF router for InventoryItemViewSet
router = DefaultRouter()
router.register(r'inventory-view', InventoryItemViewSet, basename='inventory-view')

urlpatterns = [
    # Warehouse & Supplier
    path('warehouses/', WarehouseListCreateView.as_view(), name='warehouse-list-create'),
    path('suppliers/', SupplierListCreateView.as_view(), name='supplier-list-create'),

    # Inventory Items (Basic CRUD)
    path('inventory-items/', InventoryItemListCreateView.as_view(), name='inventoryitem-list-create'),
    path('inventory-items/<int:pk>/', InventoryItemDetailView.as_view(), name='inventoryitem-detail'),

    # Inventory Transactions (Stock IN/OUT logs)
    path('transactions/', InventoryTransactionListCreateView.as_view(), name='inventorytransaction-list-create'),

    # Offline Sales Management
    path('offline-sales/create/', CreateOfflineSaleView.as_view(), name='offline-sale-create'),
    path('offline-sales/', OfflineSaleListView.as_view(), name='offline-sale-list'),
    path('offline-sales/<int:pk>/', OfflineSaleDetailView.as_view(), name='offline-sale-detail'),
    path('offline-sales/<int:sale_id>/cancel/', CancelOfflineSaleView.as_view(), name='offline-sale-cancel'),
    
    # Vendor-specific endpoints
    path('vendor/inventory/', VendorInventoryView.as_view(), name='vendor-inventory'),
    path('vendor/dashboard/', vendor_dashboard_stats, name='vendor-dashboard'),
    
    # Real-time stock management
    path('stock/check/', real_time_stock_check, name='stock-check'),
    
    # Reports
    path('reports/offline-sales/', OfflineSalesReportView.as_view(), name='offline-sales-report'),

    # ViewSet-based with export PDF and filters
    path('', include(router.urls)),
]
