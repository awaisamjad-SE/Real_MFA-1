"""
Registration Views - User registration with email verification
Rate limited: 2-3 registrations per minute per IP/device
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from .serializers import RegisterSerializer
import logging

logger = logging.getLogger(__name__)


class RegistrationThrottle(UserRateThrottle):
    """Rate limit registrations: 2 per minute per IP"""
    scope = 'registration'
    THROTTLE_RATES = {
        'registration': '2/min'  # 2 registrations per minute per IP
    }


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([RegistrationThrottle])
def register(request):
    """
    Register new user with email verification
    POST /api/auth/register/
    
    Rate limit: 2 registrations per minute per IP
    
    Request:
    {
      "username": "john",
      "email": "john@example.com",
      "password": "SecurePass123!",
      "password2": "SecurePass123!",
      "role": "user",
      "phone_number": "+1234567890",
      "device": {
        "fingerprint_hash": "abc123xyz...",
        "device_name": "iPhone 14",
        "device_type": "mobile",
        "browser": "Safari",
        "os": "iOS"
      }
    }
    
    Response (201):
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "john@example.com",
      "username": "john",
      "role": "user",
      "created_at": "2024-01-15T10:30:00Z",
      "message": "Registration successful. Check your email to verify.",
      "device": {
        "id": "device-uuid",
        "device_name": "iPhone 14",
        "device_type": "mobile"
      }
    }
    """
    serializer = RegisterSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Get device data
        device = user.devices.first()
        
        return Response({
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "role": user.role,
            "created_at": user.created_at.isoformat(),
            "message": "Registration successful. Check your email to verify.",
            "device": {
                "id": str(device.id) if device else None,
                "device_name": device.device_name if device else None,
                "device_type": device.device_type if device else None
            }
        }, status=status.HTTP_201_CREATED)
    
    logger.warning(f"Registration failed: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """
    Verify email with token from link
    POST /api/auth/verify-email/
    
    Request:
    {
      "uid": "base64_encoded_user_id",
      "token": "verification_token"
    }
    
    Response (200):
    {
      "message": "Email verified successfully. You can now login.",
      "email": "john@example.com"
    }
    """
    from .verification_serializers import EmailVerificationSerializer
    
    serializer = EmailVerificationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {
                "message": "Email verified successfully. You can now login.",
                "email": user.email
            },
            status=status.HTTP_200_OK
        )
    
    logger.warning(f"Email verification failed: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification_email(request):
    """
    Resend verification email with rate limiting
    POST /api/auth/resend-verification-email/
    
    Rate limits:
    - Max 4 resends per hour per user
    - 60 second cooldown between resends
    
    Request:
    {
      "email": "john@example.com"
    }
    
    Response (200):
    {
      "message": "Verification email resent.",
      "email": "john@example.com",
      "remaining": 3
    }
    """
    from .verification_serializers import ResendVerificationEmailSerializer
    
    serializer = ResendVerificationEmailSerializer(data=request.data)
    if serializer.is_valid():
        try:
            result = serializer.save()
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Resend email failed: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    logger.warning(f"Resend verification failed: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
