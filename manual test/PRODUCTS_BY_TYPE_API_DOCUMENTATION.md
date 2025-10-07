# Products by Type API Endpoint Documentation

## 📚 Overview

This document describes the new **Products by Type** endpoint that allows filtering products by their type (medicine, equipment, pathology).

### 🎯 Endpoint Details

- **URL**: `/api/public/products/types/{product_type}/products/`
- **Method**: `GET`
- **Authentication**: Optional (supports MedixMall mode for authenticated users)
- **Pagination**: Yes (DRF standard pagination)

## 🔗 URL Patterns

### Valid Product Types
- `medicine` - Pharmaceutical products and medicines
- `equipment` - Medical equipment and devices  
- `pathology` - Laboratory and pathology products

### URL Examples
```
GET /api/public/products/types/medicine/products/
GET /api/public/products/types/equipment/products/
GET /api/public/products/types/pathology/products/
```

## 📋 Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `ordering` | string | Sort results by field | `price`, `-price`, `name`, `-name`, `created_at`, `-created_at` |
| `page` | integer | Page number for pagination | `1`, `2`, `3` |

### Ordering Options
- `price` - Sort by price (low to high)
- `-price` - Sort by price (high to low)
- `name` - Sort by name (A-Z)
- `-name` - Sort by name (Z-A)
- `created_at` - Sort by creation date (oldest first)
- `-created_at` - Sort by creation date (newest first)

## 📊 Response Format

### Successful Response (200 OK)
```json
{
  "count": 77,
  "next": "http://127.0.0.1:8000/api/public/products/types/medicine/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Multivitamin Tablets",
      "slug": "multivitamin-tablets",
      "sku": "MULTIVITAMIN-TABLETS-12345678",
      "brand": {
        "id": 5,
        "name": "Himalaya"
      },
      "category": {
        "id": 2,
        "name": "Prescription Medicines"
      },
      "description": "High-quality multivitamin tablets...",
      "image": "https://ik.imagekit.io/medixmallstore/products/multivitamin-tablets.jpg",
      "price": "430.67",
      "stock": 100,
      "product_type": "medicine",
      "is_publish": true,
      "status": "published",
      "created_at": "2025-09-12T10:30:00Z",
      "specifications": {},
      "tags": ["vitamins", "health", "supplements"]
    }
  ]
}
```

### Error Response (404 Not Found)
```json
{
  "detail": "Not found."
}
```

## 🧪 Testing Results

### Database Statistics
- **Medicine Products**: 77 products
- **Equipment Products**: 67 products  
- **Pathology Products**: 23 products
- **Total**: 167 products

### Test Results Summary
✅ **All product types working correctly**
- Medicine endpoint: Returns 77 products
- Equipment endpoint: Returns 67 products
- Pathology endpoint: Returns 23 products

✅ **Invalid type validation working**
- Returns 404 for invalid product types like 'invalid', 'food', 'electronics'

✅ **Ordering functionality working**
- Price sorting (ascending/descending)
- Name sorting (alphabetical)
- Date sorting (newest/oldest)

✅ **Pagination working**
- Standard DRF pagination (10 items per page by default)

## 🌐 cURL Command Examples

### Basic Usage
```bash
# Get all medicine products
curl -X GET 'http://127.0.0.1:8000/api/public/products/types/medicine/products/'

# Get all equipment products
curl -X GET 'http://127.0.0.1:8000/api/public/products/types/equipment/products/'

# Get all pathology products
curl -X GET 'http://127.0.0.1:8000/api/public/products/types/pathology/products/'
```

### With Ordering
```bash
# Medicine products by price (low to high)
curl -X GET 'http://127.0.0.1:8000/api/public/products/types/medicine/products/?ordering=price'

# Equipment products by price (high to low)
curl -X GET 'http://127.0.0.1:8000/api/public/products/types/equipment/products/?ordering=-price'

# Pathology products by name (A-Z)
curl -X GET 'http://127.0.0.1:8000/api/public/products/types/pathology/products/?ordering=name'
```

### With Pagination
```bash
# Get second page of medicine products
curl -X GET 'http://127.0.0.1:8000/api/public/products/types/medicine/products/?page=2'
```

