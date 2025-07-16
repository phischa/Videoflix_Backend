from django.urls import path
from .views import (
    RegistrationView,
    LogoutView,
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
    HelloWorldView,
)

urlpatterns = [
    path('register/', RegistrationView.as_view(), name='register'),
    path('login/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'), 

    #path("activate/<uidb64>/<token>/", ),
    #path("password_reset/", ),
    #path("password_confirm/<uidb64>/<token>/",),

    path('hello/', HelloWorldView.as_view(), name='hello')
]
