from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from .models import Order
from .serializers import OrderSerializer
from coupon.utils import apply_coupon
from cart.models import Cart

class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart = Cart.objects.get(user=request.user)
        if not cart.items.exists():
            return Response({"error": "Cart is empty"}, status=400)

        total = sum(item.product.price * item.quantity for item in cart.items.all())

        code = request.data.get("coupon")
        if code:
            total, discount = apply_coupon(code, total)

        order = Order.objects.create(
            user=request.user,
            total=total,
            shipping_address=request.data.get("shipping_address", ""),
            payment_method=request.data.get("payment_method", "Cash on Delivery")
        )
        order.items.set(cart.items.all())
        cart.items.all().delete()

        return Response({"message": "Order placed successfully", "order_id": order.id})


class OrderListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


class OrderDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
