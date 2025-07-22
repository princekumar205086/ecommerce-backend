from django.urls import path
from .views import (
    CreatePaymentView,
    VerifyPaymentView,
    RazorpayWebhookView,
    PaymentListView,
    PaymentDetailView
)
from .refund_views import RefundPaymentView, check_refund_status

urlpatterns = [
    path('create/', CreatePaymentView.as_view(), name='create-payment'),
    path('verify/', VerifyPaymentView.as_view(), name='verify-payment'),
    path('webhook/', RazorpayWebhookView.as_view(), name='razorpay-webhook'),
    path('', PaymentListView.as_view(), name='payment-list'),
    path('<int:pk>/', PaymentDetailView.as_view(), name='payment-detail'),
    path('<int:payment_id>/refund/', RefundPaymentView.as_view(), name='refund-payment'),
    path('<int:payment_id>/refund-status/', check_refund_status, name='check-refund-status'),
]