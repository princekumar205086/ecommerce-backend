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

    # ViewSet-based with export PDF and filters
    path('', include(router.urls)),
]
