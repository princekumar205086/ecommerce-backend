from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

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
    path('', core_views.home, name='home'),
    path('admin/', admin.site.urls),

    # JWT auth endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # App routes (you can update these when you build the apps)
    path('api/accounts/', include('accounts.urls')),
    # path('api/adminpanel/', include('adminpanel.urls')),
    # path('api/analytics/', include('analytics.urls')),
    # path('api/cart/', include('cart.urls')),
    # path('api/cms/', include('cms.urls')),
    # path('api/common/', include('common.urls')),
    # path('api/core/', include('core.urls')),
    # path('api/inventory/', include('inventory.urls')),
    # path('api/notifications/', include('notifications.urls')),
    # path('api/orders/', include('orders.urls')),
    # path('api/payments/', include('payments.urls')),
    path('api/products/', include('products.urls')),
    # path('api/reviews/', include('reviews.urls')),
    # path('api/support/', include('support.urls')),

    # Swagger docs
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Static & media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
