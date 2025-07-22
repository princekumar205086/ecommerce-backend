# Real-time Stock Management for Online & Offline Sales

## Overview

This implementation provides a comprehensive real-time stock management system that synchronizes inventory between online orders and offline vendor sales. The system ensures that when a vendor makes a sale in their physical store, the inventory is immediately updated across all channels.

## Key Features

### ✅ **Real-time Stock Updates**
- Immediate inventory deduction for both online and offline sales
- Atomic transactions to prevent race conditions
- Centralized stock management through `RealTimeStockManager`

### ✅ **Offline Sales Management**
- Complete POS system for vendors to record in-store sales
- Multi-warehouse support
- Customer information capture
- Multiple payment methods support

### ✅ **Vendor-specific Features**
- Vendor dashboard with real-time statistics
- Inventory access restricted to relevant warehouses
- Sales reporting and analytics

### ✅ **Stock Synchronization**
- Automatic sync between `InventoryItem` and `Product.stock` fields
- Low stock alerts and notifications
- Batch processing for bulk operations

## API Endpoints

### Offline Sales Management

#### 1. Create Offline Sale
```http
POST /api/inventory/offline-sales/create/
Authorization: Bearer <token>
Content-Type: application/json

{
    "warehouse": 1,
    "customer_name": "John Doe",
    "customer_phone": "9876543210",
    "customer_email": "john@example.com",
    "payment_method": "cash",
    "payment_reference": "",
    "discount_amount": 0,
    "notes": "Walk-in customer",
    "items": [
        {
            "product_id": 1,
            "variant_id": null,
            "quantity": 2,
            "unit_price": 25.00,
            "discount_per_item": 0,
            "batch_number": "BATCH001",
            "expiry_date": "2025-12-31"
        },
        {
            "product_id": 2,
            "quantity": 1,
            "unit_price": 350.00
        }
    ]
}
```

**Response:**
```json
{
    "id": 1,
    "sale_number": "OS2501221234567",
    "vendor": 2,
    "vendor_name": "John Vendor",
    "warehouse": 1,
    "warehouse_name": "Main Store",
    "customer_name": "John Doe",
    "customer_phone": "9876543210",
    "customer_email": "john@example.com",
    "subtotal": "400.00",
    "tax_amount": "40.00",
    "discount_amount": "0.00",
    "total_amount": "440.00",
    "payment_method": "cash",
    "payment_reference": "",
    "notes": "Walk-in customer",
    "sale_date": "2025-01-22T10:30:00Z",
    "created_at": "2025-01-22T10:30:00Z",
    "is_cancelled": false,
    "cancelled_reason": "",
    "items": [
        {
            "id": 1,
            "product": 1,
            "product_name": "Paracetamol 500mg",
            "variant": null,
            "variant_details": null,
            "quantity": 2,
            "unit_price": "25.00",
            "discount_per_item": "0.00",
            "total_price": "50.00",
            "batch_number": "BATCH001",
            "expiry_date": "2025-12-31"
        }
    ]
}
```

#### 2. List Offline Sales
```http
GET /api/inventory/offline-sales/
Authorization: Bearer <token>

# Query parameters:
# - warehouse: Filter by warehouse ID
# - payment_method: Filter by payment method
# - is_cancelled: Filter cancelled sales
# - search: Search by sale number, customer name, phone
# - ordering: Sort by created_at, total_amount, sale_date
```

#### 3. Get Sale Details
```http
GET /api/inventory/offline-sales/{id}/
Authorization: Bearer <token>
```

#### 4. Cancel Sale
```http
POST /api/inventory/offline-sales/{id}/cancel/
Authorization: Bearer <token>
Content-Type: application/json

{
    "reason": "Customer requested refund"
}
```

### Vendor Management

#### 5. Vendor Inventory View
```http
GET /api/inventory/vendor/inventory/
Authorization: Bearer <token>
```

**Response:**
```json
[
    {
        "product_id": 1,
        "product_name": "Paracetamol 500mg",
        "variant_id": null,
        "variant_details": null,
        "quantity": 98,
        "low_stock_threshold": 10,
        "is_low_stock": false,
        "batch_number": "BATCH001",
        "expiry_date": "2025-12-31",
        "warehouse_name": "Main Store"
    }
]
```

#### 6. Vendor Dashboard Stats
```http
GET /api/inventory/vendor/dashboard/
Authorization: Bearer <token>
```

**Response:**
```json
{
    "today": {
        "sales_count": 5,
        "sales_amount": "2150.00"
    },
    "this_week": {
        "sales_count": 23,
        "sales_amount": "12750.00"
    },
    "low_stock_alerts": 3,
    "last_updated": "2025-01-22T10:30:00Z"
}
```

### Real-time Stock Management

#### 7. Real-time Stock Check
```http
GET /api/inventory/stock/check/
Authorization: Bearer <token>

# Query parameters:
# - product_id: Required
# - variant_id: Optional
# - warehouse_id: Required
```

