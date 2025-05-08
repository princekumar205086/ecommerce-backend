# invoice/urls.py
from django.urls import path
from . import views

app_name = 'invoice'

urlpatterns = [
    path('', views.InvoiceListView.as_view(), name='invoice-list'),
    path('create/', views.InvoiceCreateView.as_view(), name='invoice-create'),
    path('<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice-detail'),
    path('<int:pk>/pdf/', views.InvoicePDFView.as_view(), name='invoice-pdf'),
    path('<int:pk>/payments/', views.InvoicePaymentListView.as_view(), name='invoice-payment-list'),
    path('<int:pk>/record-payment/', views.RecordPaymentView.as_view(), name='record-payment'),
    path('overdue/', views.OverdueInvoicesView.as_view(), name='overdue-invoices'),
]