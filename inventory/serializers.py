from rest_framework import serializers
from .models import Warehouse, Supplier, InventoryItem, InventoryTransaction


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = '__all__'
        read_only_fields = ['created_at']


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'
        read_only_fields = ['created_at']


class InventoryItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    variant_details = serializers.SerializerMethodField()
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = InventoryItem
        fields = (
            'id', 'product', 'product_name', 'variant', 'variant_details',
            'warehouse', 'warehouse_name', 'quantity', 'low_stock_threshold',
            'supplier', 'supplier_name', 'batch_number', 'hsn_code', 'expiry_date',
            'purchase_price', 'last_updated', 'is_low_stock'
        )
        read_only_fields = ('last_updated', 'product_name', 'warehouse_name', 'supplier_name', 'is_low_stock')

    def get_variant_details(self, obj):
        if obj.variant:
            return {
                'size': obj.variant.size,
                'weight': obj.variant.weight
            }
        return None


class InventoryTransactionSerializer(serializers.ModelSerializer):
    performed_by_user = serializers.StringRelatedField(source='performed_by', read_only=True)
    inventory_item_details = InventoryItemSerializer(source='inventory_item', read_only=True)
    source_type = serializers.SerializerMethodField()

    class Meta:
        model = InventoryTransaction
        fields = (
            'id', 'inventory_item', 'inventory_item_details', 'txn_type', 'quantity',
            'unit_cost', 'performed_by', 'performed_by_user',
            'timestamp', 'notes', 'source_type'
        )
        read_only_fields = ('performed_by', 'timestamp', 'source_type')

    def get_source_type(self, obj):
        if obj.source:
            return str(obj.source_content_type)
        return None
