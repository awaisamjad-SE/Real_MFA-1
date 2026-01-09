"""
Profile Views - User profile and account management
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
import logging

from .models import User, Profile
from .profile_serializers import (
    UserProfileSerializer,
    UpdateProfileSerializer,
    AccountDetailsSerializer,
    ChangePasswordSerializer,
)

logger = logging.getLogger(__name__)


# ============================================================================
# PROFILE VIEWS
# ============================================================================

class ProfileMeView(APIView):
    """
    Get or update current user's profile.
    
    GET /api/profile/me/ - Get profile
    PUT /api/profile/me/ - Update profile
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user profile"""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        """Update current user profile"""
        serializer = UpdateProfileSerializer(
            request.user,
            data=request.data,
            context={'request': request},
            partial=True
        )
        if serializer.is_valid():
            serializer.update(request.user, serializer.validated_data)
            # Return updated profile
            return Response({
                "message": "Profile updated successfully",
                "profile": UserProfileSerializer(request.user).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AccountDetailsView(APIView):
    """
    Get account security details.
    
    GET /api/profile/account/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = AccountDetailsSerializer(request.user)
        return Response(serializer.data)


class ChangePasswordView(APIView):
    """
    Change password for authenticated user.
    
    POST /api/profile/change-password/
    {
        "current_password": "old_password",
        "new_password": "new_password",
        "new_password2": "new_password"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            result = serializer.save()
            return Response(result)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
