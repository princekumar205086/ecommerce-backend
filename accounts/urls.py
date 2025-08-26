# accounts/urls.py
from django.urls import path
from .views import RegisterView, LoginView, ProfileView, UserListView, UserAddressView, SaveAddressFromCheckoutView, MedixMallModeToggleView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('register/<str:role>/', RegisterView.as_view(), name='register-with-role'),
    path('login/', LoginView.as_view(), name='login'),
    path('me/', ProfileView.as_view(), name='profile'),
    path('list/', UserListView.as_view(), name='user_list'),
    path('address/', UserAddressView.as_view(), name='user_address'),
    path('address/save-from-checkout/', SaveAddressFromCheckoutView.as_view(), name='save_address_from_checkout'),
    path('medixmall-mode/', MedixMallModeToggleView.as_view(), name='medixmall_mode_toggle'),
]