"""
Authentication Views - Login and Logout only
Device verification moved to devices app
OTP resend moved to otp app
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .auth_serializers import LoginSerializer, LogoutSerializer, MFAVerifyLoginSerializer


class LoginRateThrottle(AnonRateThrottle):
    """Rate limit: 5 login attempts per minute per IP"""
    rate = '5/minute'


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login user with email/username and password
    
    POST /api/auth/login/
    {
        "identifier": "user@example.com",  // or "username"
        "password": "SecurePass123!",
        "device": {
            "fingerprint_hash": "abc123def456...",
            "device_name": "My iPhone",
            "device_type": "mobile",
            "browser": "Safari",
            "os": "iOS 17"
        }
    }
    
    Response Scenarios:
    
    1. Success (trusted device, no MFA or MFA skipped):
    {
        "status": "success",
        "message": "Login successful",
        "user": {"id": "uuid", "email": "...", "username": "...", "role": "user"},
        "device": {"id": "uuid", "name": "...", "is_trusted": true},
        "tokens": {"access": "...", "refresh": "..."}
    }
    
    2. MFA required:
    {
        "status": "mfa_required",
        "message": "MFA verification required. Please enter your TOTP code.",
        "user_id": "uuid",
        "fingerprint_hash": "abc123...",
        "mfa_method": "totp"
    }
    
    3. New device (requires OTP verification):
    {
        "status": "device_verification_required",
        "message": "New device detected. Please verify with the OTP sent to your email.",
        "user_id": "uuid",
        "email_hint": "use***@example.com",
        "otp_expires_at": "2026-01-08T12:30:00Z"
    }
    
    4. Error responses:
    - 400: Invalid credentials, account locked, email not verified
    - 429: Too many login attempts
    """
    # Apply rate limiting
    throttle = LoginRateThrottle()
    if not throttle.allow_request(request, None):
        return Response(
            {
                "error": "Too many login attempts. Please try again later.",
                "retry_after": throttle.wait()
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    serializer = LoginSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        result = serializer.save()
        
        # Determine appropriate status code
        if result.get('status') == 'device_verification_required':
            return Response(result, status=status.HTTP_202_ACCEPTED)
        
        if result.get('status') == 'mfa_required':
            return Response(result, status=status.HTTP_202_ACCEPTED)
        
        return Response(result, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_mfa_login(request):
    """
    Verify MFA (TOTP) code to complete login
    
    POST /api/auth/verify-mfa/
    {
        "user_id": "uuid",
        "fingerprint_hash": "abc123...",
        "totp_code": "123456",
        "trust_device": true,  // Optional: trust this device to skip MFA
        "trust_days": 30       // Optional: days to trust (1-90)
    }
    
    OR with backup code:
    {
        "user_id": "uuid",
        "fingerprint_hash": "abc123...",
        "backup_code": "A1B2-C3D4",
        "trust_device": false
    }
    
    Response (200):
    {
        "status": "success",
        "message": "MFA verified. Login successful.",
        "user": {"id": "uuid", "email": "...", "username": "...", "role": "user"},
        "device": {"id": "uuid", "name": "...", "is_trusted": true, "is_new": false},
        "tokens": {"access": "...", "refresh": "..."}
    }
    
    Response (400):
    - Invalid TOTP code
    - Invalid backup code
    - No pending MFA verification
    """
    serializer = MFAVerifyLoginSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout user by blacklisting refresh token
    
    POST /api/auth/logout/
    Headers: Authorization: Bearer <access_token>
    {
        "refresh": "<refresh_token>"
    }
    
    Response (200):
    {"message": "Logged out successfully"}
    
    Response (400):
    {"error": "Invalid or expired refresh token"}
    """
    serializer = LogoutSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            result = serializer.save()
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