**Response:**
```json
{
    "product_id": 1,
    "variant_id": null,
    "warehouse_id": 1,
    "current_stock": 98,
    "low_stock_threshold": 10,
    "is_low_stock": false,
    "last_updated": "2025-01-22T10:30:00Z"
}
```

### Reports

#### 8. Offline Sales Report
```http
POST /api/inventory/reports/offline-sales/
Authorization: Bearer <token>
Content-Type: application/json

{
    "date_from": "2025-01-01",
    "date_to": "2025-01-22",
    "warehouse": 1
}
```

**Response:**
```json
{
    "period": {
        "from": "2025-01-01",
        "to": "2025-01-22"
    },
    "summary": {
        "total_sales": "25000.00",
        "total_transactions": 150,
        "total_items_sold": 450,
        "average_transaction": "166.67"
    },
    "payment_breakdown": [
        {
            "payment_method": "cash",
            "count": 120,
            "amount": "20000.00"
        },
        {
            "payment_method": "card",
            "count": 30,
            "amount": "5000.00"
        }
    ],
    "top_products": [
        {
            "product__name": "Paracetamol 500mg",
            "total_quantity": 200,
            "total_revenue": "5000.00"
        }
    ],
    "daily_sales": [
        {
            "day": "2025-01-22",
            "count": 8,
            "amount": "1200.00"
        }
    ]
}
```

## Database Models

### OfflineSale
- `sale_number`: Unique sale identifier (auto-generated)
- `vendor`: Supplier user who made the sale
- `warehouse`: Warehouse where sale occurred
- `customer_name`, `customer_phone`, `customer_email`: Customer details
- `subtotal`, `tax_amount`, `discount_amount`, `total_amount`: Financial details
- `payment_method`, `payment_reference`: Payment information
- `sale_date`, `created_at`: Timestamps
- `is_cancelled`, `cancelled_reason`: Cancellation tracking

### OfflineSaleItem
- `sale`: Related offline sale
- `product`, `variant`: Product details
- `quantity`, `unit_price`, `discount_per_item`: Item details
- `batch_number`, `expiry_date`: Medicine tracking

## Real-time Stock Flow

### 1. Online Order Process
```
Customer adds to cart → Stock validation → Order creation → 
Inventory transaction (OUT) → Real-time stock update → 
Product.stock field sync
```

### 2. Offline Sale Process
```
Vendor creates sale → Stock validation → Sale creation →
Multiple inventory transactions (OUT) → Real-time stock update →
Product.stock field sync → Low stock alerts check
```

### 3. Stock Synchronization
```
InventoryTransaction created → Signal triggered →
sync_product_stock_field() → Product/Variant stock updated →
Low stock alerts generated
```

## Setup Instructions

1. **Run Migrations**
```bash
python manage.py migrate
```

2. **Create Sample Data**
```bash
python manage.py create_sample_data
```

3. **Sync Existing Stock**
```bash
python manage.py sync_stock --check-alerts
```

4. **Test the API**
Use the sample supplier credentials:
- Email: `supplier@test.com`
- Password: `testpass123`

## Usage Examples

### Creating an Offline Sale (Python)
```python
from inventory.offline_sales import OfflineSaleManager
from accounts.models import User
from inventory.models import Warehouse
from products.models import Product

# Get vendor and warehouse
vendor = User.objects.get(email='supplier@test.com')
warehouse = Warehouse.objects.get(name='Main Store')

# Prepare sale data
items_data = [
    {
        'product': Product.objects.get(name='Paracetamol 500mg'),
        'quantity': 2,
        'unit_price': Decimal('25.00')
    }
]

customer_data = {
    'name': 'Jane Doe',
    'phone': '9876543211'
}

payment_data = {
    'method': 'cash'
}

# Create sale
sale = OfflineSaleManager.create_offline_sale(
    vendor=vendor,
    warehouse=warehouse,
    items_data=items_data,
    customer_data=customer_data,
    payment_data=payment_data
)
```

### Real-time Stock Check (Python)
```python
from inventory.real_time_sync import RealTimeStockManager
from products.models import Product
from inventory.models import Warehouse

product = Product.objects.get(name='Paracetamol 500mg')
warehouse = Warehouse.objects.get(name='Main Store')

stock_info = RealTimeStockManager.get_real_time_stock(
    product=product,
    warehouse=warehouse
)
print(f"Current stock: {stock_info['current_stock']}")
```

## Security & Permissions

- **Suppliers**: Can only access their own sales and inventory
- **Admins**: Full access to all sales and inventory
- **Authentication**: Required for all endpoints
- **Stock Validation**: Prevents overselling
- **Transaction Safety**: All operations are atomic

## Monitoring & Alerts

- **Low Stock Alerts**: Automatic generation when stock drops below threshold
- **Logging**: All stock movements are logged
- **Audit Trail**: Complete transaction history
- **Real-time Updates**: Immediate stock synchronization

This system ensures that your inventory is always up-to-date regardless of whether sales happen online or offline, providing a seamless omnichannel experience for your medical ecommerce platform.
