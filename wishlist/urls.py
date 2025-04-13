from django.urls import path
from .views import (
    WishlistListView, WishlistDetailView,
    WishlistItemCreateView, WishlistItemDeleteView,
    DefaultWishlistView
)

urlpatterns = [
    path('', WishlistListView.as_view(), name='wishlist-list'),
    path('default/', DefaultWishlistView.as_view(), name='default-wishlist'),
    path('<int:pk>/', WishlistDetailView.as_view(), name='wishlist-detail'),
    path('<int:wishlist_id>/items/', WishlistItemCreateView.as_view(), name='wishlist-item-create'),
    path('items/<int:pk>/', WishlistItemDeleteView.as_view(), name='wishlist-item-delete'),
]