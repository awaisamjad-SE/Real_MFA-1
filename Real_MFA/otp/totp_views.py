"""
TOTP Views - TOTP/MFA management endpoints
"""

import pyotp
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from hashlib import sha256
from django.utils import timezone

from .models import TOTPDevice, BackupCode
from audits_logs.models import AuditLog

User = get_user_model()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setup_totp(request):
    """
    Setup TOTP/MFA for user
    
    POST /api/totp/setup/
    
    Response (200):
    {
        "secret": "BASE32SECRET",
        "qr_uri": "otpauth://totp/...",
        "message": "Scan QR code with authenticator app"
    }
    
    Response (400):
    - TOTP already enabled
    """
    user = request.user
    
    # Check if TOTP already exists and is verified
    if hasattr(user, 'totp_device') and user.totp_device.is_verified:
        return Response(
            {"error": "TOTP is already enabled. Disable it first to set up new device."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Generate new secret
    secret = pyotp.random_base32()
    
    # Create or update TOTP device
    totp_device, created = TOTPDevice.objects.update_or_create(
        user=user,
        defaults={
            'secret': secret,
            'is_verified': False,
            'verified_at': None,
        }
    )
    
    # Generate QR code URI
    totp = pyotp.TOTP(secret)
    qr_uri = totp.provisioning_uri(
        name=user.email,
        issuer_name='Real MFA'
    )
    
    # Log action
    AuditLog.objects.create(
        user=user,
        event_type='mfa_method_added',
        severity='low',
        description='TOTP setup initiated',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        metadata={'setup_type': 'new' if created else 'reset'}
    )
    
    return Response({
        "secret": secret,
        "qr_uri": qr_uri,
        "message": "Scan QR code with your authenticator app (Google Authenticator, Authy, etc.)"
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_totp(request):
    """
    Verify TOTP code to enable MFA
    
    POST /api/totp/verify/
    {
        "code": "123456"
    }
    
    Response (200):
    {
        "message": "TOTP verified successfully",
        "backup_codes": ["A1B2-C3D4", "E5F6-G7H8", ...]
    }
    
    Response (400):
    - Invalid code
    - TOTP not setup
    - Already verified
    """
    user = request.user
    code = request.data.get('code')
    
    if not code:
        return Response(
            {"error": "TOTP code is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if TOTP device exists
    if not hasattr(user, 'totp_device'):
        return Response(
            {"error": "TOTP is not set up. Please set up TOTP first."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    totp_device = user.totp_device
    
    # Check if already verified
    if totp_device.is_verified:
        return Response(
            {"error": "TOTP is already verified"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify code
    totp = pyotp.TOTP(totp_device.secret)
    if not totp.verify(code, valid_window=1):
        totp_device.failed_attempts += 1
        totp_device.save(update_fields=['failed_attempts'])
        
        return Response(
            {"error": "Invalid TOTP code. Please try again."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Mark as verified
    totp_device.is_verified = True
    totp_device.verified_at = timezone.now()
    totp_device.backup_codes_generated_at = timezone.now()
    totp_device.failed_attempts = 0
    totp_device.save()
    
    # Enable MFA for user
    user.mfa_enabled = True
    user.mfa_method = 'totp'
    user.save(update_fields=['mfa_enabled', 'mfa_method'])
    
    # Generate backup codes
    backup_codes_plain = []
    for _ in range(10):
        code_plain = f"{pyotp.random_base32()[:4]}-{pyotp.random_base32()[:4]}"
        code_hash = sha256(code_plain.upper().encode()).hexdigest()
        
        BackupCode.objects.create(
            user=user,
            code_hash=code_hash
        )
        backup_codes_plain.append(code_plain)
    
    # Log action
    AuditLog.objects.create(
        user=user,
        event_type='mfa_enabled',
        severity='low',
        description='TOTP verified and enabled successfully',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        metadata={'backup_codes_count': 10, 'mfa_method': 'totp'}
    )
    
    return Response({
        "message": "TOTP verified successfully. MFA is now enabled.",
        "backup_codes": backup_codes_plain,
        "warning": "Save these backup codes in a secure location. They can only be used once."
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def disable_totp(request):
    """
    Disable TOTP/MFA
    
    POST /api/totp/disable/
    {
        "password": "current_password"
    }
    
    Response (200):
    {
        "message": "TOTP disabled successfully"
    }
    
    Response (400):
    - Wrong password
    - TOTP not enabled
    """
    user = request.user
    password = request.data.get('password')
    
    if not password:
        return Response(
            {"error": "Password is required to disable TOTP"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify password
    if not user.check_password(password):
        return Response(
            {"error": "Invalid password"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if TOTP exists
    if not hasattr(user, 'totp_device'):
        return Response(
            {"error": "TOTP is not enabled"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Delete TOTP device and backup codes
    user.totp_device.delete()
    BackupCode.objects.filter(user=user).delete()
    
    # Disable MFA
    user.mfa_enabled = False
    user.mfa_method = 'totp'
    user.save(update_fields=['mfa_enabled', 'mfa_method'])
    
    # Log action
    AuditLog.objects.create(
        user=user,
        event_type='mfa_disabled',
        severity='medium',
        description='TOTP disabled by user',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        metadata={'reason': 'user_requested', 'mfa_method': 'totp'}
    )
    
    return Response({
        "message": "TOTP disabled successfully. MFA is now disabled."
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def regenerate_backup_codes(request):
    """
    Regenerate backup codes
    
    POST /api/totp/regenerate-backup-codes/
    {
        "password": "current_password"
    }
    
    Response (200):
    {
        "backup_codes": ["A1B2-C3D4", "E5F6-G7H8", ...],
        "message": "Backup codes regenerated successfully"
    }
    
    Response (400):
    - Wrong password
    - TOTP not enabled
    """
    user = request.user
    password = request.data.get('password')
    
    if not password:
        return Response(
            {"error": "Password is required to regenerate backup codes"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify password
    if not user.check_password(password):
        return Response(
            {"error": "Invalid password"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if TOTP is enabled
    if not hasattr(user, 'totp_device') or not user.totp_device.is_verified:
        return Response(
            {"error": "TOTP is not enabled"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Delete old backup codes
    BackupCode.objects.filter(user=user).delete()
    
    # Generate new backup codes
    backup_codes_plain = []
    for _ in range(10):
        code_plain = f"{pyotp.random_base32()[:4]}-{pyotp.random_base32()[:4]}"
        code_hash = sha256(code_plain.upper().encode()).hexdigest()
        
        BackupCode.objects.create(
            user=user,
            code_hash=code_hash
        )
        backup_codes_plain.append(code_plain)
    
    # Update timestamp
    user.totp_device.backup_codes_generated_at = timezone.now()
    user.totp_device.save(update_fields=['backup_codes_generated_at'])
    
    # Log action
    AuditLog.objects.create(
        user=user,
        event_type='mfa_method_added',
        severity='low',
        description='Backup codes regenerated',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        metadata={'backup_codes_count': 10, 'action': 'regenerate'}
    )
    
    return Response({
        "backup_codes": backup_codes_plain,
        "message": "Backup codes regenerated successfully",
        "warning": "Old backup codes are no longer valid. Save these new codes in a secure location."
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mfa_status(request):
    """
    Get MFA status
    
    GET /api/totp/status/
    
    Response (200):
    {
        "mfa_enabled": true,
        "mfa_method": "totp",
        "totp_verified": true,
        "backup_codes_remaining": 8,
        "last_used": "2026-01-08T12:00:00Z"
    }
    """
    user = request.user
    
    status_data = {
        "mfa_enabled": user.mfa_enabled,
        "mfa_method": user.mfa_method,
        "totp_verified": False,
        "backup_codes_remaining": 0,
        "last_used": None
    }
    
    if hasattr(user, 'totp_device'):
        totp_device = user.totp_device
        status_data.update({
            "totp_verified": totp_device.is_verified,
            "backup_codes_remaining": BackupCode.objects.filter(user=user, is_used=False).count(),
            "last_used": totp_device.last_used_at,
            "total_verifications": totp_device.total_verifications,
            "verified_at": totp_device.verified_at
        })
    
    return Response(status_data, status=status.HTTP_200_OK)
