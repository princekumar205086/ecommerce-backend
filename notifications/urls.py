# notifications/urls.py
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='notification-list'),
    path('<int:id>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('mark-as-read/', views.MarkAsReadView.as_view(), name='mark-as-read'),
    path('mark-all-as-read/', views.MarkAllAsReadView.as_view(), name='mark-all-as-read'),
    path('preferences/', views.NotificationPreferenceView.as_view(), name='notification-preferences'),
    path('count/', views.NotificationCountView.as_view(), name='notification-count'),
]