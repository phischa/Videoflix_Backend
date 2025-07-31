import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken


from ..services import (
    generate_activation_token,
    verify_activation_token,
    activate_user,
    send_activation_email,
    send_password_reset_email,       
    verify_password_reset_token,      
    reset_user_password,  
)

from .serializers import (
    RegistrationSerializer,
    CustomTokenObtainPairSerializer,
    PasswordResetSerializer,
    PasswordConfirmSerializer
)

logger = logging.getLogger(__name__)


class HelloWorldView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': 'Hello World!'})


class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)

        if serializer.is_valid():
            saved_account = serializer.save()
            email_sent = send_activation_email(saved_account, request)
            
            data = {
                "user": {
                    "id": saved_account.pk,
                    "email": saved_account.email
                },
                "message": "Account created. Activation email sent." if email_sent else "Account created. Please contact support.",
                "email_sent": email_sent
            }
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        
        if refresh_token is None:
            return Response(
                {"detail": "Refresh token missing"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            
        except Exception:
            return Response(
                {"detail": "Invalid refresh token"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        response = Response({
            "detail": "Log-Out successfully! All Tokens will be deleted. Refresh token is blacklisted."
        }, status=status.HTTP_200_OK)
        
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        
        return response


class CookieTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh = serializer.validated_data["refresh"]
        access = serializer.validated_data["access"]

        user = serializer.user 
        response = Response({
            "detail": "Login successful", 
            "user": {
                "id": user.id,
                "username": user.email
            }
        }, status=status.HTTP_200_OK)

        response.set_cookie(
            key="access_token",
            value=str(access),
            httponly=True,
            secure=False,
            samesite="Lax",
            path="/",
            domain=None 
        )

        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=False,
            samesite="Lax"
        )

        return response
    

class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token is None:
            return Response(
                {"detail": "Refresh token not found!"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        serializer = self.get_serializer(data={"refresh":refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except:
            return Response(
                {"detail": "Refresh token invalid!"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        
        access_token = serializer.validated_data.get("access")
        new_refresh_token = serializer.validated_data.get("refresh")

        response = Response({
                    "detail": "Token refreshed",
                    "access": "new_access_token"
                }, status=status.HTTP_200_OK)

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,
            samesite="Lax"
        )

        if new_refresh_token:
            response.set_cookie(
                key="refresh_token",
                value=new_refresh_token,
                httponly=True,
                secure=False,
                samesite="Lax"
            )

        return response

class AccountActivationView(APIView):
    """
    Handles account activation via email token
    GET /api/activate/<uidb64>/<token>/
    """
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        # Verify activation token
        user = verify_activation_token(uidb64, token)
        
        if not user:
            return Response({
                "detail": "Invalid or expired activation link"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Activate user if not already active
        if not user.is_active:
            success = activate_user(user)
            if success:
                return Response({
                    "message": "Account successfully activated."
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "detail": "Failed to activate account"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                "message": "Account successfully activated."
            }, status=status.HTTP_200_OK)
        

class PasswordResetView(APIView):
    """
    Handles password reset email sending
    POST /api/password_reset/
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        
        if serializer.is_valid():
            # Check if user exists (stored in serializer during validation)
            if hasattr(serializer, 'user') and serializer.user:
                # User exists - send password reset email
                
                try:
                    email_sent = send_password_reset_email(serializer.user, request)
                    
                    if email_sent:
                        logger.info(f"Password reset email sent to {serializer.user.email}")
                    else:
                        logger.error(f"Failed to send password reset email to {serializer.user.email}")
                        
                except Exception as e:
                    logger.error(f"Error sending password reset email: {e}")
            
            # ALWAYS return same success message for security
            # (Don't reveal if user exists or not)
            return Response({
                "detail": "An email has been sent to reset your password."
            }, status=status.HTTP_200_OK)
        
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordConfirmView(APIView):
    """
    Handles password reset confirmation
    POST /api/password_confirm/<uidb64>/<token>/
    """
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        # Validate the reset token first
        user = verify_password_reset_token(uidb64, token)
        
        if not user:
            return Response({
                "detail": "Invalid or expired password reset link"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate the new password
        serializer = PasswordConfirmSerializer(data=request.data)
        
        if serializer.is_valid():
            new_password = serializer.validated_data['new_password']
            
            # Reset the password using token service
            success = reset_user_password(user, new_password)
            
            if success:
                logger.info(f"Password successfully reset for user {user.id} ({user.email})")
                
                return Response({
                    "detail": "Your password has been successfully reset."
                }, status=status.HTTP_200_OK)
            else:
                logger.error(f"Failed to reset password for user {user.id} ({user.email})")
                
                return Response({
                    "detail": "Failed to reset password. Please try again."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)