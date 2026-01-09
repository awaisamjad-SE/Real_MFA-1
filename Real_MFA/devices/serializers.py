"""
Device Serializers - Device verification and management
"""

import json
from rest_framework import serializers
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User
from accounts.redis_utils import redis_client
from accounts.validators import get_location_from_ip
from otp.models import OTP
from otp.utils import hash_otp, get_client_ip
from .models import Device, Session

from rest_framework import serializers
from django.utils import timezone
from .models import Device


class DeviceListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing user devices
    """
    is_current = serializers.SerializerMethodField()
    trust_status = serializers.SerializerMethodField()
    debug_info = serializers.SerializerMethodField()  # Temporary debug field

    class Meta:
        model = Device
        fields = [
            'id',
            'device_name',
            'device_type',
            'browser',
            'browser_version',
            'os',
            'os_version',
            'ip_address',
            'last_ip',
            'country',
            'city',
            'is_verified',
            'is_trusted',
            'verified_at',
            'trust_expires_at',
            'last_used_at',
            'first_used_at',
            'total_logins',
            'is_compromised',
            'risk_score',
            'is_current',
            'trust_status',
            'created_at',
            'user_id',
            'fingerprint_hash',
            'debug_info',  # Temporary debug field
        ]
        read_only_fields = fields

    def get_debug_info(self, obj):
        """Temporary debug info to diagnose is_current issue"""
        request = self.context.get('request')
        if not request:
            return {'error': 'no_request'}
        
        # Check header fingerprint
        header_fingerprint = request.META.get('HTTP_X_DEVICE_FINGERPRINT')
        
        # Get most recent session
        most_recent = Session.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-last_activity').first()
        
        return {
            'header_fingerprint': header_fingerprint,
            'device_fingerprint': obj.fingerprint_hash,
            'header_match': header_fingerprint == obj.fingerprint_hash if header_fingerprint else None,
            'most_recent_session_fingerprint': most_recent.fingerprint_hash if most_recent else None,
            'session_match': most_recent.fingerprint_hash == obj.fingerprint_hash if most_recent else False
        }

    def get_is_current(self, obj):
        """
        Check if this device is the current device
        by matching fingerprint_hash from request header or current session.
        
        Method 1: X-Device-Fingerprint header (if matches a device)
        Method 2: Current session's fingerprint (from authentication)
        Method 3: Most recent active session's fingerprint (fallback)
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        # Method 1: Check X-Device-Fingerprint header
        header_fingerprint = request.META.get('HTTP_X_DEVICE_FINGERPRINT')
        if header_fingerprint and header_fingerprint == obj.fingerprint_hash:
            return True
        
        # Method 2: Check current session (set by SessionValidatedJWTAuthentication)
        current_session = getattr(request, 'current_session', None)
        if current_session and current_session.fingerprint_hash == obj.fingerprint_hash:
            return True
        
        # Method 3: If no header and no current_session, 
        # fall back to most recent active session
        if not header_fingerprint and not current_session:
            try:
                most_recent_session = Session.objects.filter(
                    user=request.user,
                    is_active=True
                ).order_by('-last_activity').first()
                
                if most_recent_session:
                    return obj.fingerprint_hash == most_recent_session.fingerprint_hash
            except Exception:
                pass
        
        # Method 4: If header provided but doesn't match any device, 
        # fall back to session-based detection
        if header_fingerprint:
            header_matches_any_device = Device.objects.filter(
                user=request.user,
                fingerprint_hash=header_fingerprint,
                is_deleted=False
            ).exists()
            
            if not header_matches_any_device:
                session = current_session or Session.objects.filter(
                    user=request.user,
                    is_active=True
                ).order_by('-last_activity').first()
                
                if session:
                    return obj.fingerprint_hash == session.fingerprint_hash
        
        return False

    def get_trust_status(self, obj):
        """
        Return trust status with expiry info
        """
        if not obj.is_trusted:
            return 'not_trusted'

        if obj.trust_expires_at and timezone.now() >= obj.trust_expires_at:
            return 'trust_expired'

        return 'trusted'


class DeviceRevokeSerializer(serializers.Serializer):
    """
    Revoke/remove a device from user's trusted devices
    """
    device_id = serializers.UUIDField()
    
    def validate_device_id(self, value):
        user = self.context.get('request').user
        
        try:
            device = Device.objects.get(
                id=value,
                user=user,
                is_deleted=False
            )
        except Device.DoesNotExist:
            raise serializers.ValidationError("Device not found.")
        
        # Check if trying to revoke current device
        request = self.context.get('request')
        fingerprint = request.META.get('HTTP_X_DEVICE_FINGERPRINT', '')
        if fingerprint:
            from hashlib import sha256
            fingerprint_hash = sha256(fingerprint.encode()).hexdigest()
            if device.fingerprint_hash == fingerprint_hash:
                raise serializers.ValidationError(
                    "Cannot revoke the current device. Use logout instead."
                )
        
        self.device = device
        return value
    
    def save(self):
        device = self.device
        
        # Soft delete the device
        device.soft_delete()
        
        # Mark as not trusted
        device.is_trusted = False
        device.is_verified = False
        device.save(update_fields=['is_trusted', 'is_verified'])
        
        return {
            'status': 'success',
            'message': 'Device revoked successfully',
            'device_id': str(device.id),
            'device_name': device.device_name
        }


