"""
Custom authentication backends for Real MFA
Supports email-based authentication for both admin and API
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Authenticate using email instead of username
    Supports both admin login and API authentication
    Requires email to be verified before login
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user by email or username
        Blocks login if email is not verified
        """
        try:
            # Try to find user by email
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            try:
                # Fallback to username if email doesn't work
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None
        
        # Verify password first
        if not user.check_password(password):
            return None
        
        # Check if user can authenticate (is_active, etc.)
        if not self.user_can_authenticate(user):
            return None
        
        # Block login if email not verified
        if not user.email_verified:
            return None
        
        return user
    
    def get_user(self, user_id):
        """Get user by ID"""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


# ============================================================================
# CUSTOM JWT AUTHENTICATION WITH SESSION VALIDATION
# ============================================================================
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from devices.models import Session, Device


class SessionValidatedJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that validates:
    1. JWT token is valid (standard SimpleJWT validation)
    2. Session is still active (not revoked)
    3. Device is not compromised or deleted
    
    This ensures that revoking a session or device immediately blocks access,
    even if the JWT token hasn't expired yet.
    """
    
    def authenticate(self, request):
        """
        Authenticate the request and validate session/device status.
        """
        # First, do standard JWT authentication
        result = super().authenticate(request)
        
        if result is None:
            return None
        
        user, validated_token = result
        
        # Get the token's jti (JWT ID)
        token_jti = validated_token.get('jti')
        
        # Try multiple methods to find the session
        session = None
        
        # Method 1: Find by token_jti (stored as refresh token's jti)
        if token_jti:
            session = Session.objects.filter(
                user=user,
                token_jti=token_jti
            ).first()
        
        # Method 2: Find by fingerprint from header
        if not session:
            fingerprint = request.META.get('HTTP_X_DEVICE_FINGERPRINT')
            if fingerprint:
                session = Session.objects.filter(
                    user=user,
                    fingerprint_hash=fingerprint
                ).order_by('-created_at').first()
        
        # Method 3: Find most recent session for this user
        # (fallback when no token_jti match and no fingerprint header)
        if not session:
            session = Session.objects.filter(
                user=user
            ).order_by('-last_activity', '-created_at').first()
        
        # If no session found at all, deny access
        if not session:
            raise AuthenticationFailed(
                'No valid session found. Please login again.',
                code='no_session'
            )
        
        # Check if session is revoked (is_active=False)
        if not session.is_active:
            raise AuthenticationFailed(
                'Session has been revoked. Please login again.',
                code='session_revoked'
            )
        
        # Check if session is expired
        from django.utils import timezone
        if session.expires_at and timezone.now() > session.expires_at:
            session.is_active = False
            session.revoked_reason = 'session_expired'
            session.save(update_fields=['is_active', 'revoked_reason'])
            raise AuthenticationFailed(
                'Session has expired. Please login again.',
                code='session_expired'
            )
        
        # Check if device is compromised or deleted
        if session.fingerprint_hash:
            device = Device.objects.filter(
                user=user,
                fingerprint_hash=session.fingerprint_hash
            ).first()
            
            if device:
                if device.is_deleted:
                    raise AuthenticationFailed(
                        'Device has been revoked. Please login again.',
                        code='device_revoked'
                    )
                if device.is_compromised:
                    raise AuthenticationFailed(
                        'Device has been marked as compromised. Please contact support.',
                        code='device_compromised'
                    )
        
        # Update last activity
        session.last_activity = timezone.now()
        session.save(update_fields=['last_activity'])
        
        # Store session in request for later use
        request.current_session = session
        
        return (user, validated_token)