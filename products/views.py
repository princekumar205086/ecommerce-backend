from rest_framework import generics, filters, permissions
from django_filters.rest_framework import DjangoFilterBackend
from .models import *
from .serializers import *
from ecommerce.permissions import IsSupplierOrAdmin, IsAdminOrReadOnly

class ProductCategoryListCreateView(generics.ListCreateAPIView):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    permission_classes = [IsSupplierOrAdmin]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, status='pending', is_publish=False)

class ProductSubCategoryListCreateView(generics.ListCreateAPIView):
    queryset = ProductSubCategory.objects.all()
    serializer_class = ProductSubCategorySerializer
    permission_classes = [IsSupplierOrAdmin]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, status='pending', is_publish=False)

class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsSupplierOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'subcategory', 'brand', 'type']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'date_of_created']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, status='pending', is_publish=False)

class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsSupplierOrAdmin]

class ProductReviewListCreateView(generics.ListCreateAPIView):
    queryset = ProductReview.objects.all()
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BrandListCreateView(generics.ListCreateAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsSupplierOrAdmin]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class ProductVariantListCreateView(generics.ListCreateAPIView):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    permission_classes = [IsSupplierOrAdmin]
