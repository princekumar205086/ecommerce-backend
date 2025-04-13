from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .models import Wishlist
from products.models import Product
from .serializers import WishlistSerializer

class WishlistView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WishlistSerializer  # Add serializer_class

    def get(self, request):
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(wishlist)  # Use self.get_serializer()
        return Response(serializer.data)

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return WishlistSerializer  # Return serializer for schema generation
        return super().get_serializer_class()

class ToggleWishlistItemView(APIView):
    serializer_class = WishlistSerializer

    def post(self, request, *args, **kwargs):
        # Your logic for toggling wishlist items
        return Response({"message": "Wishlist item toggled"})

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return WishlistSerializer  # Return a serializer for schema generation
        return super().get_serializer_class()