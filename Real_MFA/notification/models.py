# ============================================================================
# NOTIFICATIONS APP - models.py
# Email and SMS notification tracking and management
# ============================================================================

from django.db import models
from django.utils import timezone
import uuid

# Import User model from accounts app
from accounts.models import TimeStampedModel


# ---------------------------
# Email Notification Model
# ---------------------------
class EmailNotification(TimeStampedModel):
    """
    Track email notifications sent to users
    Supports: OTP emails, password reset, account alerts, etc.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]
    
    EMAIL_TYPE_CHOICES = [
        ('otp', 'OTP Code'),
        ('password_reset', 'Password Reset'),
        ('email_verification', 'Email Verification'),
        ('welcome', 'Welcome'),
        ('account_alert', 'Account Alert'),
        ('security_alert', 'Security Alert'),
        ('device_verification', 'Device Verification'),
        ('session_alert', 'Session Alert'),
        ('mfa_setup', 'MFA Setup'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='email_notifications')
    
    # Email Details
    to_email = models.EmailField()
    subject = models.CharField(max_length=255)
    email_type = models.CharField(max_length=50, choices=EMAIL_TYPE_CHOICES, db_index=True)
    template_name = models.CharField(max_length=100)
    
    # Email Content
    body = models.TextField()
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Tracking
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    click_url = models.URLField(blank=True)
    
    # Error Handling
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    
    # Provider Details
    provider = models.CharField(max_length=50, blank=True)  # e.g., SendGrid, AWS SES
    provider_message_id = models.CharField(max_length=255, blank=True, unique=True)
    
    class Meta:
        db_table = 'email_notifications'
        verbose_name = 'Email Notification'
        verbose_name_plural = 'Email Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['email_type', 'status']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.subject} to {self.to_email} - {self.status}"
    
    def mark_sent(self, provider_message_id=None):
        """Mark email as sent"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        if provider_message_id:
            self.provider_message_id = provider_message_id
        self.save(update_fields=['status', 'sent_at', 'provider_message_id'])
    
    def mark_failed(self, error_message=''):
        """Mark email as failed"""
        self.status = 'failed'
        if error_message:
            self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])
    
    def increment_retry(self):
        """Increment retry count"""
        self.retry_count += 1
        self.save(update_fields=['retry_count'])
    
    def is_retryable(self):
        """Check if email can be retried"""
        return self.status == 'failed' and self.retry_count < self.max_retries


# ---------------------------
# SMS Notification Model
# ---------------------------
class SMSNotification(TimeStampedModel):
    """
    Track SMS notifications sent to users
    Supports: OTP codes, alerts, notifications
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('undelivered', 'Undelivered'),
    ]
    
    SMS_TYPE_CHOICES = [
        ('otp', 'OTP Code'),
        ('verification', 'Verification'),
        ('alert', 'Alert'),
        ('reminder', 'Reminder'),
        ('confirmation', 'Confirmation'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='sms_notifications')
    
    # SMS Details
    phone_number = models.CharField(max_length=15)
    message = models.TextField()
    sms_type = models.CharField(max_length=50, choices=SMS_TYPE_CHOICES, db_index=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Provider Details
    provider = models.CharField(max_length=50, blank=True)  # e.g., Twilio, AWS SNS
    provider_message_id = models.CharField(max_length=255, blank=True, unique=True)
    
    # Error Handling
    error_message = models.TextField(blank=True)
    error_code = models.CharField(max_length=50, blank=True)
    
    # Retry Tracking
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=2)
    
    # Cost Tracking (optional)
    cost = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    class Meta:
        db_table = 'sms_notifications'
        verbose_name = 'SMS Notification'
        verbose_name_plural = 'SMS Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['sms_type', 'status']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"SMS to {self.phone_number} - {self.status}"
    
    def mark_sent(self, provider_message_id=None):
        """Mark SMS as sent"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        if provider_message_id:
            self.provider_message_id = provider_message_id
        self.save(update_fields=['status', 'sent_at', 'provider_message_id'])
    
    def mark_delivered(self):
        """Mark SMS as delivered"""
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at'])
    
    def mark_failed(self, error_message='', error_code=''):
        """Mark SMS as failed"""
        self.status = 'failed'
        if error_message:
            self.error_message = error_message
        if error_code:
            self.error_code = error_code
        self.save(update_fields=['status', 'error_message', 'error_code'])
    
    def increment_retry(self):
        """Increment retry count"""
        self.retry_count += 1
        self.save(update_fields=['retry_count'])
    
    def is_retryable(self):
        """Check if SMS can be retried"""
        return self.status in ['failed', 'undelivered'] and self.retry_count < self.max_retries


