"""
Email Verification Views - Token validation and email verification endpoints
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .verification_serializers import EmailVerificationSerializer, ResendVerificationEmailSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """
    Verify email with token from link
    POST /api/auth/verify-email/
    Body: {"uid": "base64_user_id", "token": "token"}
    """
    serializer = EmailVerificationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "Email verified successfully. You can now login."},
            status=status.HTTP_200_OK
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification_email(request):
    """
    Resend verification email with rate limiting
    POST /api/auth/resend-verification-email/
    Body: {"email": "user@example.com"}
    Rate limits: 4 resends/hour, 60sec cooldown
    """
    serializer = ResendVerificationEmailSerializer(data=request.data)
    if serializer.is_valid():
        try:
            result = serializer.save()
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
