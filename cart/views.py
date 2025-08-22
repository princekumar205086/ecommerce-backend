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
    serializer_class = CartSerializer
    permission_classes = [IsUserOrSupplier]

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart


class AddToCartView(generics.CreateAPIView):
    serializer_class = AddToCartSerializer
    permission_classes = [IsUserOrSupplier]

    def create(self, request, *args, **kwargs):
        cart = Cart.objects.get_or_create(user=request.user)[0]
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = get_object_or_404(
            Product,
            id=serializer.validated_data['product_id']
        )
        variant_id = serializer.validated_data.get('variant_id')
        quantity = serializer.validated_data.get('quantity', 1)

        variant = None
        if variant_id:
            variant = get_object_or_404(
                ProductVariant,
                id=variant_id
            )
            if variant.product != product:
                return Response(
                    {"error": "Variant does not belong to product"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        try:
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
                {"message": "Item added to cart"},
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class UpdateCartItemView(generics.UpdateAPIView):
    serializer_class = UpdateCartItemSerializer
    permission_classes = [IsUserOrSupplier]
    lookup_url_kwarg = 'pk'

    def get_queryset(self):
        # Return an empty queryset during schema generation
        if getattr(self, 'swagger_fake_view', False):
            return CartItem.objects.none()
        return CartItem.objects.filter(cart__user=self.request.user)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)

            # Manual validation and update
            instance.quantity = serializer.validated_data['quantity']
            instance.full_clean()
            instance.save()

            return Response(serializer.data, status=status.HTTP_200_OK)

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
    permission_classes = [IsUserOrSupplier]
    lookup_url_kwarg = 'pk'

    def get_queryset(self):
        # Return an empty queryset during schema generation
        if getattr(self, 'swagger_fake_view', False):
            return CartItem.objects.none()
        return CartItem.objects.filter(cart__user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Cart item not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class ClearCartView(APIView):
    permission_classes = [IsUserOrSupplier]

    def delete(self, request):
        cart = Cart.objects.filter(user=request.user).first()
        if not cart:
            return Response(status=status.HTTP_204_NO_CONTENT)
        cart.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
