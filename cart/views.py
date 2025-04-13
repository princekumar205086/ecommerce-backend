from django.shortcuts import render

# Create your views here.
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .models import Cart, CartItem
from .serializers import CartSerializer, AddToCartSerializer

class CartView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart


class AddToCartView(generics.CreateAPIView):
    serializer_class = AddToCartSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        product_id = request.data.get('product')
        quantity = int(request.data.get('quantity', 1))

        if not product_id:
            return Response({"error": "Product is required"}, status=400)

        item, created = CartItem.objects.get_or_create(cart=cart, product_id=product_id)
        if not created:
            item.quantity += quantity
            item.save()
            return Response({"message": "Item quantity updated"}, status=200)
        else:
            item.quantity = quantity
            item.save()
            return Response({"message": "Item added to cart"}, status=201)


class RemoveFromCartView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        cart = Cart.objects.get(user=request.user)
        product_id = kwargs.get('product_id')
        try:
            item = CartItem.objects.get(cart=cart, product_id=product_id)
            item.delete()
            return Response({"message": "Item removed from cart"}, status=status.HTTP_204_NO_CONTENT)
        except CartItem.DoesNotExist:
            return Response({"error": "Item not found in cart"}, status=status.HTTP_404_NOT_FOUND)

class UpdateCartItemView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, product_id):
        cart = Cart.objects.get(user=request.user)
        quantity = int(request.data.get('quantity', 1))

        try:
            item = CartItem.objects.get(cart=cart, product_id=product_id)
            item.quantity = quantity
            item.save()
            return Response({"message": "Item quantity updated"}, status=200)
        except CartItem.DoesNotExist:
            return Response({"error": "Item not found"}, status=404)


class ClearCartView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        cart = Cart.objects.get(user=request.user)
        cart.items.all().delete()
        return Response({"message": "Cart cleared"}, status=204)
