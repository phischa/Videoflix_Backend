import logging
from rest_framework_simplejwt.authentication import JWTAuthentication

logger = logging.getLogger(__name__)

class CookieJWTAuthentication(JWTAuthentication):
    def get_raw_token(self, request):
        logger.error("DEBUG: CookieJWTAuthentication.get_raw_token() called")
        
        # Header prüfen - MANUELL (umgehe super())
        header = request.META.get('HTTP_AUTHORIZATION')
        if header is not None:
            parts = header.split()
            if len(parts) == 2 and parts[0] == 'Bearer':
                logger.error(f"DEBUG: Token from header: {parts[1][:20]}...")
                return parts[1]
        
        # Cookie prüfen  
        cookie_token = request.COOKIES.get('access_token')
        logger.error(f"DEBUG: Token from cookie: {cookie_token[:20] if cookie_token else 'None'}")
        logger.error(f"DEBUG: Available cookies: {list(request.COOKIES.keys())}")
        
        return cookie_token
    
    def authenticate(self, request):
        logger.error("DEBUG: CookieJWTAuthentication.authenticate() called")
        
        raw_token = self.get_raw_token(request)
        
        if raw_token is None:
            logger.error("DEBUG: No raw token found")
            return None
            
        logger.error(f"DEBUG: Raw token found: {raw_token[:20]}")
        
        # Standard JWT-Validierung
        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            logger.error(f"DEBUG: Authentication SUCCESS for user: {user.email}")
            return (user, validated_token)
        except Exception as e:
            logger.error(f"DEBUG: Token validation failed: {e}")
            return None