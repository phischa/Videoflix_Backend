from django.urls import path
from .views import (
    RegistrationView,
    LogoutView,
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
    AccountActivationView,
    PasswordResetView,
    PasswordConfirmView,
    HelloWorldView,
)

urlpatterns = [
    path('register/', RegistrationView.as_view(), name='register'),
    path('login/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'), 

    path("activate/<str:uidb64>/<str:token>/", AccountActivationView.as_view(), name='account_activate'),
    path('password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password_confirm/<str:uidb64>/<str:token>/', PasswordConfirmView.as_view(), name='password_confirm'),

    path('hello/', HelloWorldView.as_view(), name='hello')
]
