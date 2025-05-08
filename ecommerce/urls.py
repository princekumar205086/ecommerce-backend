from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core import views as core_views

# Swagger Schema View
schema_view = get_schema_view(
    openapi.Info(
        title="Medical eCommerce API",
        default_version='v1',
        description="API documentation for eCommerce platform selling pathology, doctor, and medical products.",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="support@medecommerce.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [

    # 🌐 Core Routes
    path('', core_views.home, name='home'),
    path('admin/', admin.site.urls),

    # 🔐 JWT Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 📦 App Routes
    path('api/accounts/', include('accounts.urls')),
    path('api/adminpanel/', include('adminpanel.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('api/cart/', include('cart.urls')),
    path('api/cms/', include('cms.urls')),
    path('api/coupons/', include('coupon.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/invoice/', include('invoice.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/products/', include('products.urls')),
    path('api/reviews/', include('reviews.urls')),
    path('api/support/', include('support.urls')),
    path('api/wishlist/', include('wishlist.urls')),
    # path('api/common/', include('common.urls')),  # Uncomment if used

    # 📘 API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# 🖼️ Media/Static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
