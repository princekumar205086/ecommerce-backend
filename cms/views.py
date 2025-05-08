# cms/views.py
from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone

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
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['title', 'content']
    filterset_fields = ['status', 'is_featured', 'show_in_nav']

    def get_queryset(self):
        queryset = Page.objects.all()

        # For non-admin users, only show published pages
        if not self.request.user.is_staff:
            queryset = queryset.filter(status='published')

        return queryset.order_by('order', 'title')


class PageDetailView(generics.RetrieveAPIView):
    serializer_class = PageSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = Page.objects.all()

        # For non-admin users, only show published pages
        if not self.request.user.is_staff:
            queryset = queryset.filter(status='published')

        return queryset


class BannerListView(generics.ListAPIView):
    serializer_class = BannerSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['position', 'is_active']

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
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['title', 'content', 'excerpt']
    filterset_fields = ['status', 'is_featured', 'categories', 'tags']
    ordering_fields = ['published_at', 'view_count']
    ordering = ['-published_at']

    def get_queryset(self):
        queryset = BlogPost.objects.all()

        # For non-admin users, only show published posts
        if not self.request.user.is_staff:
            queryset = queryset.filter(status='published')

        return queryset.select_related('author').prefetch_related('categories', 'tags')


class BlogPostDetailView(generics.RetrieveAPIView):
    serializer_class = BlogPostSerializer
    lookup_field = 'slug'

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
    queryset = BlogCategory.objects.all().order_by('name')


class BlogTagListView(generics.ListAPIView):
    serializer_class = BlogTagSerializer
    queryset = BlogTag.objects.all().order_by('name')


class FAQListView(generics.ListAPIView):
    serializer_class = FAQSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'is_active']

    def get_queryset(self):
        return FAQ.objects.filter(is_active=True).order_by('category', 'order')


class TestimonialListView(generics.ListAPIView):
    serializer_class = TestimonialSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_featured', 'is_active']

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
    lookup_field = 'slug'

    def get_queryset(self):
        return BlogCategory.objects.all()


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