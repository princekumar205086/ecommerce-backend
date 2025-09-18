# Admin approval views for supplier content
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Product, ProductCategory, Brand, ProductVariant


@api_view(['GET'])
@permission_classes([IsAdminUser])
def pending_approvals(request):
    """Get all content pending admin approval"""
    
    pending_brands = Brand.objects.filter(
        status='pending', 
        created_by__role='supplier'
    ).values(
        'id', 'name', 'created_by__username', 'created_at'
    )
    
    pending_categories = ProductCategory.objects.filter(
        status='pending', 
        created_by__role='supplier'
    ).values(
        'id', 'name', 'created_by__username', 'created_at'
    )
    
    pending_products = Product.objects.filter(
        status='pending', 
        created_by__role='supplier'
    ).values(
        'id', 'name', 'product_type', 'created_by__username', 'created_at'
    )
    
    pending_variants = ProductVariant.objects.filter(
        status='pending',
        product__created_by__role='supplier'
    ).select_related('product').values(
        'id', 'product__name', 'product__created_by__username', 'created_at'
    )
    
    return Response({
        'brands': list(pending_brands),
        'categories': list(pending_categories),
        'products': list(pending_products),
        'variants': list(pending_variants),
        'total_pending': len(pending_brands) + len(pending_categories) + len(pending_products) + len(pending_variants)
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def approve_brand(request, brand_id):
    """Approve a brand"""
    brand = get_object_or_404(Brand, id=brand_id)
    brand.approve(request.user)
    return Response({
        'message': f'Brand "{brand.name}" approved successfully',
        'brand_id': brand.id,
        'status': brand.status
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def reject_brand(request, brand_id):
    """Reject a brand"""
    brand = get_object_or_404(Brand, id=brand_id)
    reason = request.data.get('reason', '')
    brand.reject(request.user, reason)
    return Response({
        'message': f'Brand "{brand.name}" rejected',
        'brand_id': brand.id,
        'status': brand.status,
        'reason': reason
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def approve_category(request, category_id):
    """Approve a category"""
    category = get_object_or_404(ProductCategory, id=category_id)
    category.approve(request.user)
    return Response({
        'message': f'Category "{category.name}" approved successfully',
        'category_id': category.id,
        'status': category.status
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def reject_category(request, category_id):
    """Reject a category"""
    category = get_object_or_404(ProductCategory, id=category_id)
    reason = request.data.get('reason', '')
    category.reject(request.user, reason)
    return Response({
        'message': f'Category "{category.name}" rejected',
        'category_id': category.id,
        'status': category.status,
        'reason': reason
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def approve_product(request, product_id):
    """Approve a product"""
    product = get_object_or_404(Product, id=product_id)
    product.approve(request.user)
    return Response({
        'message': f'Product "{product.name}" approved successfully',
        'product_id': product.id,
        'status': product.status
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def reject_product(request, product_id):
    """Reject a product"""
    product = get_object_or_404(Product, id=product_id)
    reason = request.data.get('reason', '')
    product.reject(request.user, reason)
    return Response({
        'message': f'Product "{product.name}" rejected',
        'product_id': product.id,
        'status': product.status,
        'reason': reason
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def approve_variant(request, variant_id):
    """Approve a product variant"""
    variant = get_object_or_404(ProductVariant, id=variant_id)
    variant.approve(request.user)
    return Response({
        'message': f'Variant for "{variant.product.name}" approved successfully',
        'variant_id': variant.id,
        'status': variant.status
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def reject_variant(request, variant_id):
    """Reject a product variant"""
    variant = get_object_or_404(ProductVariant, id=variant_id)
    reason = request.data.get('reason', '')
    variant.reject(request.user, reason)
    return Response({
        'message': f'Variant for "{variant.product.name}" rejected',
        'variant_id': variant.id,
        'status': variant.status,
        'reason': reason
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def bulk_approve(request):
    """Bulk approve multiple items"""
    data = request.data
    results = {}
    
    # Approve brands
    if 'brand_ids' in data:
        brands = Brand.objects.filter(id__in=data['brand_ids'])
        for brand in brands:
            brand.approve(request.user)
        results['brands_approved'] = len(brands)
    
    # Approve categories
    if 'category_ids' in data:
        categories = ProductCategory.objects.filter(id__in=data['category_ids'])
        for category in categories:
            category.approve(request.user)
        results['categories_approved'] = len(categories)
    
    # Approve products
    if 'product_ids' in data:
        products = Product.objects.filter(id__in=data['product_ids'])
        for product in products:
            product.approve(request.user)
        results['products_approved'] = len(products)
    
    # Approve variants
    if 'variant_ids' in data:
        variants = ProductVariant.objects.filter(id__in=data['variant_ids'])
        for variant in variants:
            variant.approve(request.user)
        results['variants_approved'] = len(variants)
    
    return Response({
        'message': 'Bulk approval completed',
        'results': results
    })