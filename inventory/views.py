from rest_framework import generics, permissions
from rest_framework import filters
from rest_framework.exceptions import ValidationError
from django.db import transaction
import django_filters
from .models import Warehouse, Supplier, InventoryItem, InventoryTransaction
from .serializers import (
    WarehouseSerializer, SupplierSerializer,
    InventoryItemSerializer, InventoryTransactionSerializer
)
from ecommerce.permissions import IsSupplierOrAdmin

# views.py
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets
from .utils import export_inventory_pdf
from django.db import models

DEFAULT_LOW_STOCK_THRESHOLD = 10  # Extracted constant for readability

class WarehouseListCreateView(generics.ListCreateAPIView):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsSupplierOrAdmin]

class SupplierListCreateView(generics.ListCreateAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsSupplierOrAdmin]

class InventoryItemFilter(django_filters.FilterSet):
    is_low_stock = django_filters.BooleanFilter(method='filter_is_low_stock')

    class Meta:
        model = InventoryItem
        fields = ["supplier", "warehouse", "product"]  # do NOT include 'is_low_stock' here

    def filter_is_low_stock(self, queryset, name, value):
        if value:
            return queryset.filter(quantity__lte=models.F("low_stock_threshold"))
        else:
            return queryset.filter(quantity__gt=models.F("low_stock_threshold"))

# In your view:
from rest_framework import generics
from .serializers import InventoryItemSerializer

class InventoryItemListCreateView(generics.ListCreateAPIView):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = InventoryItemFilter

class InventoryItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = InventoryItem.objects.select_related('product', 'variant', 'warehouse', 'supplier')
    serializer_class = InventoryItemSerializer
    permission_classes = [IsSupplierOrAdmin]

class InventoryTransactionListCreateView(generics.ListCreateAPIView):
    queryset = InventoryTransaction.objects.select_related('inventory_item', 'performed_by')
    serializer_class = InventoryTransactionSerializer
    permission_classes = [IsSupplierOrAdmin]
    filterset_fields = ['txn_type', 'inventory_item', 'performed_by']

    def perform_create(self, serializer):
        with transaction.atomic():
            txn_type = serializer.validated_data['txn_type']
            inv_item = serializer.validated_data['inventory_item']
            qty = serializer.validated_data['quantity']
            if txn_type == InventoryTransaction.OUT:
                if inv_item.quantity < qty:
                    raise ValidationError({'detail': 'Insufficient stock for this transaction'})
                inv_item.quantity -= qty
            else:
                inv_item.quantity += qty
            inv_item.save()
            serializer.save(performed_by=self.request.user)

class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.select_related('product', 'variant', 'warehouse', 'supplier')
    serializer_class = InventoryItemSerializer
    permission_classes = [IsSupplierOrAdmin]
    filterset_fields = ['product', 'variant', 'warehouse', 'is_low_stock', 'supplier']
    ordering_fields = ['last_updated', 'quantity']
    ordering = ['-last_updated']
    search_fields = ['product__name', 'variant__name', 'warehouse__name', 'supplier__name']
    pagination_class = None  # Disable pagination for this viewset
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    def get_queryset(self):
        queryset = super().get_queryset()
        low_stock_param = self.request.query_params.get('low_stock', None)
        if low_stock_param is not None:
            # Convert query param to boolean and filter accordingly
            queryset = queryset.filter(is_low_stock=low_stock_param.lower() == 'true')
        return queryset

    def perform_create(self, serializer):
        with transaction.atomic():
            self._create_or_update_inventory_item(serializer)

    def _create_or_update_inventory_item(self, serializer):
        """
        Handles inventory item creation or quantity update if item already exists.
        """
        product = serializer.validated_data['product']
        variant = serializer.validated_data.get('variant')
        warehouse = serializer.validated_data['warehouse']
        quantity = serializer.validated_data['quantity']
        low_stock_threshold = serializer.validated_data.get('low_stock_threshold', DEFAULT_LOW_STOCK_THRESHOLD)
        try:
            inventory_item = InventoryItem.objects.get(product=product, variant=variant, warehouse=warehouse)
            inventory_item.quantity += quantity
            inventory_item.save()
        except InventoryItem.DoesNotExist:
            serializer.save(low_stock_threshold=low_stock_threshold)
    @action(detail=False, methods=['get'], permission_classes=[IsSupplierOrAdmin])
    def export_pdf(self, request):
        return export_inventory_pdf()