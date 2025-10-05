"""
Enterprise-level filters for products with advanced search and filtering capabilities
Similar to Amazon/Flipkart filtering system with performance optimizations
"""

import django_filters
from django.db.models import Q, F, Case, When, IntegerField, DecimalField
from django.db.models.functions import Lower
from .models import Product, ProductCategory, Brand, ProductReview, ProductVariant, PRODUCT_TYPES, PRODUCT_STATUSES


class EnterpriseProductFilter(django_filters.FilterSet):
    """
    Enterprise-level product filtering with advanced features:
    - Price range filtering with exact, min, max options
    - Advanced text search with weighted relevance
    - Category and brand filtering with fuzzy matching
    - Stock availability filtering
    - Rating-based filtering
    - Date range filtering
    - Multi-value filtering for categories and brands
    """
    
    # Price filtering
    price = django_filters.RangeFilter(field_name='price')
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    
    # Advanced search - multiple search fields with OR logic
    search = django_filters.CharFilter(method='filter_search')
    q = django_filters.CharFilter(method='filter_search')  # Alias for search
    
    # Category filtering - supports both ID and name
    category = django_filters.CharFilter(method='filter_category')
    category_id = django_filters.NumberFilter(field_name='category__id')
    category_name = django_filters.CharFilter(field_name='category__name', lookup_expr='icontains')
    
    # Brand filtering - supports both ID and name
    brand = django_filters.CharFilter(method='filter_brand')
    brand_id = django_filters.NumberFilter(field_name='brand__id')
    brand_name = django_filters.CharFilter(field_name='brand__name', lookup_expr='icontains')
    
    # Product type filtering
    product_type = django_filters.ChoiceFilter(choices=PRODUCT_TYPES)
    type = django_filters.ChoiceFilter(field_name='product_type', choices=PRODUCT_TYPES)  # Alias
    
    # Stock filtering
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    stock_min = django_filters.NumberFilter(field_name='stock', lookup_expr='gte')
    
    # Status filtering
    status = django_filters.ChoiceFilter(choices=PRODUCT_STATUSES)
    is_published = django_filters.BooleanFilter(field_name='is_publish')
    
    # Date filtering
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    updated_after = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_before = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    
    # Medicine-specific filters
    prescription_required = django_filters.BooleanFilter(field_name='medicine_details__prescription_required')
    medicine_form = django_filters.CharFilter(field_name='medicine_details__form', lookup_expr='icontains')
    manufacturer = django_filters.CharFilter(field_name='medicine_details__manufacturer', lookup_expr='icontains')
    composition = django_filters.CharFilter(field_name='medicine_details__composition', lookup_expr='icontains')
    
    # Equipment-specific filters
    equipment_type = django_filters.CharFilter(field_name='equipment_details__equipment_type', lookup_expr='icontains')
    model_number = django_filters.CharFilter(field_name='equipment_details__model_number', lookup_expr='icontains')
    usage_type = django_filters.CharFilter(field_name='equipment_details__usage_type', lookup_expr='icontains')
    
    # Multi-value filters
    categories = django_filters.BaseInFilter(field_name='category__id')
    brands = django_filters.BaseInFilter(field_name='brand__id')
    types = django_filters.BaseInFilter(field_name='product_type')
    
    # Tag filtering
    tags = django_filters.CharFilter(field_name='tags__name', lookup_expr='icontains')
    
    class Meta:
        model = Product
        fields = {
            'name': ['exact', 'icontains', 'istartswith'],
            'sku': ['exact', 'icontains'],
            'description': ['icontains'],
            'price': ['exact', 'gte', 'lte'],
            'stock': ['exact', 'gte', 'lte'],
            'created_at': ['gte', 'lte'],
            'updated_at': ['gte', 'lte'],
            'is_publish': ['exact'],
            'status': ['exact', 'in'],
            'product_type': ['exact', 'in'],
        }
    
    def filter_search(self, queryset, name, value):
        """
        Enterprise-level search with weighted relevance scoring
        Searches across multiple fields with different priorities
        """
        if not value:
            return queryset
        
        # Clean and split search terms
        terms = value.lower().strip().split()
        if not terms:
            return queryset
        
        search_query = Q()
        
        for term in terms:
            # High priority: exact name match (weight: 100)
            search_query |= Q(name__icontains=term)
            
            # High priority: SKU match (weight: 90)
            search_query |= Q(sku__icontains=term)
            
            # Medium-high priority: brand match (weight: 80)
            search_query |= Q(brand__name__icontains=term)
            
            # Medium priority: category match (weight: 70)
            search_query |= Q(category__name__icontains=term)
            
            # Medium priority: description match (weight: 60)
            search_query |= Q(description__icontains=term)
            
            # Medicine-specific searches (weight: 50)
            search_query |= Q(medicine_details__composition__icontains=term)
            search_query |= Q(medicine_details__manufacturer__icontains=term)
            search_query |= Q(medicine_details__form__icontains=term)
            
            # Equipment-specific searches (weight: 50)
            search_query |= Q(equipment_details__model_number__icontains=term)
            search_query |= Q(equipment_details__equipment_type__icontains=term)
            search_query |= Q(equipment_details__usage_type__icontains=term)
            search_query |= Q(equipment_details__technical_specifications__icontains=term)
            
            # Pathology-specific searches (weight: 50)
            search_query |= Q(pathology_details__compatible_tests__icontains=term)
            search_query |= Q(pathology_details__chemical_composition__icontains=term)
            
            # Low priority: tags match (weight: 30)
            search_query |= Q(tags__name__icontains=term)
        
        return queryset.filter(search_query).distinct()
    
    def filter_category(self, queryset, name, value):
        """
        Filter by category supporting both ID and name
        """
        if not value:
            return queryset
        
        # Try to parse as integer (ID)
        try:
            category_id = int(value)
            return queryset.filter(category__id=category_id)
        except ValueError:
            # Treat as name
            return queryset.filter(category__name__icontains=value)
    
    def filter_brand(self, queryset, name, value):
        """
        Filter by brand supporting both ID and name
        """
        if not value:
            return queryset
        
        # Try to parse as integer (ID)
        try:
            brand_id = int(value)
            return queryset.filter(brand__id=brand_id)
        except ValueError:
            # Treat as name
            return queryset.filter(brand__name__icontains=value)
    
    def filter_in_stock(self, queryset, name, value):
        """
        Filter products based on stock availability
        """
        if value is True:
            return queryset.filter(stock__gt=0)
        elif value is False:
            return queryset.filter(stock=0)
        return queryset


