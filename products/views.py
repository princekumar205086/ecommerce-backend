from rest_framework import generics, filters
from .models import Product, ProductCategory
from .serializers import ProductSerializer, ProductCategorySerializer

class ProductCategoryListView(generics.ListCreateAPIView):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer

class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']

    def get_queryset(self):
        queryset = Product.objects.all()
        category = self.request.query_params.get('category')
        ptype = self.request.query_params.get('type')
        if category:
            queryset = queryset.filter(category__name__iexact=category)
        if ptype:
            queryset = queryset.filter(type=ptype)
        return queryset

class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
