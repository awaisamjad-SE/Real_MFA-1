"""
Admin Serializers - Comprehensive user data for admin dashboard
"""

from rest_framework import serializers
from django.utils import timezone
from .models import User, Profile, PasswordHistory
from devices.models import Device, Session
from otp.models import OTP, TOTPDevice, BackupCode
from notification.models import EmailNotification, SMSNotification


# =============================================================================
# NESTED SERIALIZERS - For detailed user data
# =============================================================================

class AdminProfileSerializer(serializers.ModelSerializer):
    """Profile details for admin view"""
    class Meta:
        model = Profile
        fields = [
            'phone_number', 'phone_verified', 'date_of_birth', 'avatar',
            'address_line1', 'address_line2', 'city', 'state', 'country', 'postal_code',
            'timezone', 'language', 'profile_visibility',
            'created_at', 'updated_at'
        ]


class AdminDeviceSerializer(serializers.ModelSerializer):
    """Device details for admin view"""
    trust_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Device
        fields = [
            'id', 'fingerprint_hash', 'device_name', 'device_type',
            'browser', 'browser_version', 'os', 'os_version',
            'ip_address', 'last_ip', 'country', 'city',
            'is_verified', 'is_trusted', 'verified_at', 'trust_expires_at',
            'last_used_at', 'first_used_at', 'total_logins',
            'is_compromised', 'risk_score', 'is_deleted', 'deleted_at',
            'trust_status', 'created_at', 'updated_at'
        ]
    
    def get_trust_status(self, obj):
        if obj.is_deleted:
            return 'deleted'
        if obj.is_compromised:
            return 'compromised'
        if not obj.is_trusted:
            return 'not_trusted'
        if obj.trust_expires_at and timezone.now() >= obj.trust_expires_at:
            return 'trust_expired'
        return 'trusted'


class AdminSessionSerializer(serializers.ModelSerializer):
    """Session details for admin view"""
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = Session
        fields = [
            'id', 'token_jti', 'fingerprint_hash',
            'ip_address', 'user_agent',
            'device_name', 'device_type', 'browser', 'os',
            'country', 'city',
            'is_active', 'expires_at', 'last_activity',
            'revoked_at', 'revoked_reason',
            'duration', 'created_at', 'updated_at'
        ]
    
    def get_duration(self, obj):
        """Get session duration in seconds"""
        if obj.revoked_at:
            return (obj.revoked_at - obj.created_at).total_seconds()
        return (timezone.now() - obj.created_at).total_seconds()


class AdminOTPSerializer(serializers.ModelSerializer):
    """OTP history for admin view"""
    class Meta:
        model = OTP
        fields = [
            'id', 'purpose', 'target',
            'attempts', 'max_attempts', 'ip_address',
            'is_used', 'used_at', 'expires_at',
            'created_at'
        ]


class AdminTOTPDeviceSerializer(serializers.ModelSerializer):
    """TOTP device details for admin view (secret hidden)"""
    class Meta:
        model = TOTPDevice
        fields = [
            'id', 'is_verified', 'verified_at',
            'last_used_at', 'total_verifications', 'failed_attempts',
            'backup_codes_generated_at', 'created_at', 'updated_at'
        ]


class AdminBackupCodeSerializer(serializers.ModelSerializer):
    """Backup code details for admin view (code hidden)"""
    class Meta:
        model = BackupCode
        fields = [
            'id', 'is_used', 'used_at', 'used_from_ip', 'created_at'
        ]


class AdminEmailNotificationSerializer(serializers.ModelSerializer):
    """Email notification history for admin view"""
    class Meta:
        model = EmailNotification
        fields = [
            'id', 'to_email', 'subject', 'email_type', 'template_name',
            'status', 'sent_at', 'opened_at', 'clicked_at',
            'error_message', 'retry_count', 'provider',
            'created_at'
        ]


class AdminSMSNotificationSerializer(serializers.ModelSerializer):
    """SMS notification history for admin view"""
    class Meta:
        model = SMSNotification
        fields = [
            'id', 'phone_number', 'sms_type',
            'status', 'sent_at', 'delivered_at',
            'error_message', 'retry_count', 'provider',
            'created_at'
        ]


class AdminPasswordHistorySerializer(serializers.ModelSerializer):
    """Password history for admin view (hash hidden)"""
    class Meta:
        model = PasswordHistory
        fields = ['id', 'changed_from_ip', 'created_at']


