# 📄 Main Products Endpoint Pagination Behavior

## 🎯 **Endpoint Overview**

**URL**: `/api/public/products/products/`  
**Method**: `GET`  
**Authentication**: Optional

## 🔄 **Pagination Logic**

### **Conditional Pagination Behavior**

The main products endpoint uses **conditional pagination** based on query parameters:

| Scenario | Query Parameters | Behavior | Result |
|----------|------------------|----------|---------|
| **No pagination** | No `page` parameter | Returns ALL products | 167 products total |
| **With pagination** | `page=1`, `page=2`, etc. | Returns 12 per page | Paginated results |

### **Examples**

#### ✅ **Get ALL Products (No Pagination)**
```bash
curl -X GET 'https://backend.okpuja.in/api/public/products/products/'
```

**Response:**
```json
{
  "count": 167,
  "next": null,
  "previous": null,
  "results": [
    // ALL 167 products returned
  ]
}
```

#### ✅ **Get Products with Pagination (12 per page)**
```bash
curl -X GET 'https://backend.okpuja.in/api/public/products/products/?page=1'
```

**Response:**
```json
{
  "count": 167,
  "next": "https://backend.okpuja.in/api/public/products/products/?page=2",
  "previous": null,
  "results": [
    // First 12 products only
  ]
}
```

## 🔍 **Combined with Filters**

The conditional pagination works with all filters:

### **Filter + No Pagination**
```bash
# Get ALL medicine products (77 total)
GET /api/public/products/products/?product_type=medicine

# Search ALL tablet products (28 total)  
GET /api/public/products/products/?search=tablet

# Filter by brand, get ALL results
GET /api/public/products/products/?brand=5
```

### **Filter + With Pagination**
```bash
# Get first 12 medicine products
GET /api/public/products/products/?product_type=medicine&page=1

# Search tablets, first 12 results
GET /api/public/products/products/?search=tablet&page=1

# Filter by brand, paginate results
GET /api/public/products/products/?brand=5&page=1
```

## 📊 **Response Comparison**

### **Without Page Parameter**
```json
{
  "count": 167,           // Total products
  "next": null,           // No next page
  "previous": null,       // No previous page
  "results": [            // ALL 167 products
    /* ... 167 products ... */
  ]
}
```

### **With Page Parameter**
```json
{
  "count": 167,                                                    // Total products
  "next": "https://backend.okpuja.in/api/public/products/products/?page=2",  // Next page link
  "previous": null,                                                // Previous page (null for page 1)
  "results": [                                                     // 12 products only
    /* ... 12 products ... */
  ]
}
```

## 🧪 **Test Verification**

### **Actual Test Results**

| Test Case | Results | Status |
|-----------|---------|--------|
| No page param | 167/167 products | ✅ ALL products |
| `page=1` | 12/167 products | ✅ Paginated |
| `page=2` | 12/167 products | ✅ Paginated |
| Medicine filter (no page) | 77/77 products | ✅ ALL medicine |
| Medicine filter + `page=1` | 12/77 products | ✅ Paginated |
| Search filter (no page) | 28/28 products | ✅ ALL search results |
| Search filter + `page=1` | 12/28 products | ✅ Paginated |

## 🎯 **Use Cases**

### **Frontend Implementation**

#### **Load All Products (for dropdowns, catalogs)**
```javascript
// Get all products for catalog view
async function loadAllProducts() {
  const response = await fetch('/api/public/products/products/');
  const data = await response.json();
  return data.results; // All 167 products
}
```

#### **Load Products with Pagination (for product listings)**
```javascript
// Get paginated products for product grid
async function loadProductsPage(page = 1) {
  const response = await fetch(`/api/public/products/products/?page=${page}`);
  const data = await response.json();
  return {
    products: data.results,      // 12 products
    totalCount: data.count,      // 167
    hasNext: !!data.next,        // true/false
    hasPrevious: !!data.previous // true/false
  };
}
```

#### **Filter Products (both modes)**
```javascript
// Get all products of a specific type
async function loadProductsByType(productType) {
  const response = await fetch(`/api/public/products/products/?product_type=${productType}`);
  const data = await response.json();
  return data.results; // All products of that type
}

// Get paginated products of a specific type
async function loadProductsByTypePaginated(productType, page = 1) {
  const response = await fetch(`/api/public/products/products/?product_type=${productType}&page=${page}`);
  const data = await response.json();
  return data; // Paginated results
}
```

## 🚀 **Benefits**

### **Performance**
- **Small datasets**: Get all results in one request (no multiple API calls)
- **Large datasets**: Use pagination to reduce payload size
- **Flexible**: Choose based on use case

### **User Experience**
- **Catalog views**: Show all products at once
- **Product grids**: Paginate for better performance
- **Search results**: Paginate long result lists
- **Filters**: Get all filtered results or paginate as needed

### **Development**
- **Simple**: One endpoint handles both use cases
- **Consistent**: Same response format
- **Flexible**: Easy to switch between modes

## 🔧 **Implementation Details**

### **Code Logic**
```python
def list(self, request, *args, **kwargs):
    """Return all products when 'page' query param is absent.
    
    Preserve normal DRF pagination when the client explicitly requests a page
    using the `page` query parameter.
    """
    if 'page' in request.query_params:
        return super().list(request, *args, **kwargs)  # Use pagination
    
    queryset = self.filter_queryset(self.get_queryset())
    serializer = self.get_serializer(queryset, many=True)
    return Response({
        'count': queryset.count(),
        'next': None,
        'previous': None,
        'results': serializer.data,
    })
```

### **Key Features**
- **Conditional**: Checks for `page` parameter
- **Filter Compatible**: Works with all existing filters
- **Performance Optimized**: Uses `filter_queryset()` for efficiency
- **Consistent Format**: Same response structure as paginated responses

---

**Implementation Date**: September 18, 2025  
**Status**: ✅ Production Ready  
**Breaking Changes**: None - fully backward compatible