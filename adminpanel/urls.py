# adminpanel/urls.py
from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    path('dashboard/', views.AdminDashboardView.as_view(), name='admin-dashboard'),
    path('settings/', views.SystemSettingListView.as_view(), name='system-setting-list'),
    path('settings/<str:key>/', views.SystemSettingDetailView.as_view(), name='system-setting-detail'),
    path('logs/', views.AdminLogListView.as_view(), name='admin-log-list'),
    path('notifications/', views.AdminNotificationListView.as_view(), name='admin-notification-list'),
    path('notifications/mark-read/', views.MarkNotificationReadView.as_view(), name='mark-notification-read'),
    path('notifications/mark-all-read/', views.MarkAllNotificationsReadView.as_view(), name='mark-all-notifications-read'),
    path('export/', views.ExportDataView.as_view(), name='export-data'),
    path('import/', views.ImportDataView.as_view(), name='import-data'),
    path('generate-sales-report/', views.GenerateSalesReportView.as_view(), name='generate-sales-report'),
]