## 🔧 JavaScript/Frontend Usage

### Using Fetch API
```javascript
// Get medicine products
async function getMedicineProducts() {
  try {
    const response = await fetch('/api/public/products/types/medicine/products/');
    const data = await response.json();
    console.log(`Found ${data.count} medicine products`);
    return data.results;
  } catch (error) {
    console.error('Error fetching medicine products:', error);
  }
}

// Get products with ordering
async function getProductsByType(type, ordering = '-created_at') {
  try {
    const url = `/api/public/products/types/${type}/products/?ordering=${ordering}`;
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error(`Error fetching ${type} products:`, error);
    return null;
  }
}

// Usage examples
getMedicineProducts();
getProductsByType('equipment', 'price');
getProductsByType('pathology', '-name');
```

### Using Axios
```javascript
import axios from 'axios';

// Get equipment products sorted by price
const getEquipmentProducts = async () => {
  try {
    const response = await axios.get('/api/public/products/types/equipment/products/', {
      params: {
        ordering: 'price'
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
};
```

## 🏥 MedixMall Mode Support

This endpoint respects the user's MedixMall mode preference:

- **Authenticated users** with `medixmall_mode=True` will only see medicine products regardless of the requested type
- **Anonymous users** or users with `medixmall_mode=False` will see all product types as requested
- **Response headers** include `X-MedixMall-Mode: true/false` to indicate the mode

## 🎛️ Integration with Frontend

### Product Category Pages
```javascript
// Create product type navigation
const productTypes = [
  { key: 'medicine', label: 'Medicines', icon: '💊' },
  { key: 'equipment', label: 'Equipment', icon: '🏥' },
  { key: 'pathology', label: 'Lab Tests', icon: '🧪' }
];

productTypes.forEach(type => {
  const url = `/api/public/products/types/${type.key}/products/`;
  // Create navigation links and fetch data
});
```

### Product Filters
```javascript
// Add product type filter to existing search
const applyFilters = (filters) => {
  let url = '/api/public/products/';
  
  if (filters.productType) {
    url = `/api/public/products/types/${filters.productType}/products/`;
  }
  
  const params = new URLSearchParams();
  if (filters.ordering) params.append('ordering', filters.ordering);
  if (filters.page) params.append('page', filters.page);
  
  return fetch(`${url}?${params}`);
};
```

## 🚨 Error Handling

### Common Error Scenarios

1. **Invalid Product Type (404)**
   ```json
   {
     "detail": "Not found."
   }
   ```

2. **Server Error (500)**
   ```json
   {
     "detail": "Internal server error."
   }
   ```

### Error Handling Best Practices
```javascript
const handleProductTypeRequest = async (productType) => {
  try {
    const response = await fetch(`/api/public/products/types/${productType}/products/`);
    
    if (response.status === 404) {
      console.error(`Invalid product type: ${productType}`);
      return { error: 'Invalid product type' };
    }
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Request failed:', error);
    return { error: error.message };
  }
};
```

## 📈 Performance Considerations

- **Database Optimization**: Uses proper indexes on `product_type` field
- **Query Optimization**: Includes `select_related` for category and brand
- **Caching**: Consider implementing Redis caching for frequently accessed product types
- **Pagination**: Default page size is 10, configurable via settings

## 🔄 Future Enhancements

1. **Advanced Filtering**: Add support for price range, brand filtering within product types
2. **Search Integration**: Combine with existing search functionality
3. **Analytics**: Track popular product types and usage patterns
4. **Caching**: Implement response caching for better performance

## ✅ Production Deployment

### Requirements Met
- ✅ Proper URL routing with validation
- ✅ MedixMall mode compatibility
- ✅ Swagger/OpenAPI documentation
- ✅ Error handling for invalid types
- ✅ Ordering and pagination support
- ✅ Comprehensive testing

### Ready for Production Use
This endpoint is fully tested and ready for production deployment. It follows the same patterns as existing public endpoints and maintains compatibility with the MedixMall ecosystem.

---

**Last Updated**: September 12, 2025  
**API Version**: v1  
**Status**: ✅ Production Ready
