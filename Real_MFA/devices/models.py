# ============================================================================
# DEVICES APP - models.py
# Device management and tracking
# ============================================================================

from django.db import models
from django.utils import timezone
import uuid
from accounts.models import User


# ---------------------------
# Abstract Base Models
# ---------------------------
class TimeStampedModel(models.Model):
    """Abstract model with timestamp fields"""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """Abstract model with soft delete functionality"""
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        """Soft delete the instance"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        """Restore soft deleted instance"""
        self.is_deleted = False
        self.deleted_at = None
        self.save()


# ---------------------------
# Device Model
# ---------------------------
class Device(TimeStampedModel, SoftDeleteModel):
    """
    Track user devices for device-based authentication
    Security: Device fingerprinting, verification, and trust management
    """
    
    DEVICE_TYPE_CHOICES = [
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
        ('desktop', 'Desktop'),
        ('unknown', 'Unknown'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    
    # Device Identification
    fingerprint_hash = models.CharField(max_length=255, db_index=True)
    device_name = models.CharField(max_length=255, blank=True)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPE_CHOICES, default='unknown')
    
    # Browser & OS Information
    browser = models.CharField(max_length=100, blank=True)
    browser_version = models.CharField(max_length=50, blank=True)
    os = models.CharField(max_length=100, blank=True)
    os_version = models.CharField(max_length=50, blank=True)
    
    # Network Information
    ip_address = models.GenericIPAddressField()
    last_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Location (optional - requires GeoIP)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Trust & Verification
    is_verified = models.BooleanField(default=False, db_index=True)
    is_trusted = models.BooleanField(default=False, db_index=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    trust_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Activity Tracking
    last_used_at = models.DateTimeField(auto_now=True, db_index=True)
    first_used_at = models.DateTimeField(auto_now_add=True)
    total_logins = models.PositiveIntegerField(default=0)
    
    # Anomaly & Risk Detection
    is_compromised = models.BooleanField(default=False, db_index=True)
    risk_score = models.PositiveIntegerField(default=0)  # 0-100
    last_risk_assessment = models.DateTimeField(null=True, blank=True)
    
    # MFA Bypass
    can_skip_mfa = models.BooleanField(default=False)
    mfa_skip_until = models.DateTimeField(null=True, blank=True)
    
    # Security Notes
    security_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'devices'
        verbose_name = 'Device'
        verbose_name_plural = 'Devices'
        unique_together = [['user', 'fingerprint_hash']]
        indexes = [
            models.Index(fields=['user', 'is_trusted', 'is_deleted']),
            models.Index(fields=['user', 'is_verified']),
            models.Index(fields=['fingerprint_hash']),
            models.Index(fields=['last_used_at']),
            models.Index(fields=['is_compromised']),
            models.Index(fields=['risk_score']),
        ]
    
    def __str__(self):
        return f"{self.device_name or 'Unknown Device'} - {self.user.email}"
    
    def mark_verified(self):
        """Mark device as verified"""
        self.is_verified = True
        self.verified_at = timezone.now()
        self.save(update_fields=['is_verified', 'verified_at'])
    
    def mark_trusted(self, days=30):
        """Mark device as trusted for specified days"""
        self.is_trusted = True
        self.trust_expires_at = timezone.now() + timezone.timedelta(days=days)
        self.can_skip_mfa = True
        self.mfa_skip_until = self.trust_expires_at
        self.save(update_fields=['is_trusted', 'trust_expires_at', 'can_skip_mfa', 'mfa_skip_until'])
    
    def revoke_trust(self):
        """Revoke device trust"""
        self.is_trusted = False
        self.trust_expires_at = None
        self.can_skip_mfa = False
        self.mfa_skip_until = None
        self.save(update_fields=['is_trusted', 'trust_expires_at', 'can_skip_mfa', 'mfa_skip_until'])
    
    def mark_compromised(self):
        """Mark device as compromised"""
        self.is_compromised = True
        self.is_trusted = False
        self.can_skip_mfa = False
        self.risk_score = 100
        self.save(update_fields=['is_compromised', 'is_trusted', 'can_skip_mfa', 'risk_score'])
    
    def can_skip_mfa_now(self):
        """Check if device can skip MFA at current time"""
        if not self.can_skip_mfa or self.is_compromised:
            return False
        if self.mfa_skip_until and timezone.now() > self.mfa_skip_until:
            self.can_skip_mfa = False
            self.save(update_fields=['can_skip_mfa'])
            return False
        return True
    
    def is_trust_expired(self):
        """Check if device trust has expired"""
        if not self.is_trusted:
            return False
        if self.trust_expires_at and timezone.now() > self.trust_expires_at:
            self.revoke_trust()
            return True
        return False


# ---------------------------
# TrustedDevice Model
# ---------------------------
class TrustedDevice(TimeStampedModel, SoftDeleteModel):
    """
    Devices trusted by user to skip MFA for a period
    Users can manage which devices should skip MFA verification
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trusted_devices')
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='trust_records')
    
    # Trust Details
    device_name = models.CharField(max_length=255, blank=True)
    trust_days = models.PositiveIntegerField(default=30)  # Days to trust this device
    
    # Status
    is_trusted = models.BooleanField(default=True)
    trusted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    
    # Activity
    last_verified_at = models.DateTimeField(null=True, blank=True)
    times_skipped_mfa = models.PositiveIntegerField(default=0)
    
    # Revocation
    revoked_at = models.DateTimeField(null=True, blank=True)
    revocation_reason = models.CharField(max_length=255, blank=True)
    
    class Meta:
        db_table = 'trusted_devices'
        verbose_name = 'Trusted Device'
        verbose_name_plural = 'Trusted Devices'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_trusted']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Trusted device {self.device_name} for {self.user.email}"


