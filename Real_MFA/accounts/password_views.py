"""
Password Views - Password reset and forgot password
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .password_serializers import ForgotPasswordSerializer, ResetPasswordSerializer


class ForgotPasswordThrottle(AnonRateThrottle):
    """Rate limit forgot password requests"""
    rate = '100/hour'  # Increased for development


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ForgotPasswordThrottle])
def forgot_password(request):
    """
    Request password reset
    
    POST /api/password/forgot/
    {
        "email": "user@example.com"
    }
    
    Response (200):
    {
        "status": "success",
        "message": "If an account with this email exists...",
        "expires_in": 900
    }
    
    Note: Always returns success to prevent email enumeration
    """
    serializer = ForgotPasswordSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordThrottle(AnonRateThrottle):
    """Rate limit password reset attempts"""
    rate = '100/hour'  # Increased for development


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ResetPasswordThrottle])
def reset_password(request):
    """
    Reset password with OTP code
    
    POST /api/password/reset/
    
    Method 1 - With reset token:
    {
        "reset_token": "token_from_email",
        "otp_code": "123456",
        "new_password": "NewSecurePass123!",
        "new_password2": "NewSecurePass123!"
    }
    
    Method 2 - With user ID:
    {
        "user_id": "uuid",
        "otp_code": "123456",
        "new_password": "NewSecurePass123!",
        "new_password2": "NewSecurePass123!"
    }
    
    Response (200):
    {
        "status": "success",
        "message": "Password reset successfully...",
        "sessions_revoked": 3
    }
    
    Response (400):
    - Invalid/expired token
    - Invalid OTP code
    - Password validation errors
    - Cannot reuse recent passwords
    """
    serializer = ResetPasswordSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
