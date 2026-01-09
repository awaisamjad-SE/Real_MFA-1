# ACCOUNTS APP - Complete Documentation

## 📋 Table of Contents
1. [Overview](#overview)
2. [Models](#models)
3. [Relationships](#relationships)
4. [Database Design](#database-design)
5. [Field Explanations](#field-explanations)
6. [Methods & Functionality](#methods--functionality)
7. [Best Practices](#best-practices)
8. [Future Enhancements](#future-enhancements)

---

## Overview

The **ACCOUNTS** app is the core of the authentication and user management system. It handles:
- User authentication and authorization
- User profiles and personal information
- Device management and tracking
- Session management
- MFA settings and preferences
- Password history and security
- Complete audit trail of user activities

**Key Features:**
- Role-based access control (Admin, Manager, User)
- Soft delete functionality (data not permanently removed)
- Comprehensive security fields
- UUID primary keys (better than sequential IDs)
- Device fingerprinting and trust management
- Session tracking with JWT tokens
- Refresh token rotation and blacklisting

---

## Models

### 1. **User Model** (Extends AbstractUser)
**Database Table:** `users`

Core user model with security-focused fields.

**Key Fields:**
```
id (UUID)                      # Primary key, not sequential
email (Email, unique)          # Login identifier
username (String)              # From AbstractUser
role (Choice)                  # Admin, Manager, User
password (String)              # From AbstractUser (hashed)
is_active (Boolean)            # From AbstractUser

# Security Fields
email_verified (Boolean)       # Has user verified email?
email_verified_at (DateTime)   # When was email verified?
mfa_enabled (Boolean)          # Is MFA activated?
mfa_method (Choice)            # TOTP, Email, or SMS

# Account Security
last_login_ip (IP)             # Track login location
last_login_at (DateTime)       # Track last login time
failed_login_attempts (Int)    # Count failures for lockout
account_locked_until (DateTime)# Temporary account lock
password_changed_at (DateTime) # Password security tracking
require_password_change (Boolean) # Force password change

# Timestamps
created_at (DateTime)          # Account creation time
updated_at (DateTime)          # Last profile update
last_activity (DateTime)       # Last user activity
is_deleted (Boolean)           # Soft delete flag
deleted_at (DateTime)          # When soft deleted
```

**Methods:**
- `is_account_locked()` - Check if account is currently locked
- `lock_account(duration_minutes=30)` - Lock account temporarily
- `unlock_account()` - Unlock and reset failures
- `increment_failed_login(max_attempts=5, lockout_duration=30)` - Track login failures
- `reset_failed_login()` - Reset failures on successful login

**Indexes:**
- email (unique)
- role + is_active
- email_verified + is_active
- mfa_enabled

**Permissions:**
- `can_view_audit_logs`
- `can_manage_users`
- `can_access_admin_panel`

---

### 2. **MFASettings Model**
**Database Table:** `mfa_settings`

Comprehensive MFA configuration per user.

**Key Fields:**
```
id (UUID)
user (OneToOne)                # One user, one MFA settings record

# Primary Method
primary_method (Choice)        # Which method is primary? TOTP/Email/SMS

# Enabled Methods
totp_enabled (Boolean)         # Is TOTP available?
email_enabled (Boolean)        # Is Email OTP available?
sms_enabled (Boolean)          # Is SMS OTP available?

# Backup Options
backup_codes_count (Int)       # How many backup codes?
backup_codes_generated_at (DateTime) # When generated?

# Security Settings
grace_period_minutes (Int)     # Grace period for MFA enforcement
require_on_login (Boolean)     # Require MFA every login?
require_on_sensitive_actions (Boolean) # MFA for sensitive ops?
remember_device_days (Int)     # Trust device for X days

# Verification Settings
code_length (Int)              # OTP code length (6-8 digits)
code_validity_seconds (Int)    # How long is OTP valid? (300-600s)
max_attempts (Int)             # Max failed attempts (3-5)

# Notifications
send_otp_via_email (Boolean)   # Send OTP codes via email?
send_alerts_on_mfa_changes (Boolean) # Alert on MFA changes?

# Activity Tracking
last_mfa_challenge_at (DateTime) # When was last MFA challenge?
last_method_used (Choice)      # Last MFA method used

# Status
is_enforced (Boolean)          # Is MFA mandatory?
enforcement_deadline (DateTime) # By when must user enable MFA?
```

**OneToOne Relationship with User** - Each user has exactly one MFA settings record

---

### 3. **MFAMethodPreference Model**
**Database Table:** `mfa_method_preferences`

Per-method customization (TOTP, Email, SMS independent configuration).

**Key Fields:**
```
id (UUID)
user (ForeignKey)              # Which user?
method (Choice)                # TOTP, Email, or SMS

# Enable/Disable
is_enabled (Boolean)           # Method available?
is_primary (Boolean)           # Is this the primary method?
is_backup (Boolean)            # Is this a backup method?

# Method-specific settings
code_length (Int)              # Code length for this method
code_validity_seconds (Int)    # Code validity time
max_attempts (Int)             # Max attempts for this method

# Notification preferences
send_otp_notification (Boolean) # Send OTP for this method?
require_for_login (Boolean)    # Require for login?
require_for_sensitive_actions (Boolean) # Required for sensitive ops?

# Rate limiting
max_otp_per_hour (Int)         # Max OTP requests per hour

# Status tracking
setup_completed (Boolean)      # Has user completed setup?
verified_at (DateTime)         # When verified?
last_used_at (DateTime)        # Last usage?
```

**Unique Constraint:** (user, method) - Only one preference per method per user

---

### 4. **MFAChangeLog Model**
**Database Table:** `mfa_change_logs`

Audit trail for all MFA setting modifications.

**Key Fields:**
```
id (UUID)
user (ForeignKey)              # Which user?
change_type (Choice)           # What changed? 12 types

# Details
description (Text)             # What exactly changed?
method (Choice)                # Which MFA method affected?

# Context
ip_address (IP)                # Where from?
user_agent (Text)              # What device?

# Who changed it
changed_by (ForeignKey)        # User who made change (might be admin)

# Data tracking
old_value (JSON)               # Previous setting value
new_value (JSON)               # New setting value
reason (Text)                  # Why was change made?

# Approval
requires_approval (Boolean)    # Does change need approval?
is_approved (Boolean)          # Is change approved?
```

**Change Types:**
- method_enabled / method_disabled
- primary_method_changed
- backup_method_added / removed
- settings_updated
- mfa_enforced / mfa_disabled
- recovery_codes_generated / regenerated

---

### 5. **Profile Model**
**Database Table:** `profiles`

Extended user information (separate from core User model).

**Key Fields:**
```
id (Int, auto-increment)
user (OneToOne)                # Link to User

# Personal Information
phone_number (String, 15)      # With validation regex
phone_verified (Boolean)       # Is phone verified?
date_of_birth (Date)           # User's birth date
avatar (Image)                 # Profile picture

# Address
address_line1 (String)         # Street address
address_line2 (String)         # Apt/Suite number
city (String)                  # City
state (String)                 # State/Province
country (String)               # Country
postal_code (String)           # ZIP/Postal code

# Preferences
timezone (String)              # User's timezone (UTC, EST, etc)
language (String)              # Preferred language (en, es, fr, etc)

# Privacy Settings
profile_visibility (Choice)    # Public, Private, Friends Only
```

**Methods:**
- Phone number validation using regex pattern
- Avatar upload to AWS S3 or local storage

---

### 6. **PasswordHistory Model**
**Database Table:** `password_history`

Prevents password reuse.

**Key Fields:**
```
id (Int, auto-increment)
user (ForeignKey)              # Which user?
password_hash (String)         # Hashed password (bcrypt)
changed_from_ip (IP)           # Where was password changed?
created_at (DateTime)          # When changed?
```

**Purpose:**
- Prevent users from reusing old passwords
- Require 5-10 unique passwords before reuse
- Track password change history

---

### 7. **Device Model**
**Database Table:** `devices`

Track user's devices for device-based authentication.

**Key Fields:**
```
id (UUID)
user (ForeignKey)              # Which user?

# Device Identification
fingerprint_hash (String, unique per user) # Device fingerprint
device_name (String)           # "John's iPhone"
device_type (Choice)           # Mobile, Tablet, Desktop, Unknown

# Browser & OS Information
browser (String)               # Chrome, Safari, Firefox
browser_version (String)       # 120.0
os (String)                    # iOS, Android, Windows, macOS
os_version (String)            # 17.2

# Network Information
ip_address (IP)                # Current IP
last_ip (IP)                   # Previous IP
is_deleted (Boolean)           # Soft delete

# Location (optional - GeoIP)
country (String)               # Country name
city (String)                  # City name
latitude (Float)               # Latitude coordinate
longitude (Float)              # Longitude coordinate

# Trust & Verification
is_verified (Boolean)          # Has user verified this device?
is_trusted (Boolean)           # Can this device skip MFA?
verified_at (DateTime)         # When verified?
trust_expires_at (DateTime)    # When does trust expire?

# Activity Tracking
last_used_at (DateTime)        # Last login from this device
first_used_at (DateTime)       # First seen date
total_logins (Int)             # Total login count

# Anomaly & Risk Detection
is_compromised (Boolean)       # Is device compromised?
risk_score (Int 0-100)         # Risk assessment score
last_risk_assessment (DateTime) # When was risk assessed?

# MFA Bypass
can_skip_mfa (Boolean)         # Can skip MFA on this device?
mfa_skip_until (DateTime)      # Until when can skip MFA?

# Security Notes
security_notes (Text)          # Admin notes about device
```

**Methods:**
- `mark_verified()` - Mark device as verified
- `mark_trusted(days=30)` - Trust device for N days
- `revoke_trust()` - Remove trust
- `mark_compromised()` - Mark as compromised
- `can_skip_mfa_now()` - Check if MFA can be skipped now
- `is_trust_expired()` - Check if trust period expired

**Unique Constraint:** (user, fingerprint_hash)

**Indexes:**
- user + is_trusted + is_deleted
- user + is_verified
- fingerprint_hash (for quick device lookup)
- last_used_at (for activity tracking)
- is_compromised (for security alerts)
- risk_score (for sorting risky devices)

---

### 8. **TrustedDevice Model**
**Database Table:** `trusted_devices`

Manages which devices are trusted by user (can skip MFA).

**Key Fields:**
```
id (UUID)
user (ForeignKey)              # Which user?
device (ForeignKey)            # Which device?

# Trust Details
device_name (String)           # Friendly name
trust_days (Int)               # How many days to trust? (30)
is_trusted (Boolean)           # Is currently trusted?
trusted_at (DateTime)          # When was it trusted?
expires_at (DateTime)          # When trust expires?

# Activity
last_verified_at (DateTime)    # Last verification time?
times_skipped_mfa (Int)        # How many times skipped MFA?

# Revocation
revoked_at (DateTime)          # When trust revoked?
revocation_reason (String)     # Why was it revoked?
is_deleted (Boolean)           # Soft delete?
```

**Relationship:** Many trusted devices per user

---

### 9. **Session Model**
**Database Table:** `sessions`

Active user sessions with JWT tokens.

**Key Fields:**
```
id (UUID)
user (ForeignKey)              # Which user?
device (ForeignKey, optional)  # Which device?

# Token Information
access_jti (String, unique)    # JWT ID for access token
refresh_jti (String, unique)   # JWT ID for refresh token

# Session Details
ip_address (IP)                # Session IP address
user_agent (Text)              # Browser info
session_type (Choice)          # Web, Mobile, API, Desktop

# Geographic Info
country (String)               # Country of session
city (String)                  # City of session

# Status
is_active (Boolean)            # Is session active?
revoked (Boolean)              # Has session been revoked?
revoked_at (DateTime)          # When revoked?
revocation_reason (String)     # Why revoked?

# Expiry
expires_at (DateTime)          # When does token expire?
last_activity (DateTime)       # Last activity time

# MFA Status
mfa_verified (Boolean)         # Is MFA verified?
mfa_verified_at (DateTime)     # When verified?
mfa_method_used (Choice)       # TOTP, Email, SMS, Backup

# Security
is_suspicious (Boolean)        # Suspicious activity detected?
suspicious_reason (String)     # What was suspicious?
requires_mfa_recheck (Boolean) # Needs MFA re-verification?

# Activity Metrics
total_requests (Int)           # Total HTTP requests
total_api_calls (Int)          # Total API calls
```

**Methods:**
- `is_expired()` - Check if session expired
- `revoke(reason='')` - Revoke session
- `mark_mfa_verified(mfa_method='')` - Mark MFA verified
- `mark_suspicious(reason='')` - Flag as suspicious
- `increment_requests()` - Increment request counter

**Indexes:**
- user + is_active
- user + created_at
- expires_at (for cleanup)
- access_jti (for token lookup)
- is_suspicious (for security alerts)

---

### 10. **RefreshTokenRecord Model**
**Database Table:** `refresh_tokens`

Track refresh token lifecycle for token rotation.

**Key Fields:**
```
id (UUID)
jti (String, unique)           # JWT ID of this token
session (ForeignKey)           # Which session?
user (ForeignKey)              # Which user?

# Token Rotation
parent_jti (String)            # Parent token JTI (for rotation chain)
rotation_count (Int)           # How many times rotated?

# Status
status (Choice)                # Active, Rotated, Revoked, Blacklisted, Expired
expires_at (DateTime)          # Token expiration time

# Revocation
revoked_at (DateTime)          # When revoked?
revocation_reason (String)     # Why revoked?
```

**Token Rotation Flow:**
```
1. User logs in → RefreshToken created (parent_jti = null)
2. User refreshes → New token created (parent_jti = old token's jti)
3. Old token marked as "rotated"
4. If old token is used again → BREACH DETECTED (rotation chain broken)
```

---

### 11. **AuditLog Model** (In Accounts App)
**Database Table:** `audit_logs`

Comprehensive security audit trail.

**Key Fields:**
```
id (UUID)
user (ForeignKey, optional)    # Which user? (null for system events)

# Event Details
event_type (Choice)            # 20+ types of events
severity (Choice)              # Low, Medium, High, Critical
description (Text)             # What happened?

# Request Context
ip_address (IP)                # From which IP?
user_agent (Text)              # Which device/browser?
device (ForeignKey, optional)  # Which device?

# Additional Data
metadata (JSON)                # Extra information
is_resolved (Boolean)          # Has admin reviewed?
resolved_at (DateTime)         # When resolved?
resolved_by (ForeignKey)       # Which admin resolved?
```

**Event Types (20+):**
- Authentication: login_success, login_failed, logout, session_expired
- Account: account_created, updated, deleted, locked, unlocked
- Password: password_changed, reset_requested, reset_completed
- MFA: mfa_enabled, mfa_disabled, mfa_verified, mfa_failed
- Device: device_added, device_verified, device_trusted, device_revoked
- Security: suspicious_activity, rate_limit_exceeded, unauthorized_access

---

## Relationships

### ER Diagram (Text Format):
```
User (1) ──────────── (1) MFASettings
  ├─ (1) ──────────── (1) Profile
  ├─ (1) ──────────── (1) NotificationPreferences
  ├─ (1) ──────────── (*) MFAMethodPreference
  ├─ (1) ──────────── (*) MFAChangeLog
  ├─ (1) ──────────── (*) Device
  ├─ (1) ──────────── (*) TrustedDevice
  ├─ (1) ──────────── (*) Session
  ├─ (1) ──────────── (*) PasswordHistory
  ├─ (1) ──────────── (*) RefreshTokenRecord
  ├─ (1) ──────────── (*) AuditLog
  └─ (1) ──────────── (*) Backup Codes, OTPs, etc.

Session (1) ─────── (0..1) Device
  └─ (1) ──────────── (*) RefreshTokenRecord

Device (1) ──────────── (*) TrustedDevice
  └─ (1) ──────────── (*) Session

TrustedDevice (1) ───── (1) Device
```

### Key Relationships:

**User → MFASettings:** OneToOne
- Every user has exactly one MFA settings record
- Created automatically when user registers
- Stores global MFA preferences

**User → MFAMethodPreference:** OneToMany
- User can have 3 method preferences (TOTP, Email, SMS)
- Each allows independent configuration
- Supports multi-method MFA

**User → Device:** OneToMany
- User can have multiple devices
- Unique together on (user, fingerprint_hash)
- Device activity tracked per user

**Device → Session:** OneToMany (optional)
- Multiple sessions can come from same device
- Session can exist without device (API clients)

**Session → RefreshTokenRecord:** OneToMany
- Each session generates refresh tokens
- Token rotation tracked
- Breach detection via rotation chain

**Device → TrustedDevice:** OneToOne
- Trusted status tracked separately
- Can revoke trust without deleting device
- Soft delete enabled

---

## Database Design

### Table Structure:

```sql
-- Core User Table (from AbstractUser + custom fields)
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(254) UNIQUE NOT NULL,
    username VARCHAR(150) NOT NULL,
    password VARCHAR(128) NOT NULL,
    role VARCHAR(10) NOT NULL DEFAULT 'user',
    
    -- Security
    email_verified BOOLEAN DEFAULT FALSE,
    email_verified_at TIMESTAMP NULL,
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_method VARCHAR(20),
    
    -- Account lockout
    failed_login_attempts INT DEFAULT 0,
    account_locked_until TIMESTAMP NULL,
    
    -- Tracking
    last_login_ip VARCHAR(45) NULL,
    last_login_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Soft delete
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP NULL
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_email_is_active ON users(email, is_active);
CREATE INDEX idx_users_role ON users(role, is_active);
CREATE INDEX idx_users_email_verified ON users(email_verified, is_active);
```

### Indexing Strategy:

**Primary Lookups:**
- `users.email` - All logins use email
- `users.id` - Foreign key lookups
- `devices.fingerprint_hash` - Device identification

**Security Queries:**
- `users.email + is_active` - Active user checks
- `devices.user_id + is_trusted` - Find trusted devices
- `sessions.user_id + is_active` - Active sessions

**Audit Queries:**
- `audit_logs.user_id + created_at` - User activity timeline
- `audit_logs.event_type + created_at` - Event type analysis
- `devices.last_used_at` - Activity timeline

**Range Queries:**
- `sessions.expires_at` - Find expired sessions
- `devices.trust_expires_at` - Find expired trusts
- `audit_logs.created_at` - Time-range queries

### Storage Estimates (1M users):

```
Base User Data:           ~500 MB (500 bytes per user)
Devices (avg 3/user):     ~1.5 GB
Sessions (avg 2/user):    ~1 GB
Audit Logs (daily):       ~50 MB/day = 18 GB/year
Password History (5/user):~500 MB
Total Year 1:             ~25 GB
Total Year 2+:            ~18 GB/year (audit only)
```

---

## Field Explanations

### UUID vs AutoIncrement:
```python
# ❌ BAD: Sequential IDs expose data
# User 1, 2, 3... → Attacker knows how many users
id = models.AutoField(primary_key=True)

# ✅ GOOD: UUID is random and cannot be guessed
# 550e8400-e29b-41d4-a716-446655440000
id = models.UUIDField(primary_key=True, default=uuid.uuid4)
```

### Email as Login Identifier:
```python
# ✅ Use email (unique, human-readable)
USERNAME_FIELD = 'email'
email = models.EmailField(unique=True, db_index=True)

# Advantages:
# - Users remember email
# - Email can be verified
# - Easier to recover account
# - Can send notifications to email
```

### MFA Method Choices:
```python
MFA_METHOD_CHOICES = [
    ('totp', 'TOTP'),   # Google Authenticator, Authy
    ('email', 'Email'), # OTP sent via email
    ('sms', 'SMS'),     # OTP sent via SMS
]

# TOTP: Recommended (doesn't need to send codes)
# Email: Good fallback (doesn't need phone)
# SMS: Needs phone number
```

### Role-Based Access Control:
```python
ROLE_CHOICES = [
    ('admin', 'Admin'),     # Full access, can manage users
    ('manager', 'Manager'), # Limited admin access
    ('user', 'User'),       # Regular user
]

# Automatically sets permissions:
# Admin → is_superuser=True, is_staff=True
# Manager → is_superuser=False, is_staff=True
# User → is_superuser=False, is_staff=False
```

---

## Methods & Functionality

### User Methods:

```python
user = User.objects.get(email='john@example.com')

# Account lockout
user.lock_account(duration_minutes=30)  # Lock for 30 min
user.is_account_locked()                 # Check if locked
user.unlock_account()                    # Unlock

# Failed login tracking
user.increment_failed_login(max_attempts=5)  # Increment & maybe lock
user.reset_failed_login()                # Reset on successful login

# Check if can login
if user.is_account_locked():
    return "Account locked, try again later"
if user.require_password_change:
    return "Must change password before login"
```

### Device Methods:

```python
device = Device.objects.get(id=device_id)

# Verification
device.mark_verified()  # Mark as verified device

# Trust management
device.mark_trusted(days=30)  # Trust for 30 days
device.revoke_trust()        # Remove trust

# Security
device.mark_compromised()    # Mark as compromised
device.can_skip_mfa_now()    # Check if MFA can be skipped
device.is_trust_expired()    # Check if trust expired
```

### Session Methods:

```python
session = Session.objects.get(access_jti=token_jti)

# Check validity
if session.is_expired():
    return "Session expired"
if not session.is_active:
    return "Session revoked"

# MFA verification
session.mark_mfa_verified('totp')  # Mark as MFA verified
session.mark_suspicious('Unusual location detected')

# Activity
session.increment_requests()  # Track API calls
```

---

## Best Practices

### 1. **Always Use UUIDs for IDs**
```python
# ✅ GOOD
id = models.UUIDField(primary_key=True, default=uuid.uuid4)

# ❌ BAD
id = models.AutoField(primary_key=True)  # Predictable
```

### 2. **Index Frequently Queried Fields**
```python
class Meta:
    indexes = [
        models.Index(fields=['user', 'is_active']),
        models.Index(fields=['created_at']),
        models.Index(fields=['fingerprint_hash']),
    ]
```

### 3. **Use Soft Deletes for Compliance**
```python
# Don't hard delete
device.delete()  # ❌ Data gone forever

# Use soft delete
device.soft_delete()  # ✅ Data retained, marked deleted
# Query: Device.objects.filter(is_deleted=False)
```

### 4. **Hash Sensitive Data**
```python
# ❌ DON'T: Store plaintext passwords
password_hash = models.CharField(max_length=255)
self.password_hash = password

# ✅ DO: Use Django's password hashers
from django.contrib.auth.hashers import make_password
self.password = make_password(password)
```

### 5. **Track Timestamps**
```python
# ✅ GOOD: Track all important times
email_verified_at = models.DateTimeField(null=True, blank=True)
last_login_at = models.DateTimeField(null=True, blank=True)
password_changed_at = models.DateTimeField(null=True, blank=True)

# Enables:
# - Password aging (change every 90 days)
# - Email verification tracking
# - Activity monitoring
```

### 6. **Use OneToOne for Single Relationships**
```python
# ✅ GOOD: User has exactly one profile
user_profile = models.OneToOneField(User, ...)

# ❌ BAD: If user might not have profile
user_profile = models.ForeignKey(User, ...)
```

### 7. **Use Foreign Keys with Cascading**
```python
# ✅ DELETE CASCADE: When user deleted, delete their devices
device = models.ForeignKey(User, on_delete=models.CASCADE)

# ✅ SET_NULL: Keep sessions when device deleted
session_device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True)

# ❌ Don't use PROTECT unless you have good reason
```

### 8. **Implement Query Optimization**
```python
# ❌ N+1 query problem
for user in User.objects.all():
    print(user.profile.timezone)  # Query per user!

# ✅ Use select_related for OneToOne
users = User.objects.select_related('profile')

# ✅ Use prefetch_related for OneToMany
users = User.objects.prefetch_related('devices')
```

---

## Future Enhancements

### 1. **Two-Factor Authentication via Push Notifications**
```python
# Add push notification support
class PushNotificationMFA(models.Model):
    user = models.OneToOneField(User, ...)
    push_device_token = models.CharField(max_length=500)
    is_verified = models.BooleanField(default=False)
    
    # Send push notification instead of SMS/Email
    # Faster, doesn't cost money
    # Better UX than entering codes
```

### 2. **Biometric Authentication**
```python
class BiometricAuth(models.Model):
    user = models.OneToOneField(User, ...)
    fingerprint_data = models.BinaryField()  # Encrypted
    face_data = models.BinaryField()         # Encrypted
    iris_data = models.BinaryField()         # Encrypted
    is_enabled = models.BooleanField(default=False)
    
    # For mobile apps (fingerprint, face ID)
    # No codes to enter, faster, more secure
```

### 3. **Passwordless Authentication**
```python
class PasswordlessAuth(models.Model):
    user = models.OneToOneField(User, ...)
    magic_link_enabled = models.BooleanField(default=False)
    passkey_enabled = models.BooleanField(default=False)
    
    # Magic links: "Click here to login"
    # Passkeys: WebAuthn standard
    # No password needed!
```

### 4. **Geographic Velocity Check**
```python
class LocationHistory(models.Model):
    user = models.ForeignKey(User, ...)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def is_impossible_travel(self):
        """
        Check if user traveled too far too fast
        E.g., New York to Tokyo in 2 hours = impossible
        """
        last_location = LocationHistory.objects.filter(
            user=self.user
        ).order_by('-timestamp').first()
        
        if not last_location:
            return False
            
        distance = calculate_distance(
            last_location.latitude, last_location.longitude,
            self.latitude, self.longitude
        )
        
        # Max speed: ~900 mph for commercial flights
        max_distance = (900 * time_diff_hours)
        return distance > max_distance
```

### 5. **Risk-Based Authentication (Adaptive MFA)**
```python
class RiskAssessment(models.Model):
    user = models.ForeignKey(User, ...)
    session = models.ForeignKey(Session, ...)
    risk_score = models.IntegerField(0-100)
    
    # Factors:
    # - Is device trusted? (-20 points)
    # - Is location normal? (-10 points)
    # - Is time normal? (-5 points)
    # - Is IP new? (+20 points)
    # - Is impossible travel? (+50 points)
    # - Multiple failed logins? (+30 points)
    # - Unusual user agent? (+10 points)
    
    # Actions based on risk:
    # - risk < 20: Allow login
    # - 20 < risk < 50: Require MFA
    # - risk > 50: Require strong MFA (TOTP only)
    # - risk > 80: Require email confirmation + MFA
```

### 6. **Account Takeover Detection**
```python
class AccountTakeoverDetection(models.Model):
    user = models.ForeignKey(User, ...)
    
    # Detect if attacker took over account by:
    # - Change primary email to new address
    # - Disable MFA
    # - Create API key
    # - Access from new location + device
    # - Too many password reset attempts
    
    def detect_takeover(self):
        """
        ML model trained on:
        - User's normal behavior
        - Typical login times
        - Typical devices/locations
        - Account changes
        """
        pass
```

### 7. **Session Sharing Detection**
```python
class SessionShare Detection(models.Model):
    user = models.ForeignKey(User, ...)
    
    # Detect if user shared session with others:
    # - Multiple IPs using same refresh_jti
    # - Multiple user agents from same session
    # - Concurrent requests from different cities
    # - Requests from known proxy IPs
    
    def is_session_shared(self, session):
        """Detect if session being used by multiple people"""
        pass
```

### 8. **Integration with External Auth**
```python
class ExternalAuth(models.Model):
    user = models.ForeignKey(User, ...)
    provider = models.CharField(max_length=50)  # Google, GitHub, etc
    provider_id = models.CharField(max_length=255)
    email = models.EmailField()  # From provider
    name = models.CharField(max_length=255)
    
    # OAuth2 / OpenID Connect
    # Login with Google/GitHub/Facebook
    # Faster for users
    # Leverages their 2FA
```

### 9. **Device Jailbreak/Root Detection**
```python
class DeviceHealth(models.Model):
    device = models.OneToOneField(Device, ...)
    is_jailbroken = models.BooleanField(default=False)  # iOS jailbreak
    is_rooted = models.BooleanField(default=False)      # Android root
    has_debugger = models.BooleanField(default=False)
    
    # For mobile apps:
    # - Can't protect from jailbroken/rooted devices
    # - Flag them, require stronger auth
    # - Or refuse access entirely
```

### 10. **Rate Limiting Per Device**
```python
class DeviceRateLimit(models.Model):
    device = models.OneToOneField(Device, ...)
    requests_per_minute = models.IntegerField(default=60)
    requests_per_hour = models.IntegerField(default=3600)
    requests_per_day = models.IntegerField(default=86400)
    
    # Different limits per device
    # Trusted devices: higher limits
    # Suspicious devices: lower limits
    # API clients: custom limits
```

---

## Summary

The **ACCOUNTS** app provides a comprehensive, secure foundation for user authentication and management. It includes:

✅ **Security Features:**
- Role-based access control
- Account lockout mechanisms
- Password history tracking
- Device fingerprinting
- Session management with JWT tokens
- MFA settings and preferences
- Comprehensive audit logging

✅ **Scalability:**
- UUID primary keys
- Proper indexing strategy
- Soft deletes for data retention
- Prepared for millions of users

✅ **Flexibility:**
- Support for 3 MFA methods
- Per-method configuration
- Trusted device management
- Granular audit logging

✅ **Future-Ready:**
- Extensible for biometrics
- Risk-based authentication
- Passwordless auth
- External authentication

---

