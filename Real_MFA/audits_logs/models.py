# ============================================================================
# AUDIT LOG APP - models.py
# Comprehensive audit logging for sessions, devices, and security events
# ============================================================================

from django.db import models
from django.utils import timezone
import uuid

# Import from accounts app
from accounts.models import TimeStampedModel


# ---------------------------
# Base Audit Model
# ---------------------------
class BaseAuditLog(TimeStampedModel):
    """
    Abstract base model for audit logging
    Provides common audit fields for all audit logs
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='%(class)s_logs')
    
    # Request Context
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    referer = models.URLField(blank=True)
    
    # Who made the change
    changed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_made'
    )
    
    # Action details
    action = models.CharField(max_length=100, db_index=True)
    description = models.TextField()
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[('success', 'Success'), ('failed', 'Failed'), ('pending', 'Pending')],
        default='success',
        db_index=True
    )
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]


# ---------------------------
# Session Audit Log Model
# ---------------------------
class SessionAuditLog(BaseAuditLog):
    """
    Comprehensive audit trail for user sessions
    Tracks creation, usage, and termination of sessions
    """
    
    ACTION_CHOICES = [
        # Session lifecycle
        ('session_created', 'Session Created'),
        ('session_renewed', 'Session Renewed'),
        ('session_activity', 'Session Activity'),
        ('session_revoked', 'Session Revoked'),
        ('session_expired', 'Session Expired'),
        ('session_terminated', 'Session Terminated'),
        
        # Token events
        ('access_token_issued', 'Access Token Issued'),
        ('access_token_refreshed', 'Access Token Refreshed'),
        ('refresh_token_issued', 'Refresh Token Issued'),
        ('refresh_token_used', 'Refresh Token Used'),
        ('refresh_token_rotated', 'Refresh Token Rotated'),
        ('token_blacklisted', 'Token Blacklisted'),
        
        # Security events
        ('session_hijack_detected', 'Session Hijack Detected'),
        ('concurrent_session_limit_exceeded', 'Concurrent Session Limit Exceeded'),
        ('suspicious_activity_detected', 'Suspicious Activity Detected'),
        
        # Device events
        ('device_linked_to_session', 'Device Linked'),
        ('device_changed_during_session', 'Device Changed'),
        ('device_unverified', 'Device Unverified'),
    ]
    
    # Session Reference
    session = models.ForeignKey(
        'sessions.Session',
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    
    # Device Reference (optional)
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='session_audits'
    )
    
    # Action details
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    
    # Session specific fields
    session_jti = models.CharField(max_length=255, db_index=True)
    previous_ip = models.GenericIPAddressField(null=True, blank=True)
    previous_user_agent = models.TextField(blank=True)
    
    # Token details (if applicable)
    token_type = models.CharField(
        max_length=20,
        choices=[('access', 'Access Token'), ('refresh', 'Refresh Token'), ('both', 'Both')],
        blank=True
    )
    token_jti = models.CharField(max_length=255, blank=True, db_index=True)
    
    # Duration (for session termination)
    session_duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    
    # Risk assessment
    risk_level = models.CharField(
        max_length=20,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')],
        default='low'
    )
    
    # Response/Action taken
    action_taken = models.CharField(max_length=255, blank=True)
    requires_review = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'session_audit_logs'
        verbose_name = 'Session Audit Log'
        verbose_name_plural = 'Session Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'action', '-created_at']),
            models.Index(fields=['session', '-created_at']),
            models.Index(fields=['device', '-created_at']),
            models.Index(fields=['risk_level', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.action} for {self.user.email} - {self.session.id} at {self.created_at}"


# ---------------------------
# Device Audit Log Model
# ---------------------------
class DeviceAuditLog(BaseAuditLog):
    """
    Comprehensive audit trail for device management
    Tracks device addition, verification, trust changes, and removal
    """
    
    ACTION_CHOICES = [
        # Device registration
        ('device_registered', 'Device Registered'),
        ('device_detected', 'Device Detected'),
        ('device_fingerprint_updated', 'Device Fingerprint Updated'),
        
        # Device verification
        ('device_verification_initiated', 'Device Verification Initiated'),
        ('device_verification_completed', 'Device Verification Completed'),
        ('device_verification_failed', 'Device Verification Failed'),
        
        # Device trust
        ('device_marked_trusted', 'Device Marked Trusted'),
        ('device_trust_revoked', 'Device Trust Revoked'),
        ('device_trust_expired', 'Device Trust Expired'),
        ('trusted_device_bypassed_mfa', 'Trusted Device Bypassed MFA'),
        
        # Device removal
        ('device_removed', 'Device Removed'),
        ('device_unlinked', 'Device Unlinked'),
        ('device_soft_deleted', 'Device Soft Deleted'),
        ('device_hard_deleted', 'Device Hard Deleted'),
        
        # Security alerts
        ('suspicious_device_detected', 'Suspicious Device Detected'),
        ('device_compromise_suspected', 'Device Compromise Suspected'),
        ('device_location_anomaly', 'Device Location Anomaly'),
        ('multiple_devices_same_location', 'Multiple Devices Same Location'),
        
        # Device updates
        ('device_name_changed', 'Device Name Changed'),
        ('device_metadata_updated', 'Device Metadata Updated'),
        ('device_permissions_updated', 'Device Permissions Updated'),
    ]
    
    # Device Reference
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='device_audits'
    )
    
    # Action details
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    
    # Device specific fields
    device_fingerprint = models.CharField(max_length=255, blank=True)
    device_name = models.CharField(max_length=255, blank=True)
    device_type = models.CharField(
        max_length=20,
        choices=[('mobile', 'Mobile'), ('tablet', 'Tablet'), ('desktop', 'Desktop'), ('unknown', 'Unknown')],
        blank=True
    )
    
    # Browser and OS details
    browser = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)
    
    # Location details
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    previous_country = models.CharField(max_length=100, blank=True)
    previous_city = models.CharField(max_length=100, blank=True)
    
    # Trust information
    was_trusted = models.BooleanField(default=False)
    now_trusted = models.BooleanField(default=False)
    trust_duration_days = models.PositiveIntegerField(null=True, blank=True)
    
    # Verification details
    verification_method = models.CharField(
        max_length=50,
        choices=[
            ('email_otp', 'Email OTP'),
            ('sms_otp', 'SMS OTP'),
            ('manual', 'Manual'),
            ('auto', 'Automatic'),
        ],
        blank=True
    )
    
    # Risk assessment
    risk_score = models.PositiveIntegerField(default=0)  # 0-100
    risk_level = models.CharField(
        max_length=20,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')],
        default='low'
    )
    
    # Anomaly detection
    is_anomalous = models.BooleanField(default=False)
    anomaly_reasons = models.JSONField(default=list, blank=True)  # List of detected anomalies
    
    # Session context
    session = models.ForeignKey(
        'sessions.Session',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='device_audits'
    )
    
    # Response/Action taken
    action_taken = models.CharField(max_length=255, blank=True)
    requires_review = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'device_audit_logs'
        verbose_name = 'Device Audit Log'
        verbose_name_plural = 'Device Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'action', '-created_at']),
            models.Index(fields=['device', '-created_at']),
            models.Index(fields=['risk_level', '-created_at']),
            models.Index(fields=['is_anomalous', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.action} for {self.user.email} - {self.device.device_name} at {self.created_at}"


# ---------------------------
# Session-Device Link Audit Model
# ---------------------------
class SessionDeviceLinkAuditLog(BaseAuditLog):
    """
    Track the relationship between sessions and devices
    Audit when devices are linked/unlinked from sessions
    """
    
    ACTION_CHOICES = [
        ('device_added_to_session', 'Device Added to Session'),
        ('device_removed_from_session', 'Device Removed from Session'),
        ('device_changed_mid_session', 'Device Changed Mid-Session'),
        ('device_verified_for_session', 'Device Verified for Session'),
        ('device_unverified_for_session', 'Device Unverified for Session'),
        ('session_device_sync', 'Session-Device Sync'),
    ]
    
    # References
    session = models.ForeignKey(
        'sessions.Session',
        on_delete=models.CASCADE,
        related_name='device_link_audits'
    )
    
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='session_link_audits'
    )
    
    # Action details
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    
    # Device state at time of action
    device_was_verified = models.BooleanField(default=False)
    device_now_verified = models.BooleanField(default=False)
    device_was_trusted = models.BooleanField(default=False)
    device_now_trusted = models.BooleanField(default=False)
    
    # Duration of link
    link_duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    
    # Previous device (if device was changed)
    previous_device = models.ForeignKey(
        'devices.Device',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='previous_device_links'
    )
    
    class Meta:
        db_table = 'session_device_link_audit_logs'
        verbose_name = 'Session-Device Link Audit Log'
        verbose_name_plural = 'Session-Device Link Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['session', '-created_at']),
            models.Index(fields=['device', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.action} for {self.user.email} at {self.created_at}"


# ---------------------------
# MFA Audit Log Model
# ---------------------------
class MFAAuditLog(BaseAuditLog):
    """
    Audit trail for MFA-related events
    Tracks MFA setup, changes, verification, and challenges
    """
    
    ACTION_CHOICES = [
        # MFA setup
        ('mfa_enabled', 'MFA Enabled'),
        ('mfa_disabled', 'MFA Disabled'),
        ('mfa_method_added', 'MFA Method Added'),
        ('mfa_method_removed', 'MFA Method Removed'),
        ('mfa_primary_method_changed', 'Primary Method Changed'),
        
        # TOTP
        ('totp_setup_initiated', 'TOTP Setup Initiated'),
        ('totp_setup_completed', 'TOTP Setup Completed'),
        ('totp_verified', 'TOTP Verified'),
        ('totp_disabled', 'TOTP Disabled'),
        
        # Email MFA
        ('email_mfa_setup_initiated', 'Email MFA Setup Initiated'),
        ('email_mfa_verified', 'Email MFA Verified'),
        ('email_mfa_disabled', 'Email MFA Disabled'),
        
        # SMS MFA
        ('sms_mfa_setup_initiated', 'SMS MFA Setup Initiated'),
        ('sms_mfa_verified', 'SMS MFA Verified'),
        ('sms_mfa_disabled', 'SMS MFA Disabled'),
        
        # Backup codes
        ('backup_codes_generated', 'Backup Codes Generated'),
        ('backup_codes_regenerated', 'Backup Codes Regenerated'),
        ('backup_code_used', 'Backup Code Used'),
        
        # Challenges
        ('mfa_challenge_issued', 'MFA Challenge Issued'),
        ('mfa_challenge_passed', 'MFA Challenge Passed'),
        ('mfa_challenge_failed', 'MFA Challenge Failed'),
        ('mfa_challenge_expired', 'MFA Challenge Expired'),
        
        # Recovery
        ('mfa_recovery_initiated', 'MFA Recovery Initiated'),
        ('mfa_recovery_completed', 'MFA Recovery Completed'),
    ]
    
    # User and Device
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mfa_audits'
    )
    
    # Action details
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    
    # MFA method involved
    mfa_method = models.CharField(
        max_length=20,
        choices=[('totp', 'TOTP'), ('email', 'Email'), ('sms', 'SMS'), ('backup', 'Backup Code')],
        db_index=True
    )
    
    # Details
    old_method = models.CharField(max_length=20, blank=True)
    new_method = models.CharField(max_length=20, blank=True)
    
    # Verification details
    challenge_id = models.CharField(max_length=255, blank=True)
    was_verified = models.BooleanField(null=True, blank=True)
    
    # OTP details (hashed)
    otp_hash = models.CharField(max_length=255, blank=True)
    verification_attempts = models.PositiveIntegerField(default=0)
    
    # Recovery details
    recovery_method = models.CharField(
        max_length=50,
        choices=[
            ('backup_code', 'Backup Code'),
            ('email_recovery', 'Email Recovery'),
            ('sms_recovery', 'SMS Recovery'),
            ('support_recovery', 'Support Recovery'),
        ],
        blank=True
    )
    
    # Risk assessment
    risk_level = models.CharField(
        max_length=20,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')],
        default='low'
    )
    
    class Meta:
        db_table = 'mfa_audit_logs'
        verbose_name = 'MFA Audit Log'
        verbose_name_plural = 'MFA Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'action', '-created_at']),
            models.Index(fields=['mfa_method', '-created_at']),
            models.Index(fields=['risk_level', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.action} ({self.mfa_method}) for {self.user.email} at {self.created_at}"


# ---------------------------
# Generic Audit Log Model
# ---------------------------
class AuditLog(TimeStampedModel):
    """
    Comprehensive audit trail for security events across the platform.
    Generic audit model for tracking general security-related events.
    For specific event types, use SessionAuditLog, DeviceAuditLog, or MFAAuditLog.
    """
    
    EVENT_TYPE_CHOICES = [
        # Login events
        ('login_success', 'Login Success'),
        ('login_failed', 'Login Failed'),
        ('logout', 'Logout'),
        ('session_expired', 'Session Expired'),
        
        # Account events
        ('account_created', 'Account Created'),
        ('account_updated', 'Account Updated'),
        ('account_deleted', 'Account Deleted'),
        ('email_changed', 'Email Changed'),
        ('email_verified', 'Email Verified'),
        ('phone_changed', 'Phone Changed'),
        
        # Password events
        ('password_changed', 'Password Changed'),
        ('password_reset_requested', 'Password Reset Requested'),
        ('password_reset_completed', 'Password Reset Completed'),
        ('password_failed_attempts', 'Password Failed Attempts'),
        
        # MFA events
        ('mfa_enabled', 'MFA Enabled'),
        ('mfa_disabled', 'MFA Disabled'),
        ('mfa_method_added', 'MFA Method Added'),
        ('mfa_method_removed', 'MFA Method Removed'),
        
        # Device events
        ('device_added', 'Device Added'),
        ('device_removed', 'Device Removed'),
        ('device_verified', 'Device Verified'),
        ('device_trusted', 'Device Trusted'),
        ('device_compromised', 'Device Compromised'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPE_CHOICES,
        db_index=True
    )
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        db_index=True
    )
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generic_audits'
    )
    metadata = models.JSONField(default=dict, blank=True)
    
    # Resolution fields
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_audit_logs'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'event_type', '-created_at']),
            models.Index(fields=['event_type', '-created_at']),
            models.Index(fields=['severity', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.user.email if self.user else 'System'} at {self.created_at}"


# ---------------------------
# MFA Change Log Model
# ---------------------------
class MFAChangeLog(TimeStampedModel):
    """
    Audit trail for all MFA setting changes
    Track when users enable/disable/modify MFA settings
    """
    
    CHANGE_TYPE_CHOICES = [
        ('method_enabled', 'Method Enabled'),
        ('method_disabled', 'Method Disabled'),
        ('primary_method_changed', 'Primary Method Changed'),
        ('backup_method_added', 'Backup Method Added'),
        ('backup_method_removed', 'Backup Method Removed'),
        ('settings_updated', 'Settings Updated'),
        ('mfa_enforced', 'MFA Enforced'),
        ('mfa_disabled', 'MFA Disabled'),
        ('recovery_codes_generated', 'Recovery Codes Generated'),
        ('recovery_codes_regenerated', 'Recovery Codes Regenerated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='mfa_change_logs')
    
    # Change Details
    change_type = models.CharField(max_length=50, choices=CHANGE_TYPE_CHOICES, db_index=True)
    description = models.TextField()
    
    # Method involved
    method = models.CharField(
        max_length=20,
        choices=[('totp', 'TOTP'), ('email', 'Email'), ('sms', 'SMS')],
        null=True,
        blank=True
    )
    
    # Context
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Changed by (self or admin)
    changed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mfa_changes_made'
    )
    
    # Old and new values
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    
    # Reason (optional)
    reason = models.TextField(blank=True)
    
    # Approval status (for sensitive changes)
    requires_approval = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'mfa_change_logs'
        verbose_name = 'MFA Change Log'
        verbose_name_plural = 'MFA Change Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['change_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.change_type} for {self.user.email} at {self.created_at}"


# ---------------------------
# Audit Summary/Analytics Model
# ---------------------------
class AuditLogSummary(TimeStampedModel):
    """
    Aggregated audit statistics for performance and analytics
    Daily summary of key audit events per user
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='audit_summaries')
    
    # Date
    summary_date = models.DateField(db_index=True)
    
    # Session statistics
    total_sessions_created = models.PositiveIntegerField(default=0)
    total_sessions_terminated = models.PositiveIntegerField(default=0)
    total_sessions_revoked = models.PositiveIntegerField(default=0)
    concurrent_sessions_max = models.PositiveIntegerField(default=0)
    
    # Device statistics
    total_devices_registered = models.PositiveIntegerField(default=0)
    total_devices_verified = models.PositiveIntegerField(default=0)
    total_devices_trusted = models.PositiveIntegerField(default=0)
    total_devices_removed = models.PositiveIntegerField(default=0)
    
    # Security events
    failed_mfa_attempts = models.PositiveIntegerField(default=0)
    successful_mfa_verifications = models.PositiveIntegerField(default=0)
    suspicious_activities_detected = models.PositiveIntegerField(default=0)
    anomalous_devices_detected = models.PositiveIntegerField(default=0)
    
    # Risk statistics
    high_risk_events = models.PositiveIntegerField(default=0)
    critical_risk_events = models.PositiveIntegerField(default=0)
    
    # Geographic statistics
    unique_locations = models.PositiveIntegerField(default=0)
    unique_countries = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'audit_log_summaries'
        verbose_name = 'Audit Log Summary'
        verbose_name_plural = 'Audit Log Summaries'
        unique_together = [['user', 'summary_date']]
        ordering = ['-summary_date']
        indexes = [
            models.Index(fields=['user', 'summary_date']),
        ]
    
    def __str__(self):
        return f"Audit Summary for {self.user.email} on {self.summary_date}"


# ============================================================================
# END OF FILE
# ============================================================================
