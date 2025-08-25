
# Cart API Endpoints Documentation

## ✅ Status: TESTED & VERIFIED
All endpoints have been thoroughly tested and are working correctly.

## Authentication Required
All cart endpoints require authentication with JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Permission Requirements
- **Allowed Roles**: `user`, `supplier`
- **Blocked Roles**: `admin` (Admins cannot have shopping carts)
- **Unauthenticated**: Blocked with 401 status

## Integration with Checkout Flow
This cart system integrates seamlessly with the order and payment systems:
- Cart → Order Creation → Payment → Order Fulfillment
- Cart is automatically cleared after successful order creation
- Stock validation occurs during all cart operations

---

## 1. GET /api/cart/
**Description**: Retrieve current user's cart with all items
**Permissions**: User, Supplier only
**Method**: GET

### Request Headers:
```json
{
    "Authorization": "Bearer <jwt_token>"
}
```

### Response (200 OK):
```json
{
    "id": 3,
    "user": 2,
    "items": [
        {
            "id": 15,
            "product": {
                "id": 46,
                "name": "Fixed Image Test Pathology",
                "price": "299.99",
                "image": "/media/product_images/test_image.jpg"
            },
            "variant": {
                "id": 1,
                "size": "10mg",
                "additional_price": "50.00"
            },
            "quantity": 2,
            "total_price": 599.98
        }
    ],
    "total_items": 6,
    "total_price": 2899.94,
    "created_at": "2025-08-25T10:30:00Z",
    "updated_at": "2025-08-25T10:35:00Z"
}
```

### Error Responses:
- **401**: Unauthorized (no token or invalid token)
- **403**: Forbidden (admin trying to access cart)

---

## 2. POST /api/cart/add/
**Description**: Add a product to cart
**Permissions**: User, Supplier only
**Method**: POST

### Request Headers:
```json
{
    "Authorization": "Bearer <jwt_token>",
    "Content-Type": "application/json"
}
```

### Request Body:
```json
{
    "product_id": 46,
    "variant_id": 2,  // Optional
    "quantity": 3
}
```

### Response (201 Created):
```json
{
    "message": "Item added to cart"
}
```

### Response (200 OK) - If item already exists:
```json
{
    "message": "Item added to cart"
}
```

### Error Responses:
- **400**: Bad Request (invalid data, insufficient stock)
- **401**: Unauthorized
- **403**: Forbidden (admin access)
- **404**: Product or variant not found

---

## 3. PUT /api/cart/items/<item_id>/update/
**Description**: Update quantity of a cart item
**Permissions**: User, Supplier only (own items only)
**Method**: PUT

### Request Headers:
```json
{
    "Authorization": "Bearer <jwt_token>",
    "Content-Type": "application/json"
}
```

### Request Body:
```json
{
    "quantity": 5
}
```

### Response (200 OK):
```json
{
    "quantity": 5
}
```

### Error Responses:
- **400**: Bad Request (invalid quantity, insufficient stock)
- **401**: Unauthorized
- **403**: Forbidden
- **404**: Cart item not found

---

## 4. DELETE /api/cart/items/<item_id>/remove/
**Description**: Remove a specific item from cart
**Permissions**: User, Supplier only (own items only)
**Method**: DELETE

### Request Headers:
```json
{
    "Authorization": "Bearer <jwt_token>"
}
```

### Response (204 No Content):
No response body

### Error Responses:
- **401**: Unauthorized
- **403**: Forbidden
- **404**: Cart item not found

---

## 5. DELETE /api/cart/clear/
**Description**: Remove all items from cart
**Permissions**: User, Supplier only
**Method**: DELETE

### Request Headers:
```json
{
    "Authorization": "Bearer <jwt_token>"
}
```

### Response (204 No Content):
No response body

### Error Responses:
- **401**: Unauthorized
- **403**: Forbidden (admin access)

---

## Error Response Format:
```json
{
    "error": "Error message description",
    "detail": "Additional error details"
}
```

## Notes:
1. **Stock Validation**: All cart operations validate product/variant stock availability
2. **User Isolation**: Users can only access their own cart items
3. **Admin Restriction**: Admins cannot access cart endpoints as they don't shop
4. **Automatic Cart Creation**: Carts are created automatically when first accessed
5. **Variant Support**: Products can be added with or without variants
6. **Quantity Limits**: Minimum quantity is 1, maximum is stock availability
7. **Integration**: Cart seamlessly integrates with order creation flow
8. **Auto-Clear**: Cart is automatically cleared after successful order creation

## Testing Status
✅ All endpoints tested and verified working correctly
✅ Integration with checkout flow confirmed
✅ Stock validation working properly
✅ User isolation and permissions enforced

## Related Documentation
- See `COMPLETE_CHECKOUT_API_DOCUMENTATION.md` for full checkout flow
- Use `comprehensive_checkout_test.py` to test all functionality
