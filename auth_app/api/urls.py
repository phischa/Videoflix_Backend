from django.urls import path
from .views import (
    RegistrationView,
    LogoutView,
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
    HelloWorldView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('register/', RegistrationView.as_view(), name='register'),
    path('login/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'), 

    path('hello/', HelloWorldView.as_view(), name='hello')
]
