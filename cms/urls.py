# cms/urls.py
from django.urls import path
from . import views

app_name = 'cms'

urlpatterns = [
    # Public endpoints
    path('pages/', views.PageListView.as_view(), name='page-list'),
    path('pages/<slug:slug>/', views.PageDetailView.as_view(), name='page-detail'),
    path('banners/', views.BannerListView.as_view(), name='banner-list'),
    path('carousel/', views.CarouselBannerListView.as_view(), name='carousel-list'),
    path('blog/', views.BlogPostListView.as_view(), name='blog-list'),
    path('blog/categories/', views.BlogCategoryListView.as_view(), name='blog-category-list'),
    path('blog/tags/', views.BlogTagListView.as_view(), name='blog-tag-list'),
    path('blog/<slug:slug>/', views.BlogPostDetailView.as_view(), name='blog-detail'),
    path('faqs/', views.FAQListView.as_view(), name='faq-list'),
    path('testimonials/', views.TestimonialListView.as_view(), name='testimonial-list'),

    # Admin endpoints
    path('admin/pages/', views.PageAdminView.as_view(), name='admin-page-list'),
    path('admin/pages/<slug:slug>/', views.PageAdminDetailView.as_view(), name='admin-page-detail'),
    path('admin/banners/', views.BannerAdminView.as_view(), name='admin-banner-list'),
    path('admin/banners/<int:pk>/', views.BannerAdminDetailView.as_view(), name='admin-banner-detail'),
    path('admin/carousels/', views.CarouselBannerAdminView.as_view(), name='admin-carousel-list'),
    path('admin/carousels/<int:pk>/', views.CarouselBannerAdminDetailView.as_view(), name='admin-carousel-detail'),
    path('admin/blog/', views.BlogPostAdminView.as_view(), name='admin-blog-list'),
    path('admin/blog/<slug:slug>/', views.BlogPostAdminDetailView.as_view(), name='admin-blog-detail'),
    path('admin/blog/categories/', views.BlogCategoryAdminView.as_view(), name='admin-blog-category-list'),
    path('admin/blog/categories/<int:pk>/', views.BlogCategoryAdminDetailView.as_view(), name='admin-blog-category-detail'),
    path('admin/blog/tags/', views.BlogTagAdminView.as_view(), name='admin-blog-tag-list'),
    path('admin/faqs/', views.FAQAdminView.as_view(), name='admin-faq-list'),
    path('admin/testimonials/', views.TestimonialAdminView.as_view(), name='admin-testimonial-list'),
]