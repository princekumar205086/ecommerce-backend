from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound
from django.shortcuts import get_object_or_404
from .models import Wishlist, WishlistItem
from .serializers import (
    WishlistSerializer, WishlistItemSerializer,
    CreateWishlistSerializer, UpdateWishlistSerializer
)
from products.models import Product, ProductVariant


class WishlistListView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WishlistSerializer

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateWishlistSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WishlistDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WishlistSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Wishlist.objects.none()  # Return an empty queryset for schema generation
        if not self.request.user.is_authenticated:
            return Wishlist.objects.none()
        return Wishlist.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UpdateWishlistSerializer
        return super().get_serializer_class()


class WishlistItemCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WishlistItemSerializer

    def get_queryset(self):
        return WishlistItem.objects.filter(wishlist__user=self.request.user)

    def perform_create(self, serializer):
        wishlist = get_object_or_404(
            Wishlist,
            pk=self.kwargs['wishlist_id'],
            user=self.request.user
        )

        # Get the product and variant from validated data
        product = serializer.validated_data['product']
        variant = serializer.validated_data.get('variant')

        # Check for existing item
        if WishlistItem.objects.filter(
                wishlist=wishlist,
                product=product,
                variant=variant
        ).exists():
            raise ValidationError({
                'detail': 'This item already exists in your wishlist'
            })

        serializer.save(wishlist=wishlist)

    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            return Response(
                exc.detail,
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().handle_exception(exc)


class WishlistItemDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {'detail': 'Item removed from wishlist'},
            status=status.HTTP_204_NO_CONTENT
        )

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Wishlist.objects.none()
        if not self.request.user.is_authenticated:
            return Wishlist.objects.none()
        return Wishlist.objects.filter(user=self.request.user)


class DefaultWishlistView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WishlistSerializer

    def get_object(self):
        wishlist, created = Wishlist.objects.get_or_create(
            user=self.request.user,
            is_default=True,
            defaults={'name': 'My Wishlist'}
        )
        return wishlist
