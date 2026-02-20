# NOTIFICATIONS APP - Complete Documentation

## ðŸ“‹ Table of Contents
1. [Overview](#overview)
2. [Models](#models)
3. [Notification Preferences](#notification-preferences)
4. [Email & SMS Tracking](#email--sms-tracking)
5. [MFA Notifications](#mfa-notifications)
6. [User Customization](#user-customization)
7. [Best Practices](#best-practices)
8. [Future Enhancements](#future-enhancements)

---

## Overview

The **NOTIFICATIONS** app handles all user communication:
- Email notifications (OTP, alerts, verification)
- SMS notifications (OTP, alerts)
- Notification preferences (per type, per channel)
- User opt-in/opt-out (GDPR compliance)
- Quiet hours (don't disturb periods)
- Blocklist (block senders)
- MFA-specific notifications
- Delivery tracking and analytics

**Key Features:**
- Multi-channel delivery (email, SMS, in-app, push)
- User-controlled preferences
- Granular per-notification-type settings
- Quiet hours with timezone support
- GDPR consent tracking
- Delivery and open rate tracking
- Cost tracking for SMS
- Retry logic for failed sends

---

## Models

### 1. **EmailNotification Model**
**Database Table:** `email_notifications`

Track email notifications sent to users.

**Key Fields:**
```
id (UUID)
user (ForeignKey)              # Which user?

# Email Details
to_email (EmailField)          # Email address
subject (String)               # Email subject line
email_type (Choice)            # OTP, alert, verification, etc
template_name (String)         # Which template? confirmation.html

# Content
body (Text)                    # Email body

# Status
status (Choice)                # Pending, Sent, Failed, Bounced
sent_at (DateTime)             # When sent?

# Tracking
opened_at (DateTime)           # When user opened email?
clicked_at (DateTime)          # When user clicked link?
click_url (URL)                # Which link clicked?

# Error Handling
error_message (Text)           # If failed, why?
retry_count (Int)              # How many retries?
max_retries (Int)              # Max retries allowed?

# Provider Details
provider (String)              # SendGrid, AWS SES, Mailgun, etc
provider_message_id (String)   # Provider's message ID

# Timestamps
created_at (DateTime)          # When queued?
```

**Email Types:**
- `otp` - OTP code
- `password_reset` - Password reset link
- `email_verification` - Email verification
- `welcome` - Welcome email
- `account_alert` - Account activity alert
- `security_alert` - Security event alert
- `device_verification` - Device verification
- `session_alert` - Session activity
- `mfa_setup` - MFA setup instructions

**Methods:**
```python
email = EmailNotification.objects.get(id=email_id)

# Mark as sent
email.mark_sent(provider_message_id='msg_123')

# Mark as failed
email.mark_failed(error_message='Invalid email address')

# Increment retry
email.increment_retry()

# Check if retryable
if email.is_retryable():
    # Retry sending email
    pass
```

**Indexes:**
- user + status (find pending emails)
- email_type + status (find failed emails by type)
- created_at (time-range queries)

---

### 2. **SMSNotification Model**
**Database Table:** `sms_notifications`

Track SMS notifications sent to users.

**Key Fields:**
```
id (UUID)
user (ForeignKey)              # Which user?

# SMS Details
phone_number (String)          # Phone number
message (Text)                 # SMS message body
sms_type (Choice)              # OTP, verification, alert, reminder

# Status
status (Choice)                # Pending, Sent, Delivered, Failed, Undelivered
sent_at (DateTime)             # When sent?
delivered_at (DateTime)        # When delivered?

# Provider Details
provider (String)              # Twilio, AWS SNS, vonage, etc
provider_message_id (String)   # Provider's message ID

# Error Information
error_message (Text)           # Error description
error_code (String)            # Error code

# Retry Tracking
retry_count (Int)              # Retries so far
max_retries (Int)              # Max allowed retries

# Cost Tracking
cost (Decimal)                 # How much did this SMS cost?

# Timestamps
created_at (DateTime)          # When queued?
```

**SMS Types:**
- `otp` - OTP code
- `verification` - Verification code
- `alert` - Security alert
- `reminder` - Reminder notification
- `confirmation` - Action confirmation

**Methods:**
```python
sms = SMSNotification.objects.get(id=sms_id)

# Mark as sent
sms.mark_sent(provider_message_id='msg_456')

# Mark as delivered
sms.mark_delivered()

# Mark as failed
sms.mark_failed(error_message='Invalid number', error_code='21614')

# Increment retry
sms.increment_retry()

# Check if retryable
if sms.is_retryable():
    # Retry sending
    pass
```

**Cost Analysis Query:**
```python
# Calculate SMS costs for user
costs = SMSNotification.objects.filter(
    user=user,
    status__in=['sent', 'delivered']
).aggregate(
    total_cost=Sum('cost')
)

# Typical SMS costs: $0.01-$0.05 per SMS
# 1M users Ã— 2 SMS/month = 2M SMS = $20k-$100k/month
```

---

### 3. **NotificationPreference Model**
**Database Table:** `notification_preferences`

Global notification settings per user.

**Key Fields:**
```
id (UUID)
user (OneToOne)                # User's global settings

# Email Preferences
email_otp (Boolean)            # Send OTP via email?
email_alerts (Boolean)         # Send alerts via email?
email_marketing (Boolean)      # Send marketing emails?

# SMS Preferences
sms_otp (Boolean)              # Send OTP via SMS?
sms_alerts (Boolean)           # Send alerts via SMS?

# Push Notifications
push_enabled (Boolean)         # Enable push notifications?

# Quiet Hours
quiet_hours_enabled (Boolean)  # Enable quiet hours?
quiet_start (Time)             # Start time (e.g., 22:00)
quiet_end (Time)               # End time (e.g., 08:00)

# Frequency
digest_frequency (Choice)      # Real-time, Daily, Weekly
```

**Digest Frequency:**
```
Real-time: Send immediately
Daily: Bundle and send once per day
Weekly: Bundle and send once per week
```

---

### 4. **DetailedNotificationPreference Model**
**Database Table:** `detailed_notification_preferences`

Per-notification-type granular settings.

**Key Fields:**
```
id (UUID)
user (ForeignKey)              # Which user?
notification_type (Choice)     # OTP, login alert, etc

# Enable/Disable per channel
email_enabled (Boolean)        # Send via email?
sms_enabled (Boolean)          # Send via SMS?
in_app_enabled (Boolean)       # In-app notification?
push_enabled (Boolean)         # Push notification?

# Priority
priority (Choice)              # Low, Medium, High
                              # High priority = always deliver

# Timing
respect_quiet_hours (Boolean)  # Skip during quiet hours?
delay_minutes (Int)            # Delay before sending?

# Frequency Cap
max_per_day (Int)              # Max 10 per day?
```

**Notification Types (14 types):**
```
'otp_email'              - OTP codes via email
'otp_sms'                - OTP codes via SMS
'login_alert'            - New login detected
'device_added'           - New device registered
'device_verified'        - Device verified
'password_changed'       - Password changed
'mfa_enabled'            - MFA enabled
'mfa_disabled'           - MFA disabled
'security_alert'         - Security event
'account_locked'         - Account locked
'failed_login'           - Failed login attempts
'unusual_activity'       - Unusual activity detected
'account_recovery'       - Account recovery attempt
'session_expired'        - Session expired
```

**Example Configuration:**
```python
# User's detailed preferences:

# OTP via email: CRITICAL
pref = DetailedNotificationPreference.objects.get(
    user=user,
    notification_type='otp_email'
)
pref.email_enabled = True
pref.priority = 'high'
pref.respect_quiet_hours = False  # Always send, even at night
pref.max_per_day = 100  # Unlimited

# Marketing emails: OPTIONAL
pref = DetailedNotificationPreference.objects.get(
    user=user,
    notification_type='marketing'
)
pref.email_enabled = False  # User opted out
pref.priority = 'low'
```

**Unique Constraint:** (user, notification_type)

---

### 5. **QuietHours Model**
**Database Table:** `quiet_hours`

Multiple quiet hour periods per user.

**Key Fields:**
```
id (UUID)
user (ForeignKey)              # Which user?

# Time Period
day_of_week (Int)              # 0=Monday, 6=Sunday
start_time (Time)              # e.g., 22:00 (10 PM)
end_time (Time)                # e.g., 08:00 (8 AM)

# Configuration
is_enabled (Boolean)           # Is this period active?
allow_critical_only (Boolean)  # Allow critical notifications?
timezone (String)              # User's timezone

# Description
description (String)           # "Sleep", "Work", etc
```

**Use Cases:**
```
Example 1: Sleep
day_of_week: All (0-6)
start_time: 22:00
end_time: 08:00
allow_critical_only: True  # Allow OTP, not marketing

Example 2: Work
day_of_week: 1-5 (Mon-Fri)
start_time: 09:00
end_time: 17:00
allow_critical_only: True

Example 3: Gym
day_of_week: 3 (Wednesday)
start_time: 18:00
end_time: 19:00
allow_critical_only: True  # Allow emergency, not marketing
```

**Unique Constraint:** (user, day, start_time, end_time)

---

### 6. **NotificationBlocklist Model**
**Database Table:** `notification_blocklist`

Allow users to block specific senders.

**Key Fields:**
```
id (UUID)
user (ForeignKey)              # Which user?

# Block Details
block_type (Choice)            # Email, domain, phone, sender_id
blocked_value (String)         # spam@example.com, example.com, etc

# Status
is_active (Boolean)            # Is block active?
blocked_at (DateTime)          # When blocked?
unblocked_at (DateTime)        # When unblocked?

# Reason
reason (String)                # Why blocked?
```

**Block Types:**
```
'email'     - Specific email address
'domain'    - Email domain (@example.com)
'phone'     - Specific phone number
'sender_id' - SMS sender ID
```

**Unique Constraint:** (user, block_type, blocked_value)

**Usage:**
```python
# User receives spam from marketing@ads.com
blocklist = NotificationBlocklist.objects.create(
    user=user,
    block_type='email',
    blocked_value='marketing@ads.com',
    reason='Spam emails'
)

# On next email send:
if NotificationBlocklist.objects.filter(
    user=user,
    block_type='email',
    blocked_value=email_sender,
    is_active=True
).exists():
    # Skip sending this email
    pass
```

---

### 7. **NotificationConsent Model**
**Database Table:** `notification_consents`

Track user opt-in/opt-out for compliance.

**Key Fields:**
```
id (UUID)
user (ForeignKey)              # Which user?

# Consent Type
consent_type (Choice)          # Marketing, security, etc

# Consent Status
is_consented (Boolean)         # User opted in?
consented_at (DateTime)        # When did user consent?
withdrawn_at (DateTime)        # When withdrawn?

# Source
source (Choice)                # Signup form, settings, email link, admin

# Context
ip_address (IP)                # Where consent given?
user_agent (Text)              # Which device/browser?
```

**Consent Types:**
```
'marketing'          - Marketing emails
'security'           - Security alerts (always on)
'product_updates'    - Product update emails
'newsletter'         - Newsletter subscription
'promotions'         - Promotional emails
'analytics'          - Analytics tracking
```

**GDPR Compliance:**
```python
# User must explicitly opt-in (not opt-out)
# Default is no consent

# Get all consented users for marketing email
consented = NotificationConsent.objects.filter(
    consent_type='marketing',
    is_consented=True
)

# Only send to these users
for consent in consented:
    send_marketing_email(consent.user)

# Track unsubscribe/withdrawal
consent.is_consented = False
consent.withdrawn_at = timezone.now()
consent.save()

# Audit trail is important for GDPR
```

**Unique Constraint:** (user, consent_type)

---

### 8. **MFANotification Model**
**Database Table:** `mfa_notifications`

Dedicated MFA OTP tracking (email + SMS OTPs).

**Key Fields:**
```
id (UUID)
user (ForeignKey)              # Which user?

# Details
mfa_type (Choice)              # TOTP setup, email OTP, etc
delivery_method (Choice)       # Email, SMS, In-app

# Recipient
recipient (String)             # Email or phone

# Message
subject (String)               # Email subject
message (Text)                 # Message body

# OTP Code
otp_code_hash (String)         # Hashed OTP code
code_length (Int)              # Code length (6-8)

# Delivery
is_sent (Boolean)              # Sent successfully?
sent_at (DateTime)             # When sent?
is_delivered (Boolean)         # Delivered to user?
delivered_at (DateTime)        # When delivered?

# Verification
is_verified (Boolean)          # User verified code?
verified_at (DateTime)         # When verified?
verification_attempts (Int)    # Verification attempts
max_attempts (Int)             # Max allowed attempts

# Expiry
expires_at (DateTime)          # Code expiration time

# Error Handling
error_message (Text)           # Error if failed
retry_count (Int)              # Retry count

# Provider
provider (String)              # SendGrid, Twilio, etc
provider_message_id (String)   # Provider ID
```

**Methods:**
```python
mfa_notif = MFANotification.objects.get(id=notif_id)

# Check if valid
if mfa_notif.is_valid():
    print("Code still valid")

# Check if expired
if mfa_notif.is_expired():
    print("Code expired")

# Record attempt
mfa_notif.increment_attempts()

# Mark as sent
mfa_notif.mark_sent(provider_message_id='msg_789')

# Mark as verified
mfa_notif.mark_verified()
```

---

## Notification Preferences

### Preference Hierarchy:

```
1. NotificationConsent (GDPR - must have consent)
   â†“
2. NotificationBlocklist (User blocklist)
   â†“
3. DetailedNotificationPreference (Per-type settings)
   â†“
4. QuietHours (Don't disturb periods)
   â†“
5. NotificationPreference (Global settings)
   â†“
SEND NOTIFICATION
```

### Decision Logic:

```python
def should_send_notification(user, notification_type, channel):
    """
    Determine if notification should be sent
    """

    # 1. Check GDPR consent
    consent = NotificationConsent.objects.get(
        user=user,
        consent_type=notification_type
    )
    if not consent.is_consented:
        return False  # User not consented

    # 2. Check blocklist
    if NotificationBlocklist.objects.filter(
        user=user,
        blocked_value=sender,
        is_active=True
    ).exists():
        return False  # Sender blocked

    # 3. Check detailed preference
    detail_pref = DetailedNotificationPreference.objects.get(
        user=user,
        notification_type=notification_type
    )

    if channel == 'email' and not detail_pref.email_enabled:
        return False
    if channel == 'sms' and not detail_pref.sms_enabled:
        return False

    # 4. Check quiet hours
    if should_respect_quiet_hours(detail_pref):
        if is_in_quiet_hours(user):
            if detail_pref.priority != 'high':
                return False  # Delay until quiet hours end

    # 5. Check frequency cap
    today_count = EmailNotification.objects.filter(
        user=user,
        notification_type=notification_type,
        created_at__date=today
    ).count()

    if today_count >= detail_pref.max_per_day:
        return False  # Daily limit reached

    # All checks passed
    return True
```

---

## Email & SMS Tracking

### Email Delivery Status:

```
Pending (Queued)
    â†“
Sent (Provider accepted)
    â†“
Bounced (Invalid email) â†’ FAILED
    â†“
Delivered (User's mailbox)
    â†“
Opened (User opened email)
    â†“
Clicked (User clicked link)
```

### SMS Delivery Status:

```
Pending (Queued)
    â†“
Sent (Provider accepted)
    â†“
Delivered (Phone received)
    â†“
Failed (Network error)
    â†“
Undelivered (Invalid number)
```

### Retry Logic:

```python
# Retry failed emails
failed_emails = EmailNotification.objects.filter(
    status='failed',
    retry_count__lt=3  # Max 3 retries
)

for email in failed_emails:
    try:
        send_email(email)
        email.mark_sent()
    except Exception as e:
        email.increment_retry()
        email.mark_failed(error_message=str(e))
```

---

## MFA Notifications

### OTP via Email Flow:

```
User tries to login
    â†“
System detects MFA required
    â†“
System generates OTP code (6 digits)
    â†“
System hashes OTP
    â†“
System creates MFANotification (pending)
    â†“
System sends email to user
    â†“
MFANotification marked as sent
    â†“
User receives email: "Your code: 123456"
    â†“
User enters code in form
    â†“
System verifies code matches hash
    â†“
MFANotification marked as verified
    â†“
User logged in!
```

### Security Best Practices:

```python
# 1. Never send plaintext code
code = "123456"
email_body = f"Your code is: {code}"  # âœ… OK - in email

# But DON'T store plaintext
code_hash = make_password(code)
mfa_notif.code_hash = code_hash  # âœ… OK - hashed in DB

# 2. Time limit OTPs
mfa_notif.expires_at = timezone.now() + timedelta(minutes=5)

# 3. Limit attempts
mfa_notif.max_attempts = 3

# 4. Rate limit OTP requests
otp_count_last_hour = MFANotification.objects.filter(
    user=user,
    created_at__gte=timezone.now() - timedelta(hours=1)
).count()

if otp_count_last_hour >= 5:
    raise RateLimitError("Too many OTP requests")
```

---

## User Customization

### Complete Customization Example:

```python
# User John customizes notifications:

# 1. OTP via email: CRITICAL - always send
DetailedNotificationPreference.objects.filter(
    user=john,
    notification_type='otp_email'
).update(
    email_enabled=True,
    priority='high',
    respect_quiet_hours=False,
    max_per_day=100
)

# 2. Marketing emails: NEVER
DetailedNotificationPreference.objects.filter(
    user=john,
    notification_type='marketing'
).update(
    email_enabled=False
)

# 3. Sleep time: 10 PM - 8 AM
QuietHours.objects.create(
    user=john,
    day_of_week=0,  # Monday
    start_time=time(22, 0),
    end_time=time(8, 0),
    allow_critical_only=True,
    description='Sleep'
)

# 4. Block spam sender
NotificationBlocklist.objects.create(
    user=john,
    block_type='email',
    blocked_value='ads@spam.com',
    reason='Spam'
)

# 5. Consent to newsletter
NotificationConsent.objects.filter(
    user=john,
    consent_type='newsletter'
).update(
    is_consented=True,
    consented_at=timezone.now()
)

# Result: John gets:
# - OTP codes: Always (critical)
# - Newsletter: Once subscribed
# - Marketing: Never
# - Quiet hours: 10PM-8AM (except critical)
# - Spam blocked: Always
```

---

## Best Practices

### 1. **Always Get Consent (GDPR)**
```python
# âŒ BAD: Send emails without consent
EmailNotification.objects.create(user=user, ...)

# âœ… GOOD: Check consent first
consent = NotificationConsent.objects.get(
    user=user,
    consent_type='marketing'
)
if consent.is_consented:
    EmailNotification.objects.create(user=user, ...)
```

### 2. **Hash Sensitive Data**
```python
# âŒ BAD: Store plaintext OTP
mfa_notif.otp_code = "123456"

# âœ… GOOD: Hash before storing
otp_hash = make_password("123456")
mfa_notif.code_hash = otp_hash
```

### 3. **Implement Retry Logic**
```python
# âœ… GOOD: Retry failed notifications
failed = EmailNotification.objects.filter(
    status='failed',
    retry_count__lt=3
)

for notif in failed:
    try:
        send_email(notif)
        notif.mark_sent()
    except:
        notif.increment_retry()
```

### 4. **Track Delivery**
```python
# âœ… GOOD: Use webhooks from email provider
# Provider calls: POST /webhooks/email/bounce
# We mark email as bounced and disable user's email

def handle_email_bounce(email, reason):
    EmailNotification.objects.filter(
        to_email=email
    ).update(status='bounced')

    # Disable email notifications for this user
    user = User.objects.get(email=email)
    pref = DetailedNotificationPreference.objects.get(
        user=user,
        notification_type='otp_email'
    )
    pref.email_enabled = False
    pref.save()
```

### 5. **Rate Limit Notifications**
```python
# âœ… GOOD: Don't spam users
today = timezone.now().date()
count = EmailNotification.objects.filter(
    user=user,
    notification_type='marketing',
    created_at__date=today
).count()

max_per_day = DetailedNotificationPreference.objects.get(
    user=user,
    notification_type='marketing'
).max_per_day

if count >= max_per_day:
    # Don't send, user already received max today
    pass
```

---

## Future Enhancements

### 1. **In-App Notifications**
```python
class InAppNotification(models.Model):
    user = models.ForeignKey(User, ...)
    message = models.TextField()
    is_read = models.BooleanField(default=False)

    # Show popup in user's dashboard
    # No email/SMS needed
    # Instant delivery
```

### 2. **Push Notifications**
```python
class PushNotification(models.Model):
    user = models.ForeignKey(User, ...)
    device_token = models.CharField(max_length=500)

    # Send to mobile app
    # Works even if app not open
    # Rich notifications with images
```

### 3. **SMS Fallback Chain**
```python
# Try email first, fallback to SMS if needed
try:
    send_email(user, otp_code)
except EmailError:
    # Email failed, send SMS instead
    send_sms(user.phone, otp_code)
```

### 4. **Notification Templates**
```python
class NotificationTemplate(models.Model):
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=255)
    email_template = models.TextField()  # HTML template
    sms_template = models.TextField()   # Plain text template

    # Use Jinja2 templating
    # {{ code }} = rendered to 123456
    # {{ name }} = rendered to John
```

### 5. **Analytics & Reporting**
```python
class NotificationAnalytics(models.Model):
    notification_type = models.CharField(...)
    total_sent = models.IntegerField()
    total_opened = models.IntegerField()
    total_clicked = models.IntegerField()
    open_rate = models.FloatField()  # opened / sent
    click_rate = models.FloatField() # clicked / sent
    bounce_rate = models.FloatField() # bounced / sent
```

---

## Summary

The **NOTIFICATIONS** app provides:

âœ… **Multi-Channel Delivery**
- Email (SMTP, SendGrid, AWS SES)
- SMS (Twilio, AWS SNS, Vonage)
- In-app (future)
- Push (future)

âœ… **User Control**
- Global preferences
- Per-notification-type settings
- Quiet hours
- Blocklist
- Frequency caps

âœ… **GDPR Compliance**
- Consent tracking
- Opt-in for marketing
- Easy unsubscribe
- Data retention policies

âœ… **Reliability**
- Delivery tracking
- Retry logic
- Error handling
- Webhook integration

âœ… **Analytics**
- Open rates
- Click rates
- Bounce rates
- Cost tracking

---

