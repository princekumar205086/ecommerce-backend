# analytics/urls.py
from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('track/', views.TrackEventView.as_view(), name='track-event'),
    path('dashboard/', views.AnalyticsDashboardView.as_view(), name='analytics-dashboard'),
    path('reports/', views.SalesReportListView.as_view(), name='sales-report-list'),
    path('reports/generate/', views.GenerateSalesReportView.as_view(), name='generate-sales-report'),
    path('products/', views.ProductAnalyticsView.as_view(), name='product-analytics'),
    path('categories/', views.CategoryAnalyticsView.as_view(), name='category-analytics'),
    path('user-activity/<int:user__id>/', views.UserActivityView.as_view(), name='user-activity'),
    path('inventory-alerts/', views.InventoryAlertsView.as_view(), name='inventory-alerts'),
    path('inventory-alerts/<int:pk>/resolve/', views.ResolveInventoryAlertView.as_view(), name='resolve-inventory-alert'),
    path('events/', views.EventLogView.as_view(), name='event-log'),
]