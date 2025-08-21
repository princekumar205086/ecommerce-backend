# cms/views.py
from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import (
    Page, Banner, BlogPost, BlogCategory,
    BlogTag, FAQ, Testimonial
)
from .serializers import (
    PageSerializer, BannerSerializer, BlogPostSerializer,
    BlogCategorySerializer, BlogTagSerializer, FAQSerializer,
    TestimonialSerializer
)


class PageListView(generics.ListAPIView):
    serializer_class = PageSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['title', 'content']
    filterset_fields = ['status', 'is_featured', 'show_in_nav']

    @swagger_auto_schema(
        operation_description="Get list of published pages",
        operation_summary="List Pages (Public)",
        tags=['Public - CMS'],
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Search pages by title or content", type=openapi.TYPE_STRING),
            openapi.Parameter('status', openapi.IN_QUERY, description="Filter by status", type=openapi.TYPE_STRING, enum=['draft', 'published', 'archived']),
            openapi.Parameter('is_featured', openapi.IN_QUERY, description="Filter by featured status", type=openapi.TYPE_BOOLEAN),
        ],
        responses={
            200: openapi.Response('Success', PageSerializer(many=True)),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Page.objects.all()

        # For non-admin users, only show published pages
        if not self.request.user.is_staff:
            queryset = queryset.filter(status='published')

        return queryset.order_by('order', 'title')


class PageDetailView(generics.RetrieveAPIView):
    serializer_class = PageSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    @swagger_auto_schema(
        operation_description="Get detailed view of a page",
        operation_summary="Get Page Details (Public)",
        tags=['Public - CMS'],
        responses={
            200: openapi.Response('Success', PageSerializer),
            404: openapi.Response('Not Found'),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Page.objects.all()

        # For non-admin users, only show published pages
        if not self.request.user.is_staff:
            queryset = queryset.filter(status='published')

        return queryset


class BannerListView(generics.ListAPIView):
    serializer_class = BannerSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['position', 'is_active']

    @swagger_auto_schema(
        operation_description="Get list of active banners",
        operation_summary="List Banners (Public)",
        tags=['Public - CMS'],
        manual_parameters=[
            openapi.Parameter('position', openapi.IN_QUERY, description="Filter by position", type=openapi.TYPE_STRING, enum=['home_top', 'home_middle', 'home_bottom', 'category_top', 'product_top']),
            openapi.Parameter('is_active', openapi.IN_QUERY, description="Filter by active status", type=openapi.TYPE_BOOLEAN),
        ],
        responses={
            200: openapi.Response('Success', BannerSerializer(many=True)),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        now = timezone.now()
        queryset = Banner.objects.filter(
            is_active=True,
            start_date__lte=now
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=now)
        )

        # Filter by position if provided in query params
        position = self.request.query_params.get('position')
        if position:
            queryset = queryset.filter(position=position)

        return queryset.order_by('order')


class BlogPostListView(generics.ListAPIView):
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['title', 'content', 'excerpt']
    filterset_fields = ['status', 'is_featured', 'categories', 'tags']
    ordering_fields = ['published_at', 'view_count']
    ordering = ['-published_at']

    @swagger_auto_schema(
        operation_description="Get list of published blog posts",
        operation_summary="List Blog Posts (Public)",
        tags=['Public - CMS'],
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Search blog posts by title, content, or excerpt", type=openapi.TYPE_STRING),
            openapi.Parameter('is_featured', openapi.IN_QUERY, description="Filter by featured status", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('categories', openapi.IN_QUERY, description="Filter by category ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('tags', openapi.IN_QUERY, description="Filter by tag ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by field", type=openapi.TYPE_STRING, enum=['published_at', '-published_at', 'view_count', '-view_count']),
        ],
        responses={
            200: openapi.Response('Success', BlogPostSerializer(many=True)),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = BlogPost.objects.all()

        # For non-admin users, only show published posts
        if not self.request.user.is_staff:
            queryset = queryset.filter(status='published')

        return queryset.select_related('author').prefetch_related('categories', 'tags')


class BlogPostDetailView(generics.RetrieveAPIView):
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    @swagger_auto_schema(
        operation_description="Get detailed view of a blog post",
        operation_summary="Get Blog Post Details (Public)",
        tags=['Public - CMS'],
        responses={
            200: openapi.Response('Success', BlogPostSerializer),
            404: openapi.Response('Not Found'),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = BlogPost.objects.all()

        # For non-admin users, only show published posts
        if not self.request.user.is_staff:
            queryset = queryset.filter(status='published')

        return queryset.select_related('author').prefetch_related('categories', 'tags')

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # Increment view count
        if instance.status == 'published':
            instance.view_count += 1
            instance.save()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class BlogCategoryListView(generics.ListAPIView):
    serializer_class = BlogCategorySerializer
    permission_classes = [permissions.AllowAny]
    queryset = BlogCategory.objects.all().order_by('name')

    @swagger_auto_schema(
        operation_description="Get list of blog categories",
        operation_summary="List Blog Categories (Public)",
        tags=['Public - CMS'],
        responses={
            200: openapi.Response('Success', BlogCategorySerializer(many=True)),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class BlogTagListView(generics.ListAPIView):
    serializer_class = BlogTagSerializer
    permission_classes = [permissions.AllowAny]
    queryset = BlogTag.objects.all().order_by('name')

    @swagger_auto_schema(
        operation_description="Get list of blog tags",
        operation_summary="List Blog Tags (Public)",
        tags=['Public - CMS'],
        responses={
            200: openapi.Response('Success', BlogTagSerializer(many=True)),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class FAQListView(generics.ListAPIView):
    serializer_class = FAQSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'is_active']

    @swagger_auto_schema(
        operation_description="Get list of frequently asked questions",
        operation_summary="List FAQs (Public)",
        tags=['Public - CMS'],
        manual_parameters=[
            openapi.Parameter('category', openapi.IN_QUERY, description="Filter by category", type=openapi.TYPE_STRING),
            openapi.Parameter('is_active', openapi.IN_QUERY, description="Filter by active status", type=openapi.TYPE_BOOLEAN),
        ],
        responses={
            200: openapi.Response('Success', FAQSerializer(many=True)),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return FAQ.objects.filter(is_active=True).order_by('category', 'order')


class TestimonialListView(generics.ListAPIView):
    serializer_class = TestimonialSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_featured', 'is_active']

    @swagger_auto_schema(
        operation_description="Get list of testimonials",
        operation_summary="List Testimonials (Public)",
        tags=['Public - CMS'],
        manual_parameters=[
            openapi.Parameter('is_featured', openapi.IN_QUERY, description="Filter by featured status", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('is_active', openapi.IN_QUERY, description="Filter by active status", type=openapi.TYPE_BOOLEAN),
        ],
        responses={
            200: openapi.Response('Success', TestimonialSerializer(many=True)),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Testimonial.objects.filter(is_active=True).order_by('-is_featured', '-created_at')


# Admin Views
class PageAdminView(generics.ListCreateAPIView):
    serializer_class = PageSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['title', 'content']
    filterset_fields = ['status', 'is_featured', 'show_in_nav']

    def get_queryset(self):
        return Page.objects.all().order_by('order', 'title')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class PageAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PageSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'slug'

    def get_queryset(self):
        return Page.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class BannerAdminView(generics.ListCreateAPIView):
    serializer_class = BannerSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['position', 'is_active']

    def get_queryset(self):
        return Banner.objects.all().order_by('position', 'order')


class BannerAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BannerSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return Banner.objects.all()


class BlogPostAdminView(generics.ListCreateAPIView):
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['title', 'content', 'excerpt']
    filterset_fields = ['status', 'is_featured', 'categories', 'tags']
    ordering_fields = ['published_at', 'view_count']
    ordering = ['-published_at']

    def get_queryset(self):
        return BlogPost.objects.all().select_related('author').prefetch_related('categories', 'tags')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class BlogPostAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'slug'

    def get_queryset(self):
        return BlogPost.objects.all().select_related('author').prefetch_related('categories', 'tags')


class BlogCategoryAdminView(generics.ListCreateAPIView):
    serializer_class = BlogCategorySerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = BlogCategory.objects.all().order_by('name')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class BlogCategoryAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BlogCategorySerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = BlogCategory.objects.all()


class BlogTagAdminView(generics.ListCreateAPIView):
    serializer_class = BlogTagSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = BlogTag.objects.all().order_by('name')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class FAQAdminView(generics.ListCreateAPIView):
    serializer_class = FAQSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'is_active']
    queryset = FAQ.objects.all().order_by('category', 'order')


class TestimonialAdminView(generics.ListCreateAPIView):
    serializer_class = TestimonialSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_featured', 'is_active']
    queryset = Testimonial.objects.all().order_by('-is_featured', '-created_at')