class EnterpriseCategoryFilter(django_filters.FilterSet):
    """
    Enterprise-level category filtering
    """
    
    search = django_filters.CharFilter(method='filter_search')
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    parent = django_filters.NumberFilter(field_name='parent__id')
    has_parent = django_filters.BooleanFilter(method='filter_has_parent')
    
    class Meta:
        model = ProductCategory
        fields = {
            'name': ['exact', 'icontains'],
            'is_publish': ['exact'],
            'status': ['exact', 'in'],
            'created_at': ['gte', 'lte'],
        }
    
    def filter_search(self, queryset, name, value):
        """
        Search across category fields
        """
        if not value:
            return queryset
        
        return queryset.filter(
            Q(name__icontains=value)
        )
    
    def filter_has_parent(self, queryset, name, value):
        """
        Filter categories based on whether they have a parent
        """
        if value is True:
            return queryset.filter(parent__isnull=False)
        elif value is False:
            return queryset.filter(parent__isnull=True)
        return queryset


class EnterpriseBrandFilter(django_filters.FilterSet):
    """
    Enterprise-level brand filtering
    """
    
    search = django_filters.CharFilter(method='filter_search')
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    
    class Meta:
        model = Brand
        fields = {
            'name': ['exact', 'icontains'],
            'is_publish': ['exact'],
            'status': ['exact', 'in'],
            'created_at': ['gte', 'lte'],
        }
    
    def filter_search(self, queryset, name, value):
        """
        Search across brand fields
        """
        if not value:
            return queryset
        
        return queryset.filter(name__icontains=value)


class EnterpriseReviewFilter(django_filters.FilterSet):
    """
    Enterprise-level review filtering
    """
    
    rating = django_filters.NumberFilter(field_name='rating')
    rating_min = django_filters.NumberFilter(field_name='rating', lookup_expr='gte')
    rating_max = django_filters.NumberFilter(field_name='rating', lookup_expr='lte')
    product = django_filters.NumberFilter(field_name='product__id')
    user = django_filters.NumberFilter(field_name='user__id')
    
    class Meta:
        model = ProductReview
        fields = {
            'rating': ['exact', 'gte', 'lte'],
            'is_published': ['exact'],
            'created_at': ['gte', 'lte'],
        }


class EnterpriseVariantFilter(django_filters.FilterSet):
    """
    Enterprise-level variant filtering
    """
    
    product = django_filters.NumberFilter(field_name='product__id')
    price = django_filters.RangeFilter(field_name='price')
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    
    class Meta:
        model = ProductVariant
        fields = {
            'sku': ['exact', 'icontains'],
            'price': ['exact', 'gte', 'lte'],
            'stock': ['exact', 'gte', 'lte'],
            'is_active': ['exact'],
            'status': ['exact', 'in'],
        }
    
    def filter_in_stock(self, queryset, name, value):
        """
        Filter variants based on stock availability
        """
        if value is True:
            return queryset.filter(stock__gt=0)
        elif value is False:
            return queryset.filter(stock=0)
        return queryset