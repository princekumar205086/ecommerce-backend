from django.urls import path
from .views import (
    CreatePaymentView,
    CreatePaymentFromCartView,
    VerifyPaymentView,
    ConfirmRazorpayView,
    RazorpayWebhookView,
    PaymentListView,
    PaymentDetailView,
    ConfirmCODView,
    PathlogWalletVerifyView,
    PathlogWalletOTPView,
    PathlogWalletPaymentView
)
from .refund_views import RefundPaymentView, check_refund_status

urlpatterns = [
    path('create/', CreatePaymentView.as_view(), name='create-payment'),  # Legacy: from order
    path('create-from-cart/', CreatePaymentFromCartView.as_view(), name='create-payment-from-cart'),  # NEW: from cart
    path('verify/', VerifyPaymentView.as_view(), name='verify-payment'),
    path('confirm-razorpay/', ConfirmRazorpayView.as_view(), name='confirm-razorpay'),  # NEW: Razorpay confirmation
    path('confirm-cod/', ConfirmCODView.as_view(), name='confirm-cod'),  # NEW: COD confirmation
    
    # Pathlog Wallet endpoints
    path('pathlog-wallet/verify/', PathlogWalletVerifyView.as_view(), name='pathlog-wallet-verify'),
    path('pathlog-wallet/otp/', PathlogWalletOTPView.as_view(), name='pathlog-wallet-otp'),
    path('pathlog-wallet/pay/', PathlogWalletPaymentView.as_view(), name='pathlog-wallet-pay'),
    
    path('webhook/', RazorpayWebhookView.as_view(), name='razorpay-webhook'),
    path('', PaymentListView.as_view(), name='payment-list'),
    path('<int:pk>/', PaymentDetailView.as_view(), name='payment-detail'),
    path('<int:payment_id>/refund/', RefundPaymentView.as_view(), name='refund-payment'),
    path('<int:payment_id>/refund-status/', check_refund_status, name='check-refund-status'),
]