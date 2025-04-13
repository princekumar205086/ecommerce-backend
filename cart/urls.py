from django.urls import path
from .views import CartView, AddToCartView, RemoveFromCartView, UpdateCartItemView, ClearCartView

urlpatterns = [
    path('', CartView.as_view(), name='get-cart'),
    path('add/', AddToCartView.as_view(), name='add-to-cart'),
    path('remove/<int:product_id>/', RemoveFromCartView.as_view(), name='remove-from-cart'),
    path('update/<int:product_id>/', UpdateCartItemView.as_view(), name='update-cart-item'),
    path('clear/', ClearCartView.as_view(), name='clear-cart'),

]
