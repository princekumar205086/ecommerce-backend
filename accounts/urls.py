# accounts/urls.py
from django.urls import path
from .views import RegisterView, LoginView, ProfileView, UserListView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('register/<str:role>/', RegisterView.as_view(), name='register-with-role'),
    path('login/', LoginView.as_view(), name='login'),
    path('me/', ProfileView.as_view(), name='profile'),
    path('list/', UserListView.as_view(), name='user_list'),
]