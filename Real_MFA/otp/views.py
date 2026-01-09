"""
OTP Views - Resend OTP endpoints
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .serializers import ResendDeviceOTPSerializer


class ResendOTPRateThrottle(AnonRateThrottle):
    """Rate limit: 3 OTP resend requests per minute per IP"""
    rate = '3/minute'


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_device_otp(request):
    """
    Resend OTP for device verification
    
    POST /api/otp/resend-device/
    {
        "user_id": "uuid",
        "fingerprint_hash": "abc123..."
    }
    
    Response (200):
    {
        "message": "OTP resent successfully",
        "email_hint": "use***@example.com",
        "expires_at": "2026-01-08T12:30:00Z",
        "remaining_resends": 2
    }
    
    Response (400):
    - No pending device verification
    - Cooldown not expired (wait X seconds)
    - Too many OTP requests
    
    Response (429):
    - Rate limit exceeded
    """
    # Apply rate limiting
    throttle = ResendOTPRateThrottle()
    if not throttle.allow_request(request, None):
        return Response(
            {
                "error": "Too many OTP requests. Please try again later.",
                "retry_after": throttle.wait()
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    serializer = ResendDeviceOTPSerializer(
        data=request.data,
        context={'request': request}
    )
    
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
