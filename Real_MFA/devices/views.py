"""
Device Views - Device verification and management
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Device, Session
from .serializers import (
    DeviceVerificationSerializer,
    DeviceListSerializer,
    DeviceRevokeSerializer,
    SessionListSerializer,
    SessionRevokeSerializer,
    RevokeAllSessionsSerializer
)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_device(request):
    """
    Verify new device with OTP code sent to email
    
    POST /api/devices/verify/
    {
        "user_id": "uuid",
        "fingerprint_hash": "abc123...",  // Required - identifies which device
        "otp_code": "123456",
        "trust_device": true,
        "trust_days": 30
    }
    
    Note: fingerprint_hash is returned from login response when device verification
    is required. This allows multiple devices to verify simultaneously.
    
    Response (200):
    {
        "status": "success",
        "message": "Device verified successfully",
        "user": {"id": "uuid", "email": "...", "username": "...", "role": "user"},
        "device": {"id": "uuid", "name": "...", "is_trusted": true, "is_new": true},
        "tokens": {"access": "...", "refresh": "..."}
    }
    
    Response (400):
    - Invalid OTP code
    - OTP expired
    - Too many failed attempts
    - No pending verification
    """
    serializer = DeviceVerificationSerializer(
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


class DeviceListView(APIView):
    """
    List all user devices
    
    GET /api/devices/
    
    Response (200):
    {
        "count": 2,
        "devices": [
            {
                "id": "uuid",
                "device_name": "Chrome on Windows",
                "device_type": "desktop",
                "browser": "Chrome",
                "os": "Windows",
                "ip_address": "192.168.1.1",
                "is_verified": true,
                "is_trusted": true,
                "is_current": true,
                "trust_status": "trusted",
                "last_used_at": "2024-01-15T10:30:00Z",
                ...
            },
            ...
        ]
    }
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        devices = Device.objects.filter(
            user=request.user,
            is_deleted=False
        ).order_by('-last_used_at')
        
        serializer = DeviceListSerializer(
            devices,
            many=True,
            context={'request': request}
        )
        
        
        return Response({
            'count': devices.count(),
            'devices': serializer.data
        }, status=status.HTTP_200_OK)


class DeviceRevokeView(APIView):
    """
    Revoke a specific device
    
    POST /api/devices/{device_id}/revoke/
    
    Response (200):
    {
        "status": "success",
        "message": "Device revoked successfully",
        "device_id": "uuid",
        "device_name": "Chrome on Windows"
    }
    
    Response (400):
    - Device not found
    - Cannot revoke current device
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, device_id):
        serializer = DeviceRevokeSerializer(
            data={'device_id': device_id},
            context={'request': request}
        )
        
        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SessionListView(APIView):
    """
    List all active sessions for the user
    
    GET /api/devices/sessions/
    
    Response (200):
    {
        "count": 2,
        "sessions": [
            {
                "id": "uuid",
                "device_name": "Chrome on Windows",
                "device_type": "desktop",
                "ip_address": "192.168.1.1",
                "country": "US",
                "city": "New York",
                "is_active": true,
                "is_current": true,
                "last_activity": "2024-01-15T10:30:00Z",
                "created_at": "2024-01-15T08:00:00Z",
                "expires_at": "2024-01-22T08:00:00Z"
            },
            ...
        ]
    }
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        sessions = Session.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-last_activity')
        
        serializer = SessionListSerializer(
            sessions,
            many=True,
            context={'request': request}
        )
        
        return Response({
            'count': sessions.count(),
            'sessions': serializer.data
        }, status=status.HTTP_200_OK)


class SessionRevokeView(APIView):
    """
    Revoke a specific session
    
    POST /api/devices/sessions/{session_id}/revoke/
    
    Response (200):
    {
        "status": "success",
        "message": "Session revoked successfully",
        "session_id": "uuid",
        "device_name": "Chrome on Windows"
    }
    
    Response (400):
    - Session not found
    - Cannot revoke current session
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, session_id):
        serializer = SessionRevokeSerializer(
            data={'session_id': session_id},
            context={'request': request}
        )
        
        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RevokeAllSessionsView(APIView):
    """
    Revoke all sessions except the current one (or all including current)
    
    POST /api/devices/sessions/revoke-all/
    {
        "include_current": false  // Optional, default false
    }
    
    Response (200):
    {
        "status": "success",
        "message": "3 session(s) revoked successfully",
        "revoked_count": 3,
        "current_session_revoked": false
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = RevokeAllSessionsSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
