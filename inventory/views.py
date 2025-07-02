# inventory/views.py

from rest_framework import generics, permissions, filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db import transaction, models
import django_filters.rest_framework as django_filters

from .models import Warehouse, Supplier, InventoryItem, InventoryTransaction
from .serializers import (
    WarehouseSerializer,
    SupplierSerializer,
    InventoryItemSerializer,
    InventoryTransactionSerializer,
)
from .utils import export_inventory_pdf
from ecommerce.permissions import IsSupplierOrAdmin

DEFAULT_LOW_STOCK_THRESHOLD = 10


# ----------------------------
# Warehouse Views
# ----------------------------
class WarehouseListCreateView(generics.ListCreateAPIView):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsSupplierOrAdmin]


# ----------------------------
# Supplier Views
# ----------------------------
class SupplierListCreateView(generics.ListCreateAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsSupplierOrAdmin]


# ----------------------------
# Inventory Filter
# ----------------------------
class InventoryItemFilter(django_filters.FilterSet):
    is_low_stock = django_filters.BooleanFilter(method='filter_low_stock')

    class Meta:
        model = InventoryItem
        fields = ['product', 'variant', 'warehouse', 'supplier']

    def filter_low_stock(self, queryset, name, value):
        return queryset.filter(quantity__lte=models.F("low_stock_threshold") if value else models.F("low_stock_threshold") + 1)


# ----------------------------
# Inventory Item Views
# ----------------------------
class InventoryItemListCreateView(generics.ListCreateAPIView):
    queryset = InventoryItem.objects.select_related('product', 'variant', 'warehouse', 'supplier')
    serializer_class = InventoryItemSerializer
    filter_backends = [django_filters.DjangoFilterBackend]
    filterset_class = InventoryItemFilter
    permission_classes = [IsSupplierOrAdmin]


class InventoryItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = InventoryItem.objects.select_related('product', 'variant', 'warehouse', 'supplier')
    serializer_class = InventoryItemSerializer
    permission_classes = [IsSupplierOrAdmin]


# ----------------------------
# Inventory ViewSet (With Search + Export)
# ----------------------------
class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.select_related('product', 'variant', 'warehouse', 'supplier')
    serializer_class = InventoryItemSerializer
    permission_classes = [IsSupplierOrAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, django_filters.DjangoFilterBackend]
    filterset_class = InventoryItemFilter
    search_fields = ['product__name', 'variant__size', 'variant__weight', 'warehouse__name', 'supplier__name']
    ordering_fields = ['last_updated', 'quantity']
    ordering = ['-last_updated']

    def perform_create(self, serializer):
        self._create_or_update(serializer)

    def _create_or_update(self, serializer):
        data = serializer.validated_data
        product = data['product']
        variant = data.get('variant')
        warehouse = data['warehouse']
        quantity = data['quantity']
        low_stock_threshold = data.get('low_stock_threshold', DEFAULT_LOW_STOCK_THRESHOLD)

        with transaction.atomic():
            item, created = InventoryItem.objects.select_for_update().get_or_create(
                product=product, variant=variant, warehouse=warehouse,
                defaults={
                    'quantity': quantity,
                    'low_stock_threshold': low_stock_threshold,
                    'supplier': data.get('supplier'),
                    'batch_number': data.get('batch_number', ''),
                    'expiry_date': data.get('expiry_date')
                }
            )
            if not created:
                item.quantity += quantity
                item.save()

            if created:
                serializer.save()
            else:
                serializer.instance = item  # Assign for consistency

    @action(detail=False, methods=['get'], permission_classes=[IsSupplierOrAdmin])
    def export_pdf(self, request):
        return export_inventory_pdf()


# ----------------------------
# Inventory Transaction Views
# ----------------------------
class InventoryTransactionListCreateView(generics.ListCreateAPIView):
    queryset = InventoryTransaction.objects.select_related('inventory_item', 'performed_by')
    serializer_class = InventoryTransactionSerializer
    permission_classes = [IsSupplierOrAdmin]
    filterset_fields = ['txn_type', 'inventory_item', 'performed_by']

    def perform_create(self, serializer):
        with transaction.atomic():
            inv_item = serializer.validated_data['inventory_item']
            txn_type = serializer.validated_data['txn_type']
            qty = serializer.validated_data['quantity']

            if txn_type == InventoryTransaction.OUT and inv_item.quantity < qty:
                raise ValidationError({'detail': 'Insufficient stock for this transaction'})

            serializer.save(performed_by=self.request.user)
            serializer.instance.apply_transaction()
