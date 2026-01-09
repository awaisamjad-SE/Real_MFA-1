# ============================================================================
# OTP APP - models.py
# One-Time Password management for various verification purposes
# ============================================================================

from django.db import models
from django.utils import timezone
import uuid

# Import User model from accounts app
from accounts.models import TimeStampedModel


# ---------------------------
# OTP Model
# ---------------------------
class OTP(TimeStampedModel):
    """
    One-Time Password for various verification purposes
    Security: Time-limited, attempt tracking, purpose-specific
    """
    
    PURPOSE_CHOICES = [
        ('email_verification', 'Email Verification'),
        ('phone_verification', 'Phone Verification'),
        ('device_verification', 'Device Verification'),
        ('password_reset', 'Password Reset'),
        ('login_2fa', 'Login 2FA'),
        ('sensitive_action', 'Sensitive Action'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Use string reference to avoid circular imports
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='otps')
    
    # OTP Details
    code_hash = models.CharField(max_length=255, db_index=True)  # Hashed OTP code
    purpose = models.CharField(max_length=30, choices=PURPOSE_CHOICES, db_index=True)
    
    # Target (email or phone)
    target = models.CharField(max_length=255)  # Email or phone number
    
    # Security
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Status
    is_used = models.BooleanField(default=False, db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)
    
    # Expiry
    expires_at = models.DateTimeField(db_index=True)
    
    class Meta:
        db_table = 'otps'
        verbose_name = 'OTP'
        verbose_name_plural = 'OTPs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'purpose', 'is_used']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"OTP for {self.user.email} - {self.get_purpose_display()}"
    
    def is_valid(self):
        """Check if OTP is still valid"""
        return (
            not self.is_used 
            and timezone.now() < self.expires_at 
            and self.attempts < self.max_attempts
        )
    
    def increment_attempts(self):
        """Increment failed attempts"""
        self.attempts += 1
        self.save(update_fields=['attempts'])
    
    def mark_used(self):
        """Mark OTP as used"""
        self.is_used = True
        self.used_at = timezone.now()
        self.save(update_fields=['is_used', 'used_at'])


# ---------------------------
# TOTP Device Model
# ---------------------------
class TOTPDevice(TimeStampedModel):
    """
    TOTP/Google Authenticator configuration
    Security: Stores TOTP secret, backup codes, and verification status
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='totp_device')
    
    # TOTP Configuration
    secret = models.CharField(max_length=32)  # Base32 encoded secret
    
    # Status
    is_verified = models.BooleanField(default=False, db_index=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Backup Codes
    backup_codes_generated_at = models.DateTimeField(null=True, blank=True)
    
    # Usage Stats
    last_used_at = models.DateTimeField(null=True, blank=True)
    total_verifications = models.PositiveIntegerField(default=0)
    failed_attempts = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'totp_devices'
        verbose_name = 'TOTP Device'
        verbose_name_plural = 'TOTP Devices'
    
    def __str__(self):
        return f"TOTP for {self.user.email} - {'Verified' if self.is_verified else 'Unverified'}"
    
    def mark_verified(self):
        """Mark TOTP as verified"""
        self.is_verified = True
        self.verified_at = timezone.now()
        self.save(update_fields=['is_verified', 'verified_at'])


# ---------------------------
# Backup Code Model
# ---------------------------
class BackupCode(TimeStampedModel):
    """
    Backup codes for account recovery when TOTP is unavailable
    Security: One-time use codes, hashed storage
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='backup_codes')
    
    # Code Storage (hashed)
    code_hash = models.CharField(max_length=255, db_index=True)
    
    # Usage Tracking
    is_used = models.BooleanField(default=False, db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)
    used_from_ip = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        db_table = 'backup_codes'
        verbose_name = 'Backup Code'
        verbose_name_plural = 'Backup Codes'
        ordering = ['is_used', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_used']),
        ]
    
    def __str__(self):
        status = 'Used' if self.is_used else 'Active'
        return f"Backup Code for {self.user.email} - {status}"
    
    def mark_used(self, ip_address):
        """Mark backup code as used"""
        self.is_used = True
        self.used_at = timezone.now()
        self.used_from_ip = ip_address
        self.save(update_fields=['is_used', 'used_at', 'used_from_ip'])




