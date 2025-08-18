import logging
from rest_framework_simplejwt.authentication import JWTAuthentication

logger = logging.getLogger(__name__)


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT Authentication that reads tokens from cookies.
    
    Extends SimpleJWT's JWTAuthentication to support cookie-based tokens.
    Allows frontend applications to use JWT tokens via HttpOnly cookies
    instead of Authorization headers.
    """
    
    def get_raw_token(self, request):
        """
        Extracts JWT token from request header or cookie.
        
        Args:
            request (HttpRequest): Django HTTP request object
            
        Returns:
            str|None: JWT token string or None if not found
        """
        
        # Header prüfen - MANUELL (umgehe super())
        header = request.META.get('HTTP_AUTHORIZATION')
        if header is not None:
            parts = header.split()
            if len(parts) == 2 and parts[0] == 'Bearer':
                return parts[1]
        
        # Cookie prüfen  
        cookie_token = request.COOKIES.get('access_token')
        
        return cookie_token
    
    def authenticate(self, request):
        """
        Authenticates request based on JWT token.
        
        Args:
            request (HttpRequest): Django HTTP request object
            
        Returns:
            tuple|None: (User, Token) on successful authentication or None
        """
        
        raw_token = self.get_raw_token(request)
        
        if raw_token is None:
            return None
        
        # Standard JWT-Validierung
        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            return (user, validated_token)
        except Exception as e:
            return None