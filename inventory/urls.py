from django.urls import path
from . import views

urlpatterns = [
    path('warehouses/', views.WarehouseListCreateView.as_view(), name='warehouse-list-create'),
    path('suppliers/', views.SupplierListCreateView.as_view(), name='supplier-list-create'),
    path('inventory-items/', views.InventoryItemListCreateView.as_view(), name='inventoryitem-list-create'),
    path('inventory-items/<int:pk>/', views.InventoryItemDetailView.as_view(), name='inventoryitem-detail'),
    path('transactions/', views.InventoryTransactionListCreateView.as_view(), name='inventorytransaction-list-create'),
]