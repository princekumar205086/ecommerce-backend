from django.urls import path
from .views import TicketListCreateAPIView, TicketDetailAPIView

app_name = 'support'

urlpatterns = [
    path('tickets/', TicketListCreateAPIView.as_view(), name='list-create'),
    path('tickets/<int:pk>/', TicketDetailAPIView.as_view(), name='detail'),
]