# ---------------------------
# Session Model
# ---------------------------
class Session(TimeStampedModel, SoftDeleteModel):
    """
    Track user login sessions (per user, not per device)
    Each login creates a new session with JWT token reference
    Allows users to see active sessions and revoke them
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    
    # Session Token Reference (JWT jti)
    token_jti = models.CharField(max_length=255, unique=True, db_index=True)
    
    # Device fingerprint - used to identify which device this session belongs to
    fingerprint_hash = models.CharField(max_length=255, db_index=True, blank=True)
    
    # Session Details
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Device info (stored as text, not FK - for display purposes only)
    device_name = models.CharField(max_length=255, blank=True)
    device_type = models.CharField(max_length=50, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)
    
    # Location (optional)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    # Revocation
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_reason = models.CharField(
        max_length=50,
        choices=[
            ('user_logout', 'User Logout'),
            ('user_revoked', 'User Revoked'),
            ('password_changed', 'Password Changed'),
            ('password_reset', 'Password Reset'),
            ('admin_revoked', 'Admin Revoked'),
            ('security_concern', 'Security Concern'),
            ('session_expired', 'Session Expired'),
        ],
        blank=True
    )
    
    class Meta:
        db_table = 'sessions'
        verbose_name = 'Session'
        verbose_name_plural = 'Sessions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['token_jti']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Session for {self.user.email} - {self.device_name or 'Unknown Device'}"
    
    def revoke(self, reason='user_revoked'):
        """Revoke this session and blacklist the token"""
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
        
        self.is_active = False
        self.revoked_at = timezone.now()
        self.revoked_reason = reason
        self.save(update_fields=['is_active', 'revoked_at', 'revoked_reason'])
        
        # Blacklist the token
        try:
            outstanding_token = OutstandingToken.objects.get(jti=self.token_jti)
            BlacklistedToken.objects.get_or_create(token=outstanding_token)
        except OutstandingToken.DoesNotExist:
            pass
    
    @classmethod
    def revoke_all_for_user(cls, user, reason='user_revoked', exclude_session_id=None):
        """Revoke all active sessions for a user"""
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
        
        sessions = cls.objects.filter(user=user, is_active=True)
        if exclude_session_id:
            sessions = sessions.exclude(id=exclude_session_id)
        
        revoked_count = 0
        for session in sessions:
            session.is_active = False
            session.revoked_at = timezone.now()
            session.revoked_reason = reason
            session.save(update_fields=['is_active', 'revoked_at', 'revoked_reason'])
            
            # Blacklist the token
            try:
                outstanding_token = OutstandingToken.objects.get(jti=session.token_jti)
                BlacklistedToken.objects.get_or_create(token=outstanding_token)
            except OutstandingToken.DoesNotExist:
                pass
            
            revoked_count += 1
        
        return revoked_count