# =============================================================================
# MAIN ADMIN SERIALIZERS
# =============================================================================

class AdminUserListSerializer(serializers.ModelSerializer):
    """
    User list for admin - summary view
    """
    devices_count = serializers.SerializerMethodField()
    active_sessions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'role',
            'is_active', 'is_staff', 'is_superuser',
            'email_verified', 'email_verified_at',
            'mfa_enabled', 'mfa_method',
            'last_login_ip', 'last_login_at', 'last_activity',
            'failed_login_attempts', 'account_locked_until',
            'is_deleted', 'deleted_at',
            'devices_count', 'active_sessions_count',
            'created_at', 'updated_at'
        ]
    
    def get_devices_count(self, obj):
        return obj.devices.filter(is_deleted=False).count()
    
    def get_active_sessions_count(self, obj):
        return obj.sessions.filter(is_active=True).count()


class AdminUserDetailSerializer(serializers.ModelSerializer):
    """
    Comprehensive user detail for admin - includes ALL related data
    """
    # Related data
    profile = AdminProfileSerializer(read_only=True)
    devices = serializers.SerializerMethodField()
    sessions = serializers.SerializerMethodField()
    otps = serializers.SerializerMethodField()
    totp_device = AdminTOTPDeviceSerializer(read_only=True)
    backup_codes = serializers.SerializerMethodField()
    email_notifications = serializers.SerializerMethodField()
    sms_notifications = serializers.SerializerMethodField()
    password_history = serializers.SerializerMethodField()
    
    # Computed fields
    devices_count = serializers.SerializerMethodField()
    active_sessions_count = serializers.SerializerMethodField()
    backup_codes_remaining = serializers.SerializerMethodField()
    account_status = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            # User fields
            'id', 'email', 'username', 'first_name', 'last_name', 'role',
            'is_active', 'is_staff', 'is_superuser',
            'email_verified', 'email_verified_at',
            'mfa_enabled', 'mfa_method',
            'last_login_ip', 'last_login_at', 'last_activity',
            'failed_login_attempts', 'account_locked_until',
            'password_changed_at', 'require_password_change',
            'is_deleted', 'deleted_at',
            'created_at', 'updated_at',
            
            # Computed fields
            'devices_count', 'active_sessions_count', 'backup_codes_remaining',
            'account_status',
            
            # Related data
            'profile', 'devices', 'sessions', 'otps', 
            'totp_device', 'backup_codes',
            'email_notifications', 'sms_notifications',
            'password_history'
        ]
    
    def get_devices(self, obj):
        devices = obj.devices.all().order_by('-last_used_at')
        return AdminDeviceSerializer(devices, many=True).data
    
    def get_sessions(self, obj):
        sessions = obj.sessions.all().order_by('-created_at')[:50]  # Last 50 sessions
        return AdminSessionSerializer(sessions, many=True).data
    
    def get_otps(self, obj):
        otps = obj.otps.all().order_by('-created_at')[:20]  # Last 20 OTPs
        return AdminOTPSerializer(otps, many=True).data
    
    def get_backup_codes(self, obj):
        codes = obj.backup_codes.all().order_by('-created_at')
        return AdminBackupCodeSerializer(codes, many=True).data
    
    def get_email_notifications(self, obj):
        notifications = obj.email_notifications.all().order_by('-created_at')[:50]
        return AdminEmailNotificationSerializer(notifications, many=True).data
    
    def get_sms_notifications(self, obj):
        notifications = obj.sms_notifications.all().order_by('-created_at')[:50]
        return AdminSMSNotificationSerializer(notifications, many=True).data
    
    def get_password_history(self, obj):
        history = obj.password_history.all().order_by('-created_at')[:10]
        return AdminPasswordHistorySerializer(history, many=True).data
    
    def get_devices_count(self, obj):
        return obj.devices.filter(is_deleted=False).count()
    
    def get_active_sessions_count(self, obj):
        return obj.sessions.filter(is_active=True).count()
    
    def get_backup_codes_remaining(self, obj):
        return obj.backup_codes.filter(is_used=False).count()
    
    def get_account_status(self, obj):
        if obj.is_deleted:
            return 'deleted'
        if obj.is_account_locked():
            return 'locked'
        if not obj.email_verified:
            return 'unverified'
        if not obj.is_active:
            return 'inactive'
        return 'active'