# ---------------------------
# MFA Challenge Model
# ---------------------------
class MFAChallenge(TimeStampedModel):
    """
    Track MFA challenges sent to users
    Security: Challenge tracking, delivery status, verification status
    """
    
    CHALLENGE_TYPE_CHOICES = [
        ('totp', 'TOTP'),
        ('email', 'Email OTP'),
        ('sms', 'SMS OTP'),
        ('backup_code', 'Backup Code'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='mfa_challenges')
    
    # Challenge Details
    challenge_type = models.CharField(max_length=20, choices=CHALLENGE_TYPE_CHOICES, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    
    # Challenge Context
    session_id = models.CharField(max_length=255, null=True, blank=True)  # Link to login session
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Verification Attempts
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    
    # Timing
    expires_at = models.DateTimeField(db_index=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Device used for verification
    verified_device = models.ForeignKey(
        'devices.Device',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mfa_challenges'
    )
    
    class Meta:
        db_table = 'mfa_challenges'
        verbose_name = 'MFA Challenge'
        verbose_name_plural = 'MFA Challenges'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['session_id']),
        ]
    
    def __str__(self):
        return f"MFA Challenge {self.challenge_type} for {self.user.email} - {self.status}"
    
    def is_valid(self):
        """Check if challenge is still valid"""
        return (
            self.status == 'pending'
            and timezone.now() < self.expires_at
            and self.attempts < self.max_attempts
        )
    
    def increment_attempts(self):
        """Increment failed attempts"""
        self.attempts += 1
        if self.attempts >= self.max_attempts:
            self.status = 'failed'
        self.save(update_fields=['attempts', 'status'])
    
    def mark_verified(self, device=None):
        """Mark challenge as verified"""
        self.status = 'verified'
        self.verified_at = timezone.now()
        if device:
            self.verified_device = device
        self.save(update_fields=['status', 'verified_at', 'verified_device'])
    
    def mark_expired(self):
        """Mark challenge as expired"""
        self.status = 'expired'
        self.save(update_fields=['status'])


# ---------------------------
# Email MFA Method Model
# ---------------------------
class EmailMFAMethod(TimeStampedModel):
    """
    Email-based MFA method configuration
    Allows users to set email as their MFA method
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='email_mfa_method')
    
    # Configuration
    email = models.EmailField()
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_enabled = models.BooleanField(default=True)
    
    # Usage Stats
    last_used_at = models.DateTimeField(null=True, blank=True)
    total_verifications = models.PositiveIntegerField(default=0)
    failed_attempts = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'email_mfa_methods'
        verbose_name = 'Email MFA Method'
        verbose_name_plural = 'Email MFA Methods'
    
    def __str__(self):
        return f"Email MFA for {self.user.email} - {self.email}"


# ---------------------------
# SMS MFA Method Model
# ---------------------------
class SMSMFAMethod(TimeStampedModel):
    """
    SMS-based MFA method configuration
    Allows users to set SMS as their MFA method
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='sms_mfa_method')
    
    # Configuration
    phone_number = models.CharField(max_length=15)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_enabled = models.BooleanField(default=True)
    
    # Usage Stats
    last_used_at = models.DateTimeField(null=True, blank=True)
    total_verifications = models.PositiveIntegerField(default=0)
    failed_attempts = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'sms_mfa_methods'
        verbose_name = 'SMS MFA Method'
        verbose_name_plural = 'SMS MFA Methods'
    
    def __str__(self):
        return f"SMS MFA for {self.user.email} - {self.phone_number}"


# ---------------------------
# MFA Recovery Model
# ---------------------------
class MFARecovery(TimeStampedModel):
    """
    Track MFA recovery attempts and recovery codes usage
    Security: Track when users recover accounts using backup codes
    """
    
    RECOVERY_TYPE_CHOICES = [
        ('backup_code', 'Backup Code'),
        ('email_recovery', 'Email Recovery'),
        ('sms_recovery', 'SMS Recovery'),
        ('support_recovery', 'Support Recovery'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='mfa_recoveries')
    
    # Recovery Details
    recovery_type = models.CharField(max_length=30, choices=RECOVERY_TYPE_CHOICES)
    
    # Context
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Status
    is_successful = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'mfa_recoveries'
        verbose_name = 'MFA Recovery'
        verbose_name_plural = 'MFA Recoveries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_successful']),
        ]
    
    def __str__(self):
        status = 'Successful' if self.is_successful else 'Failed'
        return f"MFA Recovery for {self.user.email} - {status}"


# ============================================================================
# END OF FILE
# ============================================================================
