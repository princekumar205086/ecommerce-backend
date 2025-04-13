from django.urls import path
from .views import WishlistView, ToggleWishlistItemView

urlpatterns = [
    path('', WishlistView.as_view(), name='wishlist'),
    path('toggle/<int:product_id>/', ToggleWishlistItemView.as_view(), name='toggle-wishlist'),
]
