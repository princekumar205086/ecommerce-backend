"""
Shipping URL Configuration
"""

from django.urls import path, include
from . import views

app_name = 'shipping'

urlpatterns = [
    # Testing endpoints
    path('test/', views.ShipRocketTestView.as_view(), name='test_connection'),
    
    # Serviceability and rates
    path('serviceability/', views.CheckServiceabilityView.as_view(), name='check_serviceability'),
    path('rates/', views.ShippingRatesView.as_view(), name='shipping_rates'),
    
    # Shipment management
    path('shipments/', views.ShipmentListView.as_view(), name='shipment_list'),
    path('shipments/create/', views.CreateShipmentView.as_view(), name='create_shipment'),
    path('shipments/<str:order_id>/', views.ShipmentDetailView.as_view(), name='shipment_detail'),
    
    # Tracking
    path('track/', views.TrackShipmentView.as_view(), name='track_shipment'),
    
    # Webhooks
    path('webhook/', views.shiprocket_webhook, name='shiprocket_webhook'),
]