# products/mixins.py
from django.db.models import Q


class MedixMallFilterMixin:
    """
    Mixin to filter products based on user's MedixMall mode preference
    When user has medixmall_mode=True (from profile or session), only show medicine products
    """
    
    def get_medixmall_mode(self, request):
        """Get MedixMall mode from user profile or session"""
        if hasattr(request, 'user') and request.user.is_authenticated:
            return getattr(request.user, 'medixmall_mode', False)
        else:
            return request.session.get('medixmall_mode', False)
    
    def get_queryset(self):
        # Define base queryset for Product model (lightweight for list views)
        from .models import Product
        queryset = Product.objects.filter(
            status='published',
            is_publish=True,
            stock__gt=0,
            created_by__is_on_duty=True  # Only show products from suppliers who are on duty
        ).select_related('category', 'brand', 'created_by')
        
        # Apply MedixMall filtering for both authenticated and anonymous users
        if self.get_medixmall_mode(self.request):
            # Filter to show only medicine products
            queryset = queryset.filter(product_type='medicine')
        
        return queryset


class MedixMallDetailMixin:
    """
    Mixin for MedixMall filtering and mode detection with heavy prefetching for detail views
    """
    
    def get_medixmall_mode(self, request):
        """
        Determine if user is in MedixMall mode
        """
        # For authenticated users, check database settings
        if request.user.is_authenticated:
            try:
                from accounts.models import UserProfile
                user_profile = UserProfile.objects.get(user=request.user)
                return user_profile.medixmall_mode
            except:
                return False
        else:
            return request.session.get('medixmall_mode', False)
    
    def get_queryset(self):
        # Define base queryset for Product model (with heavy prefetching for detail views)
        from .models import Product
        queryset = Product.objects.filter(
            status='published',
            is_publish=True,
            stock__gt=0,
            created_by__is_on_duty=True  # Only show products from suppliers who are on duty
        ).prefetch_related(
            'variants__attributes__attribute',
            'images', 
            'reviews'
        ).select_related('category', 'brand', 'created_by')
        
        # Apply MedixMall filtering for both authenticated and anonymous users
        if self.get_medixmall_mode(self.request):
            # Filter to show only medicine products
            queryset = queryset.filter(product_type='medicine')
        
        return queryset


class MedixMallContextMixin:
    """
    Mixin to add MedixMall mode context to response data
    """
    
    def get_medixmall_mode(self, request):
        """Get MedixMall mode from user profile or session"""
        if hasattr(request, 'user') and request.user.is_authenticated:
            return getattr(request.user, 'medixmall_mode', False)
        else:
            return request.session.get('medixmall_mode', False)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['medixmall_mode'] = self.get_medixmall_mode(self.request)
        return context
    
    def finalize_response(self, request, response, *args, **kwargs):
        """Add MedixMall mode info to response headers"""
        response = super().finalize_response(request, response, *args, **kwargs)
        
        medixmall_mode = self.get_medixmall_mode(request)
        response['X-MedixMall-Mode'] = 'true' if medixmall_mode else 'false'
        
        return response


class EnterpriseSearchMixin:
    """
    Enterprise-level search functionality with advanced features
    Similar to Amazon/Flipkart search capabilities
    """
    
    def apply_enterprise_search(self, queryset, search_query):
        """
        Apply enterprise-level search with:
        - Weighted scoring
        - Fuzzy matching
        - Category matching
        - Brand matching
        - Description matching
        - Tags matching
        """
        if not search_query:
            return queryset
        
        # Import Product model locally
        from .models import Product
        
        # Split search query into terms
        terms = search_query.lower().split()
        
        # Build search conditions with weights
        search_conditions = Q()
        
        for term in terms:
            # High priority: exact name match
            search_conditions |= Q(name__icontains=term)
            
            # Medium priority: brand match
            search_conditions |= Q(brand__name__icontains=term)
            
            # Medium priority: category match
            search_conditions |= Q(category__name__icontains=term)
            
            # Lower priority: description match
            search_conditions |= Q(description__icontains=term)
            
            # Medicine-specific searches
            if hasattr(Product, 'medicine_details'):
                search_conditions |= Q(medicine_details__composition__icontains=term)
                search_conditions |= Q(medicine_details__manufacturer__icontains=term)
                search_conditions |= Q(medicine_details__form__icontains=term)
            
            # Equipment-specific searches
            if hasattr(Product, 'equipment_details'):
                search_conditions |= Q(equipment_details__model_number__icontains=term)
                search_conditions |= Q(equipment_details__equipment_type__icontains=term)
                search_conditions |= Q(equipment_details__usage_type__icontains=term)
            
            # Tags search
            search_conditions |= Q(tags__name__icontains=term)
        
        return queryset.filter(search_conditions).distinct()
    
    def apply_smart_filters(self, queryset, filters):
        """
        Apply smart filters with auto-suggestions and related filtering
        """
        filtered_queryset = queryset
        
        # Category filter with subcategory support
        category = filters.get('category')
        if category:
            # Support both ID and name filtering
            try:
                category_id = int(category)
                filtered_queryset = filtered_queryset.filter(category_id=category_id)
            except ValueError:
                filtered_queryset = filtered_queryset.filter(category__name__icontains=category)
        
        # Brand filter with fuzzy matching
        brand = filters.get('brand')
        if brand:
            try:
                brand_id = int(brand)
                filtered_queryset = filtered_queryset.filter(brand_id=brand_id)
            except ValueError:
                filtered_queryset = filtered_queryset.filter(brand__name__icontains=brand)
        
        # Price range filtering
        min_price = filters.get('min_price')
        max_price = filters.get('max_price')
        if min_price:
            filtered_queryset = filtered_queryset.filter(price__gte=min_price)
        if max_price:
            filtered_queryset = filtered_queryset.filter(price__lte=max_price)
        
        # Product type filtering
        product_type = filters.get('product_type')
        if product_type:
            filtered_queryset = filtered_queryset.filter(product_type=product_type)
        
        # Stock availability
        in_stock_only = filters.get('in_stock_only', True)
        if in_stock_only:
            filtered_queryset = filtered_queryset.filter(stock__gt=0)
        
        # Medicine-specific filters
        prescription_required = filters.get('prescription_required')
        if prescription_required is not None:
            filtered_queryset = filtered_queryset.filter(medicine_details__prescription_required=prescription_required)
        
        form = filters.get('form')
        if form:
            filtered_queryset = filtered_queryset.filter(medicine_details__form__icontains=form)
        
        return filtered_queryset
    
    def apply_intelligent_sorting(self, queryset, sort_by, search_query=None):
        """
        Apply intelligent sorting with relevance scoring
        """
        # Default sorting options
        sort_options = {
            'relevance': ['-created_at'],  # Default when no search
            'price_low': ['price', 'name'],
            'price_high': ['-price', 'name'],
            'name_asc': ['name'],
            'name_desc': ['-name'],
            'newest': ['-created_at'],
            'oldest': ['created_at'],
            'popularity': ['-created_at'],  # Could be based on order count
            'rating': ['-created_at'],  # Could be based on review ratings
        }
        
        # If there's a search query, prioritize relevance
        if search_query and sort_by == 'relevance':
            # For now, we'll use creation date as relevance
            # In a real enterprise system, this would use search engines like Elasticsearch
            return queryset.order_by('-created_at', 'name')
        
        # Apply the requested sorting
        if sort_by in sort_options:
            return queryset.order_by(*sort_options[sort_by])
        
        # Default fallback
        return queryset.order_by('-created_at')