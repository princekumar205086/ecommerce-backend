from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from rest_framework.exceptions import NotFound, PermissionDenied

from .models import Cart, CartItem
from .serializers import (
    CartSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer
)
from products.models import Product, ProductVariant


class IsUserOrSupplier(IsAuthenticated):
    """
    Custom permission to only allow users and suppliers to access cart functionality.
    Admins should not be able to add items to cart as they don't have shopping carts.
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.role in ['user', 'supplier']


class CartView(generics.RetrieveAPIView):
    """Get user's cart with enhanced variant information"""
    serializer_class = CartSerializer
    permission_classes = [IsUserOrSupplier]

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart


class AddToCartView(generics.CreateAPIView):
    """Add item to cart with enhanced variant validation"""
    serializer_class = AddToCartSerializer
    permission_classes = [IsUserOrSupplier]

    def create(self, request, *args, **kwargs):
        cart = Cart.objects.get_or_create(user=request.user)[0]
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = get_object_or_404(Product, id=serializer.validated_data['product_id'])
            variant_id = serializer.validated_data.get('variant_id')
            quantity = serializer.validated_data.get('quantity', 1)

            variant = None
            if variant_id:
                variant = get_object_or_404(ProductVariant, id=variant_id)

            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                variant=variant,
                defaults={'quantity': quantity}
            )

            if not created:
                cart_item.quantity += quantity
                cart_item.save()

            return Response(
                {"message": "Item added to cart successfully"},
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )

        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UpdateCartItemView(generics.UpdateAPIView):
    """Update cart item with enhanced validation"""
    serializer_class = UpdateCartItemSerializer
    permission_classes = [IsUserOrSupplier]
    lookup_url_kwarg = 'pk'

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return CartItem.objects.none()
        return CartItem.objects.filter(cart__user=self.request.user)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data)
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Update quantity
            instance.quantity = serializer.validated_data['quantity']
            instance.save()

            return Response({
                "message": "Cart item updated successfully",
                "quantity": instance.quantity,
                "total_price": instance.total_price
            }, status=status.HTTP_200_OK)

        except CartItem.DoesNotExist:
            return Response(
                {"error": "Cart item not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class RemoveFromCartView(generics.DestroyAPIView):
    """Remove item from cart"""
    permission_classes = [IsUserOrSupplier]
    lookup_url_kwarg = 'pk'

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return CartItem.objects.none()
        return CartItem.objects.filter(cart__user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(
                {"message": "Item removed from cart successfully"},
                status=status.HTTP_200_OK
            )
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Cart item not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class ClearCartView(APIView):
    """Clear all items from cart"""
    permission_classes = [IsUserOrSupplier]

    def delete(self, request):
        cart = Cart.objects.filter(user=request.user).first()
        if not cart:
            return Response(
                {"message": "Cart is already empty"},
                status=status.HTTP_200_OK
            )
        
        items_count = cart.items.count()
        cart.items.all().delete()
        
        return Response(
            {"message": f"Cart cleared successfully. {items_count} items removed."},
            status=status.HTTP_200_OK
        )
