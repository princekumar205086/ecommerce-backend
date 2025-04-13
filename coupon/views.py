from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny
from .models import Coupon
from .serializers import CouponSerializer
from django.utils import timezone

class CouponListCreateView(generics.ListCreateAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [AllowAny()]

class ApplyCouponView(generics.GenericAPIView):
    serializer_class = CouponSerializer

    def post(self, request):
        code = request.data.get('code')
        total = float(request.data.get('total', 0))

        try:
            coupon = Coupon.objects.get(code=code, active=True, valid_until__gte=timezone.now())
            discount = total * (coupon.discount_percent / 100)
            final_total = total - discount
            return Response({
                "valid": True,
                "discount_percent": coupon.discount_percent,
                "discount_amount": round(discount, 2),
                "final_total": round(final_total, 2)
            })
        except Coupon.DoesNotExist:
            return Response({"valid": False, "error": "Invalid or expired coupon."}, status=status.HTTP_400_BAD_REQUEST)
