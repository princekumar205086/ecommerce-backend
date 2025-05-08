from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from products.models import Product, Brand, ProductCategory, ProductSubCategory
from .models import Warehouse, Supplier, InventoryItem, InventoryTransaction

class InventoryAPITest(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email='admin@test.com', password='admin123', role='admin', full_name="Admin User")
        self.supplier = User.objects.create_user(email='supplier@test.com', password='supp123', role='supplier', full_name="Supp User")
        self.category = ProductCategory.objects.create(name="Chemical", slug="chemical", created_by=self.admin)
        self.brand = Brand.objects.create(name="Generic", created_by=self.admin)
        self.product = Product.objects.create(
            name="Test Reagent", price=20, category=self.category,
            brand=self.brand, created_by=self.admin, type='pathology'
        )
        self.warehouse = Warehouse.objects.create(name="Main Warehouse")
        self.supplier_obj = Supplier.objects.create(name="ABC Suppliers")
        self.item = InventoryItem.objects.create(
            product=self.product, warehouse=self.warehouse, quantity=100, supplier=self.supplier_obj
        )

    def authenticate(self, user):
        self.client.force_authenticate(user)

    def test_create_warehouse(self):
        self.authenticate(self.supplier)
        response = self.client.post(reverse('warehouse-list-create'), {'name': 'Secondary', 'location': 'Delhi'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Warehouse.objects.count(), 2)

    def test_list_warehouses(self):
        self.authenticate(self.supplier)
        response = self.client.get(reverse('warehouse-list-create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Main Warehouse', str(response.data))

    def test_create_inventory_item(self):
        self.authenticate(self.supplier)
        response = self.client.post(reverse('inventoryitem-list-create'), {
            "product": self.product.id,
            "warehouse": self.warehouse.id,
            "quantity": 50,
            "supplier": self.supplier_obj.id
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_prevent_negative_stock_on_out_transaction(self):
        self.authenticate(self.admin)
        txndata = {
            'inventory_item': self.item.id,
            'txn_type': 'OUT',
            'quantity': 200,  # more than available
            'notes': 'Test negative'
        }
        response = self.client.post(reverse('inventorytransaction-list-create'), txndata)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient stock', response.data['detail'])

    def test_stock_in_and_out_transaction_success(self):
        self.authenticate(self.supplier)
        # OUT
        response = self.client.post(reverse('inventorytransaction-list-create'), {
            'inventory_item': self.item.id,
            'txn_type': 'OUT',
            'quantity': 10,
            'notes': 'Sample out'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 90)
        # IN
        response = self.client.post(reverse('inventorytransaction-list-create'), {
            'inventory_item': self.item.id,
            'txn_type': 'IN',
            'quantity': 50,
            'notes': 'Restock'
        })
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 140)

    def test_update_inventory_item(self):
        self.authenticate(self.admin)
        url = reverse('inventoryitem-detail', args=[self.item.id])
        response = self.client.patch(url, {'quantity': 200})
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 200)

    def test_filter_inventory_items_by_supplier(self):
        self.authenticate(self.admin)
        response = self.client.get(reverse('inventoryitem-list-create'), {
            'supplier': self.supplier_obj.id
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_permission_denied_for_unauthenticated(self):
        self.client.logout()
        response = self.client.get(reverse('warehouse-list-create'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)