class DeviceVerificationSerializer(serializers.Serializer):
    """
    Verify new device with OTP code sent to email
    After verification, device is registered and JWT tokens are issued
    
    Note: fingerprint_hash is required to identify which device is being verified
    (allows multiple devices to verify simultaneously)
    """
    user_id = serializers.UUIDField()
    fingerprint_hash = serializers.CharField(max_length=255)  # Required for multi-device support
    otp_code = serializers.CharField(min_length=6, max_length=6)
    trust_device = serializers.BooleanField(default=False)
    trust_days = serializers.IntegerField(default=30, min_value=1, max_value=90)
    
    def validate(self, attrs):
        user_id = attrs.get('user_id')
        fingerprint_hash = attrs.get('fingerprint_hash')
        otp_code = attrs.get('otp_code')
        request = self.context.get('request')
        
        # Find user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError({"error": "Invalid user."})
        
        # Check for pending device verification (using fingerprint_hash)
        pending_key = f"pending_device_verification:{user_id}:{fingerprint_hash}"
        pending_otp_id = redis_client.get(pending_key)
        
        if not pending_otp_id:
            raise serializers.ValidationError({
                "error": "No pending device verification. Please login again."
            })
        
        # Find OTP record
        try:
            otp = OTP.objects.get(
                id=pending_otp_id,
                user=user,
                purpose='device_verification',
                is_used=False
            )
        except OTP.DoesNotExist:
            raise serializers.ValidationError({
                "error": "OTP expired or invalid. Please login again."
            })
        
        # Check OTP validity
        if not otp.is_valid():
            if otp.attempts >= otp.max_attempts:
                raise serializers.ValidationError({
                    "error": "Too many failed attempts. Please login again."
                })
            if timezone.now() >= otp.expires_at:
                raise serializers.ValidationError({
                    "error": "OTP expired. Please login again."
                })
        
        # Verify OTP code
        if otp.code_hash != hash_otp(otp_code):
            otp.increment_attempts()
            remaining = otp.max_attempts - otp.attempts
            raise serializers.ValidationError({
                "error": f"Invalid OTP code. {remaining} attempts remaining."
            })
        
        attrs['user'] = user
        attrs['otp'] = otp
        attrs['ip_address'] = get_client_ip(request)
        
        return attrs
    
    def save(self):
        user = self.validated_data['user']
        otp = self.validated_data['otp']
        fingerprint_hash = self.validated_data['fingerprint_hash']
        trust_device = self.validated_data.get('trust_device', False)
        trust_days = self.validated_data.get('trust_days', 30)
        ip_address = self.validated_data['ip_address']
        
        # Mark OTP as used
        otp.mark_used()
        
        # Get pending device data from Redis (using fingerprint_hash)
        pending_device_key = f"pending_device_data:{user.id}:{fingerprint_hash}"
        device_data_json = redis_client.get(pending_device_key)
        
        if not device_data_json:
            raise serializers.ValidationError({
                "error": "Device data expired. Please login again."
            })
        
        device_data = json.loads(device_data_json)
        
        # Get location data from IP
        location_data = get_location_from_ip(ip_address)
        
        # Check if device exists (including soft-deleted ones)
        try:
            device = Device.objects.get(
                user=user,
                fingerprint_hash=device_data['fingerprint_hash']
            )
            # If found, restore if soft-deleted and update
            if device.is_deleted:
                device.restore()
            
            # Update device fields
            device.device_name = device_data.get('device_name', '')
            device.device_type = device_data.get('device_type', 'unknown')
            device.browser = device_data.get('browser', '')
            device.os = device_data.get('os', '')
            device.ip_address = location_data['ip']
            device.country = location_data['country']
            device.city = location_data['city']
            device.latitude = location_data['latitude']
            device.longitude = location_data['longitude']
            device.is_verified = True
            device.verified_at = timezone.now()
            device.save()
            created = False
            
        except Device.DoesNotExist:
            # Create new device
            device = Device.objects.create(
                user=user,
                fingerprint_hash=device_data['fingerprint_hash'],
                device_name=device_data.get('device_name', ''),
                device_type=device_data.get('device_type', 'unknown'),
                browser=device_data.get('browser', ''),
                os=device_data.get('os', ''),
                ip_address=location_data['ip'],
                country=location_data['country'],
                city=location_data['city'],
                latitude=location_data['latitude'],
                longitude=location_data['longitude'],
                is_verified=True,
                verified_at=timezone.now(),
                is_deleted=False
            )
            created = True
        
        # Refresh from DB to ensure we have the latest state
        device.refresh_from_db()
        
        # Update device trust and login count
        device.total_logins += 1
        
        if trust_device:
            # Mark as trusted and update login count in single operation
            device.is_trusted = True
            device.trust_expires_at = timezone.now() + timezone.timedelta(days=trust_days)
            device.can_skip_mfa = True
            device.mfa_skip_until = device.trust_expires_at
            device.save(update_fields=['is_trusted', 'trust_expires_at', 'can_skip_mfa', 'mfa_skip_until', 'total_logins'])
        else:
            device.save(update_fields=['total_logins'])
        
        # Update user login info
        user.last_login_ip = location_data['ip']
        user.last_login_at = timezone.now()
        user.last_activity = timezone.now()
        user.save(update_fields=['last_login_ip', 'last_login_at', 'last_activity'])
        
        # Clean up Redis keys (using fingerprint_hash)
        redis_client.delete(pending_device_key)
        redis_client.delete(f"pending_device_verification:{user.id}:{fingerprint_hash}")
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        tokens = {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }
        
        # Create session record
        request = self.context.get('request')
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
        
        Session.objects.create(
            user=user,
            token_jti=str(refresh.access_token.payload.get('jti')),
            fingerprint_hash=device.fingerprint_hash,
            ip_address=location_data['ip'],
            user_agent=user_agent,
            device_name=device.device_name,
            device_type=device.device_type,
            browser=device.browser,
            os=device.os,
            country=location_data['country'],
            city=location_data['city'],
            expires_at=timezone.now() + timezone.timedelta(days=7)
        )
        
        return {
            'status': 'success',
            'message': 'Device verified successfully',
            'user': {
                'id': str(user.id),
                'email': user.email,
                'username': user.username,
                'role': user.role
            },
            'device': {
                'id': str(device.id),
                'name': device.device_name,
                'is_trusted': device.is_trusted,
                'is_new': created
            },
            'tokens': tokens
        }


class SessionListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing user sessions
    """
    is_current = serializers.SerializerMethodField()
    
    class Meta:
        model = Session
        fields = [
            'id',
            'device_name',
            'device_type',
            'browser',
            'os',
            'ip_address',
            'user_agent',
            'country',
            'city',
            'is_active',
            'last_activity',
            'created_at',
            'expires_at',
            'is_current',
        ]
        read_only_fields = fields
    
    def get_is_current(self, obj):
        """Check if this is the current session"""
        request = self.context.get('request')
        if not request:
            return False
        
        # Get current token JTI from request
        current_jti = getattr(request, 'auth', {})
        if hasattr(current_jti, 'payload'):
            return obj.token_jti == current_jti.payload.get('jti')
        return False


class SessionRevokeSerializer(serializers.Serializer):
    """
    Revoke a specific session
    """
    session_id = serializers.UUIDField()
    
    def validate_session_id(self, value):
        user = self.context.get('request').user
        
        try:
            session = Session.objects.get(
                id=value,
                user=user,
                is_active=True
            )
        except Session.DoesNotExist:
            raise serializers.ValidationError("Session not found or already revoked.")
        
        # Check if trying to revoke current session
        request = self.context.get('request')
        current_jti = getattr(request, 'auth', {})
        if hasattr(current_jti, 'payload') and session.token_jti == current_jti.payload.get('jti'):
            raise serializers.ValidationError(
                "Cannot revoke the current session. Use logout instead."
            )
        
        self.session = session
        return value
    
    def save(self):
        session = self.session
        session.revoke(reason='user_revoked')
        
        return {
            'status': 'success',
            'message': 'Session revoked successfully',
            'session_id': str(session.id),
            'device_name': session.device_name or 'Unknown'
        }


class RevokeAllSessionsSerializer(serializers.Serializer):
    """
    Revoke all sessions except the current one
    """
    include_current = serializers.BooleanField(default=False)
    
    def save(self):
        user = self.context.get('request').user
        request = self.context.get('request')
        include_current = self.validated_data.get('include_current', False)
        
        # Get current session ID to exclude (if not revoking current)
        exclude_session_id = None
        if not include_current:
            current_jti = getattr(request, 'auth', {})
            if hasattr(current_jti, 'payload'):
                jti = current_jti.payload.get('jti')
                current_session = Session.objects.filter(
                    user=user,
                    token_jti=jti,
                    is_active=True
                ).first()
                if current_session:
                    exclude_session_id = current_session.id
        
        revoked_count = Session.revoke_all_for_user(
            user=user,
            reason='user_revoked',
            exclude_session_id=exclude_session_id
        )
        
        return {
            'status': 'success',
            'message': f'{revoked_count} session(s) revoked successfully',
            'revoked_count': revoked_count,
            'current_session_revoked': include_current
        }