# ---------------------------
# Notification Preference Model
# ---------------------------
class NotificationPreference(TimeStampedModel):
    """
    Store user notification preferences
    Allows users to control how they receive notifications
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Email Preferences
    email_otp = models.BooleanField(default=True)
    email_alerts = models.BooleanField(default=True)
    email_marketing = models.BooleanField(default=False)
    
    # SMS Preferences
    sms_otp = models.BooleanField(default=True)
    sms_alerts = models.BooleanField(default=True)
    
    # Push Notifications (optional)
    push_enabled = models.BooleanField(default=False)
    
    # Quiet Hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_start = models.TimeField(null=True, blank=True)
    quiet_end = models.TimeField(null=True, blank=True)
    
    # Frequency
    digest_frequency = models.CharField(
        max_length=20,
        choices=[
            ('real_time', 'Real-time'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
        ],
        default='real_time'
    )
    
    class Meta:
        db_table = 'notification_preferences'
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"Notification preferences for {self.user.email}"


# ---------------------------
# Detailed Notification Preference Model
# ---------------------------
class DetailedNotificationPreference(TimeStampedModel):
    """
    Granular notification preferences per notification type
    Allows users to customize exactly which notifications they receive
    """
    
    NOTIFICATION_TYPE_CHOICES = [
        ('otp_email', 'OTP via Email'),
        ('otp_sms', 'OTP via SMS'),
        ('login_alert', 'Login Alert'),
        ('device_added', 'New Device Added'),
        ('device_verified', 'Device Verified'),
        ('password_changed', 'Password Changed'),
        ('mfa_enabled', 'MFA Enabled'),
        ('mfa_disabled', 'MFA Disabled'),
        ('security_alert', 'Security Alert'),
        ('account_locked', 'Account Locked'),
        ('failed_login', 'Failed Login Attempts'),
        ('unusual_activity', 'Unusual Activity'),
        ('account_recovery', 'Account Recovery'),
        ('session_expired', 'Session Expired'),
    ]
    
    DELIVERY_CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('in_app', 'In-App'),
        ('push', 'Push Notification'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='detailed_notification_preferences')
    
    # Notification type
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE_CHOICES)
    
    # Enable/Disable per channel
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    in_app_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=False)
    
    # Priority
    priority = models.CharField(
        max_length=20,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        default='medium'
    )
    
    # Timing preferences
    respect_quiet_hours = models.BooleanField(default=True)
    delay_minutes = models.PositiveIntegerField(default=0, help_text='Delay notification by minutes')
    
    # Frequency cap
    max_per_day = models.PositiveIntegerField(default=10, help_text='Max notifications per day')
    
    class Meta:
        db_table = 'detailed_notification_preferences'
        verbose_name = 'Detailed Notification Preference'
        verbose_name_plural = 'Detailed Notification Preferences'
        unique_together = [['user', 'notification_type']]
        indexes = [
            models.Index(fields=['user', 'notification_type']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} preferences for {self.user.email}"
    
    def is_enabled_for_channel(self, channel):
        """Check if notification is enabled for specific channel"""
        if channel == 'email':
            return self.email_enabled
        elif channel == 'sms':
            return self.sms_enabled
        elif channel == 'in_app':
            return self.in_app_enabled
        elif channel == 'push':
            return self.push_enabled
        return False


# ---------------------------
# Quiet Hours Model
# ---------------------------
class QuietHours(TimeStampedModel):
    """
    Allow users to set multiple quiet hour periods
    Times when they don't want to receive notifications
    """
    
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='quiet_hours')
    
    # Day and Time
    day_of_week = models.IntegerField(choices=DAY_CHOICES)  # 0=Monday, 6=Sunday
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Configuration
    is_enabled = models.BooleanField(default=True)
    allow_critical_only = models.BooleanField(default=False, help_text='Allow only critical notifications')
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Description
    description = models.CharField(max_length=255, blank=True)
    
    class Meta:
        db_table = 'quiet_hours'
        verbose_name = 'Quiet Hours'
        verbose_name_plural = 'Quiet Hours'
        unique_together = [['user', 'day_of_week', 'start_time', 'end_time']]
        indexes = [
            models.Index(fields=['user', 'day_of_week']),
        ]
    
    def __str__(self):
        day_name = dict(self.DAY_CHOICES)[self.day_of_week]
        return f"Quiet hours for {self.user.email} on {day_name} {self.start_time} - {self.end_time}"


# ---------------------------
# Notification Blocklist Model
# ---------------------------
class NotificationBlocklist(TimeStampedModel):
    """
    Allow users to block specific senders or domains
    """
    
    BLOCK_TYPE_CHOICES = [
        ('email', 'Email Address'),
        ('domain', 'Email Domain'),
        ('phone', 'Phone Number'),
        ('sender_id', 'Sender ID (SMS)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notification_blocklist')
    
    # Block Details
    block_type = models.CharField(max_length=20, choices=BLOCK_TYPE_CHOICES)
    blocked_value = models.CharField(max_length=255)  # Email, phone, domain, etc.
    
    # Status
    is_active = models.BooleanField(default=True)
    blocked_at = models.DateTimeField(auto_now_add=True)
    unblocked_at = models.DateTimeField(null=True, blank=True)
    
    # Reason
    reason = models.CharField(max_length=255, blank=True)
    
    class Meta:
        db_table = 'notification_blocklist'
        verbose_name = 'Notification Blocklist'
        verbose_name_plural = 'Notification Blocklists'
        unique_together = [['user', 'block_type', 'blocked_value']]
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"Block {self.blocked_value} for {self.user.email}"


# ---------------------------
# Notification Consent Model
# ---------------------------
class NotificationConsent(TimeStampedModel):
    """
    Track user consent for different types of notifications
    GDPR/Privacy compliance - user must opt-in for certain notifications
    """
    
    CONSENT_TYPE_CHOICES = [
        ('marketing', 'Marketing Emails'),
        ('security', 'Security Alerts'),
        ('product_updates', 'Product Updates'),
        ('newsletter', 'Newsletter'),
        ('promotions', 'Promotions'),
        ('analytics', 'Analytics Tracking'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notification_consents')
    
    # Consent Type
    consent_type = models.CharField(max_length=50, choices=CONSENT_TYPE_CHOICES)
    
    # Consent Status
    is_consented = models.BooleanField(default=False)
    consented_at = models.DateTimeField(null=True, blank=True)
    withdrawn_at = models.DateTimeField(null=True, blank=True)
    
    # Consent Source
    source = models.CharField(
        max_length=50,
        choices=[
            ('signup', 'Sign Up'),
            ('settings', 'Settings'),
            ('email_link', 'Email Link'),
            ('admin', 'Admin'),
        ]
    )
    
    # IP and user agent for tracking
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'notification_consents'
        verbose_name = 'Notification Consent'
        verbose_name_plural = 'Notification Consents'
        unique_together = [['user', 'consent_type']]
        indexes = [
            models.Index(fields=['user', 'consent_type']),
            models.Index(fields=['is_consented']),
        ]
    
    def __str__(self):
        status = 'Consented' if self.is_consented else 'Not Consented'
        return f"{self.consent_type} - {self.user.email} - {status}"


# ============================================================================
# END OF FILE
# ============================================================================
class NotificationLog(TimeStampedModel):
    """
    Audit trail for all notifications
    Track notification delivery history
    """
    
    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push'),
        ('in_app', 'In-App'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notification_logs')
    
    # Notification Details
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, db_index=True)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    
    # Recipient
    recipient = models.CharField(max_length=255)  # Email or phone number
    
    # Status
    delivered = models.BooleanField(default=False)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'notification_logs'
        verbose_name = 'Notification Log'
        verbose_name_plural = 'Notification Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'channel']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.channel.upper()} notification to {self.recipient} - {self.created_at}"


# ---------------------------
# MFA Notification Model
# ---------------------------
class MFANotification(TimeStampedModel):
    """
    Dedicated tracking for MFA-related notifications (OTP, challenges)
    Includes both email and SMS OTP notifications for MFA purposes
    """
    
    MFA_TYPE_CHOICES = [
        ('totp_setup', 'TOTP Setup'),
        ('email_otp', 'Email OTP'),
        ('sms_otp', 'SMS OTP'),
        ('backup_code_generation', 'Backup Code Generation'),
        ('mfa_disabled', 'MFA Disabled'),
        ('mfa_enabled', 'MFA Enabled'),
        ('device_verified', 'Device Verified'),
        ('suspicious_login', 'Suspicious Login'),
    ]
    
    DELIVERY_METHOD_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('in_app', 'In-App'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='mfa_notifications')
    
    # Notification Details
    mfa_type = models.CharField(max_length=50, choices=MFA_TYPE_CHOICES, db_index=True)
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHOD_CHOICES)
    
    # Recipient Information
    recipient = models.CharField(max_length=255)  # Email or phone
    
    # Message Details
    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    
    # OTP Code (if applicable, should be hashed in production)
    otp_code_hash = models.CharField(max_length=255, blank=True)
    code_length = models.PositiveIntegerField(default=6)
    
    # Delivery Status
    is_sent = models.BooleanField(default=False, db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Delivery Tracking
    is_delivered = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Verification Tracking
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Expiry
    expires_at = models.DateTimeField(db_index=True)
    
    # Attempts
    verification_attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    
    # Error Information
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    
    # Provider Information
    provider = models.CharField(max_length=50, blank=True)
    provider_message_id = models.CharField(max_length=255, blank=True)
    
    class Meta:
        db_table = 'mfa_notifications'
        verbose_name = 'MFA Notification'
        verbose_name_plural = 'MFA Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'mfa_type', 'is_sent']),
            models.Index(fields=['user', 'is_verified']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"MFA {self.mfa_type} to {self.recipient} - {self.get_delivery_method_display()}"
    
    def is_valid(self):
        """Check if OTP is still valid for verification"""
        return (
            not self.is_verified
            and timezone.now() < self.expires_at
            and self.verification_attempts < self.max_attempts
        )
    
    def is_expired(self):
        """Check if OTP has expired"""
        return timezone.now() > self.expires_at
    
    def increment_attempts(self):
        """Increment verification attempts"""
        self.verification_attempts += 1
        self.save(update_fields=['verification_attempts'])
    
    def mark_sent(self, provider_message_id=None):
        """Mark as sent"""
        self.is_sent = True
        self.sent_at = timezone.now()
        if provider_message_id:
            self.provider_message_id = provider_message_id
        self.save(update_fields=['is_sent', 'sent_at', 'provider_message_id'])
    
    def mark_delivered(self):
        """Mark as delivered"""
        self.is_delivered = True
        self.delivered_at = timezone.now()
        self.save(update_fields=['is_delivered', 'delivered_at'])
    
    def mark_verified(self):
        """Mark OTP as verified"""
        self.is_verified = True
        self.verified_at = timezone.now()
        self.save(update_fields=['is_verified', 'verified_at'])


# ============================================================================
# END OF FILE
# ============================================================================
