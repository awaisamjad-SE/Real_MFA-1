# OTP APP - Complete Documentation

## ðŸ“‹ Table of Contents
1. [Overview](#overview)
2. [Models](#models)
3. [Relationships](#relationships)
4. [Database Design](#database-design)
5. [OTP Flow & Security](#otp-flow--security)
6. [TOTP Implementation](#totp-implementation)
7. [Best Practices](#best-practices)
8. [Future Enhancements](#future-enhancements)

---

## Overview

The **OTP** (One-Time Password) app handles all aspects of temporary password generation and verification for:
- Email verification
- Phone verification
- Device verification
- Password reset
- Login 2FA (two-factor authentication)
- Sensitive action verification

**Key Features:**
- Time-limited OTP codes (5 minutes default)
- Multiple purpose types
- Attempt tracking and lockout
- TOTP/Google Authenticator support
- Backup codes for account recovery
- MFA challenges tracking
- Email/SMS MFA method configuration

---

## Models

### 1. **OTP Model**
**Database Table:** `otps`

Stores temporary one-time password codes sent to users.

**Key Fields:**
```
id (UUID)
user (ForeignKey)              # Which user?

# OTP Details
code_hash (String)             # Hashed OTP code (not plaintext!)
purpose (Choice)               # Email verification, phone, device, etc
target (String)                # Email or phone number

# Security
attempts (Int)                 # Failed attempts so far
max_attempts (Int)             # Max failed attempts (default: 3)
ip_address (IP)                # From which IP?

# Status
is_used (Boolean)              # Has OTP been used?
used_at (DateTime)             # When was it used?

# Expiry
expires_at (DateTime)          # When does OTP expire?
created_at (DateTime)          # When was OTP generated?
```

**Purpose Types:**
- `email_verification` - Verify user's email address
- `phone_verification` - Verify user's phone number
- `device_verification` - Verify new device login
- `password_reset` - Verify identity during password reset
- `login_2fa` - Two-factor authentication during login
- `sensitive_action` - Verify before sensitive operations

**Methods:**
```python
otp = OTP.objects.get(id=otp_id)

# Check if valid (not used, not expired, attempts remaining)
if otp.is_valid():
    print("OTP is still valid")
else:
    print("OTP is invalid/expired/used")

# Increment failed attempts
otp.increment_attempts()  # If reaches max, user locked out

# Mark as used
otp.mark_used()  # Sets is_used=True, used_at=now()
```

**Indexes:**
- user + purpose + is_used (find active OTPs)
- expires_at (find expired OTPs for cleanup)
- code_hash (verify OTP code)

**Database Cleanup:**
```sql
-- Delete expired OTPs daily
DELETE FROM otps WHERE expires_at < NOW();
-- This prevents database bloat
```

---

### 2. **TOTPDevice Model**
**Database Table:** `totp_devices`

Stores TOTP secret for Google Authenticator/Authy integration.

**Key Fields:**
```
id (UUID)
user (OneToOne)                # Each user has one TOTP device

# TOTP Configuration
secret (String)                # Base32-encoded secret key
                              # Used to generate codes in Authenticator app

# Status
is_verified (Boolean)          # Has user proved they saved secret?
verified_at (DateTime)         # When verified?

# Backup Codes
backup_codes_generated_at (DateTime) # When were backup codes generated?

# Usage Stats
last_used_at (DateTime)        # Last successful TOTP code used
total_verifications (Int)      # How many times verified?
failed_attempts (Int)          # Failed verification attempts
```

**TOTP Flow:**
```
1. User requests TOTP setup
2. Server generates random secret (Base32)
3. Server shows QR code (encodes secret + user info)
4. User scans QR with Google Authenticator app
5. App generates 6-digit codes every 30 seconds
6. User enters code to prove they saved it
7. Server verifies code matches algorithm
8. TOTP is now enabled
```

**Secret Generation:**
```python
import pyotp

# Generate random secret (Base32)
secret = pyotp.random_base32()
# Output: "ABC12XYZ9DEFGHIJ5KLMNOP8QRSTUV="

# Create QR code for user to scan
qr_code = pyotp.totp.TOTP(secret).provisioning_uri(
    name='user@example.com',
    issuer_name='Real_MFA'
)
# Output: otpauth://totp/Real_MFA:user@example.com?secret=ABC12XYZ...&issuer=Real_MFA

# User scans QR with phone
# Phone app generates codes using TOTP algorithm
```

**Verification:**
```python
totp = pyotp.TOTP(device.secret)

# User enters code from authenticator app
user_code = request.POST.get('code')

# Verify code (with 30-second window for clock skew)
if totp.verify(user_code, valid_window=1):
    print("Valid TOTP code!")
    device.mark_verified()
else:
    print("Invalid TOTP code")
    device.failed_attempts += 1
```

---

### 3. **BackupCode Model**
**Database Table:** `backup_codes`

Recovery codes for account access when TOTP unavailable.

**Key Fields:**
```
id (UUID)
user (ForeignKey)              # Which user?

# Code Storage
code_hash (String)             # Hashed backup code
                              # DO NOT store plaintext!

# Usage Tracking
is_used (Boolean)              # Has code been used?
used_at (DateTime)             # When was it used?
used_from_ip (IP)              # From which IP used?

# Timestamps
created_at (DateTime)          # When generated?
```

**Backup Code Generation:**
```python
import secrets

# Generate 10 backup codes
backup_codes = []
for _ in range(10):
    # Generate random code: "ABC1-DEF2-GHI3"
    code = f"{secrets.token_hex(3)}-{secrets.token_hex(3)}-{secrets.token_hex(3)}"
    backup_codes.append(code)

# Hash and store
from django.contrib.auth.hashers import make_password
for code in backup_codes:
    BackupCode.objects.create(
        user=user,
        code_hash=make_password(code)
    )
```

**Usage Flow:**
```
1. User lost phone with authenticator
2. User enters backup code instead of TOTP
3. System verifies backup code matches hash
4. System marks backup code as used (can't reuse)
5. User now has access, can set up new TOTP
```

**Best Practices:**
```python
# âœ… Generate 10 backup codes
# - User writes them down / saves to password manager
# - Codes good for account recovery emergency

# âœ… Display codes only once
# - After user saves them
# - Never show again
# - User responsible for saving

# âœ… Each code = one use
# - Can't reuse backup codes
# - User has 10 attempts to recover
# - After 10 uses, need new codes
```

---

### 4. **MFAChallenge Model**
**Database Table:** `mfa_challenges`

Tracks active MFA challenges sent to users during login.

**Key Fields:**
```
id (UUID)
user (ForeignKey)              # Which user?

# Challenge Details
challenge_type (Choice)        # TOTP, Email OTP, SMS OTP, Backup Code
status (Choice)                # Pending, Verified, Failed, Expired

# Context
session_id (String)            # Login session ID
ip_address (IP)                # From which IP?
user_agent (Text)              # Which device/browser?

# Verification Attempts
attempts (Int)                 # Failed attempts
max_attempts (Int)             # Max allowed (default: 3)

# Timing
expires_at (DateTime)          # When challenge expires?
verified_at (DateTime)         # When verified?

# Device used for verification
verified_device (ForeignKey)   # Which device verified?

# Risk Assessment
risk_level (Choice)            # Low, Medium, High, Critical
```

**MFA Challenge Flow:**
```
1. User enters email + password (passed)
2. System creates MFAChallenge (pending)
3. System sends OTP (if email/SMS) or displays TOTP prompt
4. User enters code
5. If correct: MFAChallenge marked as verified
6. If wrong: attempts incremented
7. If max attempts reached: challenge marked as failed
8. If expires: challenge marked as expired
9. After verification: Session marked as mfa_verified=True
```

**Methods:**
```python
challenge = MFAChallenge.objects.get(id=challenge_id)

# Check if still valid
if challenge.is_valid():
    print("Challenge still active")

# Record failed attempt
challenge.increment_attempts()

# Mark as verified
challenge.mark_verified(device=user_device)

# Mark as expired
challenge.mark_expired()
```

---

### 5. **EmailMFAMethod Model**
**Database Table:** `email_mfa_methods`

Stores email-based MFA configuration.

**Key Fields:**
```
id (UUID)
user (OneToOne)                # User's email MFA setting

# Configuration
email (EmailField)             # Which email to send OTPs to
is_verified (Boolean)          # Has email been verified?
verified_at (DateTime)         # When verified?
is_enabled (Boolean)           # Is email MFA active?

# Usage Stats
last_used_at (DateTime)        # When last used?
total_verifications (Int)      # How many times verified?
failed_attempts (Int)          # Failed attempts
```

**Email MFA Flow:**
```
1. User enables email MFA
2. System sends verification code to email
3. User enters code to verify they control email
4. Email MFA now enabled
5. On login: System sends OTP to email
6. User checks email, enters code
7. Login successful
```

**Advantages:**
- âœ… No phone needed
- âœ… Works globally (no SMS fees)
- âœ… User already has email

**Disadvantages:**
- âŒ Slower (need to check email)
- âŒ Less secure (email can be compromised)
- âŒ Dependent on email service uptime

---

### 6. **SMSMFAMethod Model**
**Database Table:** `sms_mfa_methods`

Stores SMS-based MFA configuration.

**Key Fields:**
```
id (UUID)
user (OneToOne)                # User's SMS MFA setting

# Configuration
phone_number (String)          # Phone number (validated)
is_verified (Boolean)          # Has phone been verified?
verified_at (DateTime)         # When verified?
is_enabled (Boolean)           # Is SMS MFA active?

# Usage Stats
last_used_at (DateTime)        # When last used?
total_verifications (Int)      # How many times verified?
failed_attempts (Int)          # Failed attempts
```

**SMS MFA Flow:**
```
1. User enters phone number
2. System sends verification code via SMS
3. User enters code to verify they control phone
4. SMS MFA now enabled
5. On login: System sends OTP via SMS
6. User receives text, enters code
7. Login successful
```

**Advantages:**
- âœ… Fast (SMS nearly instant)
- âœ… No app needed
- âœ… Familiar to users

**Disadvantages:**
- âŒ SMS can be intercepted (not encrypted)
- âŒ Costs money per SMS
- âŒ SIM swap attacks possible
- âŒ Not available in all countries

---

### 7. **MFARecovery Model**
**Database Table:** `mfa_recoveries`

Tracks account recovery attempts.

**Key Fields:**
```
id (UUID)
user (ForeignKey)              # Which user?

# Recovery Details
recovery_type (Choice)         # Backup code, Email, SMS, Support
ip_address (IP)                # From which IP?
user_agent (Text)              # Which device?

# Status
is_successful (Boolean)        # Did recovery succeed?
verified_at (DateTime)         # When verified?

# Notes
notes (Text)                   # Admin notes about recovery
```

**Recovery Types:**
- `backup_code` - User used backup code
- `email_recovery` - User used email recovery
- `sms_recovery` - User used SMS recovery
- `support_recovery` - Admin helped user recover

**Recovery Scenarios:**
```
Scenario 1: Lost phone with TOTP
â†’ User has backup codes
â†’ User enters backup code
â†’ System verifies code
â†’ User can now reset TOTP

Scenario 2: Lost phone AND lost backup codes
â†’ User contacts support
â†’ Support verifies identity (questions, documents)
â†’ Support disables old TOTP
â†’ User sets up new TOTP
â†’ MFARecovery logged for audit
```

---

## Relationships

### ER Diagram:
```
User (1) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ (1) TOTPDevice
  â”œâ”€ (1) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ (1) EmailMFAMethod
  â”œâ”€ (1) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ (1) SMSMFAMethod
  â”œâ”€ (1) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ (*) BackupCode
  â”œâ”€ (1) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ (*) OTP
  â”œâ”€ (1) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ (*) MFAChallenge
  â””â”€ (1) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ (*) MFARecovery

MFAChallenge (0..1) â”€â”€â”€â”€â”€â”€â”€â”€ (*) Device
```

### Relationship Descriptions:

**User â†’ TOTPDevice:** OneToOne
- Each user has at most one TOTP device
- TOTP is optional (not required)

**User â†’ EmailMFAMethod:** OneToOne
- Each user has at most one email MFA config
- Email MFA is optional

**User â†’ SMSMFAMethod:** OneToOne
- Each user has at most one SMS MFA config
- SMS MFA is optional

**User â†’ BackupCode:** OneToMany
- User can have 10 backup codes
- Each code single-use
- Generated when setting up TOTP

**User â†’ OTP:** OneToMany
- Multiple active OTPs per user (different purposes)
- Usually 1-3 active OTPs at a time

**User â†’ MFAChallenge:** OneToMany
- Multiple active challenges during login
- Usually 1 active per login attempt

---

## Database Design

### OTP Table Structure:
```sql
CREATE TABLE otps (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    code_hash VARCHAR(255) NOT NULL,
    purpose VARCHAR(30) NOT NULL,
    target VARCHAR(255) NOT NULL,

    attempts INT DEFAULT 0,
    max_attempts INT DEFAULT 3,
    ip_address VARCHAR(45),

    is_used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP NULL,

    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_otps_user_purpose_used ON otps(user_id, purpose, is_used);
CREATE INDEX idx_otps_expires_at ON otps(expires_at);
CREATE INDEX idx_otps_code_hash ON otps(code_hash);
```

### Storage Estimates (1M users with 2 active OTPs each):
```
Base OTP data:         ~2 GB (2 records per user)
TOTP devices:          ~500 MB (50% have TOTP)
Backup codes (10 each):~1 GB (50% have codes)
MFA challenges:        ~500 MB (transient, deleted after 10 min)
MFA recovery logs:     ~100 MB/year

Total:                 ~4.5 GB + 100 MB/year
```

### Cleanup Jobs:

**Daily OTP Cleanup:**
```python
from django.core.management.base import BaseCommand
from otp.models import OTP

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Delete OTPs older than 1 hour
        OTP.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()
```

**Backup Code Cleanup:**
```python
# Mark all backup codes as used if user hasn't accessed account in 2 years
old_users = User.objects.filter(
    last_activity__lt=timezone.now() - timedelta(days=730)
)
for user in old_users:
    BackupCode.objects.filter(user=user, is_used=False).update(
        is_used=True
    )
```

---

## OTP Flow & Security

### Generation:
```python
import secrets

# Generate 6-digit OTP
code = secrets.randbelow(999999)
code = str(code).zfill(6)  # "123456"

# Hash before storing
from django.contrib.auth.hashers import make_password
code_hash = make_password(code)

# Store hashed code in database
OTP.objects.create(
    user=user,
    code_hash=code_hash,
    purpose='login_2fa',
    target=user.email,
    expires_at=timezone.now() + timedelta(minutes=5)
)

# Send to user (never store plaintext!)
send_email(
    to=user.email,
    subject='Your OTP Code',
    body=f'Enter this code: {code}'  # Plain code in email, not hash!
)
```

### Verification:
```python
# User submits code
submitted_code = "123456"

# Get OTP record
otp = OTP.objects.get(user=user, purpose='login_2fa', is_used=False)

# Check expiration
if timezone.now() > otp.expires_at:
    otp.status = 'expired'
    otp.save()
    return "OTP expired"

# Check attempts
if otp.attempts >= otp.max_attempts:
    otp.status = 'failed'
    otp.save()
    return "Too many attempts"

# Verify code
from django.contrib.auth.hashers import check_password
if check_password(submitted_code, otp.code_hash):
    otp.mark_used()
    return "Login successful"
else:
    otp.increment_attempts()
    return "Invalid OTP code"
```

### Security Best Practices:

**1. Never store plaintext OTP:**
```python
# âŒ BAD
code = "123456"
OTP.objects.create(code=code)  # Plaintext in database!

# âœ… GOOD
code_hash = make_password(code)
OTP.objects.create(code_hash=code_hash)  # Hashed
```

**2. Send over secure channel:**
```python
# âœ… Good channels:
# - Email (HTTPS, encrypted inbox)
# - SMS (encrypted by carrier)
# - Push notification (encrypted)

# âŒ Bad channels:
# - Plaintext email body
# - HTTP (unencrypted)
```

**3. Time-limit OTPs:**
```python
# âœ… GOOD: 5-10 minute expiry
expires_at = timezone.now() + timedelta(minutes=5)

# âŒ BAD: No expiry
expires_at = None  # Code valid forever!
```

**4. Rate limit OTP requests:**
```python
# âœ… GOOD: Max 5 OTP requests per hour per user
OTP_requests_today = OTP.objects.filter(
    user=user,
    created_at__gte=timezone.now() - timedelta(hours=1)
).count()

if OTP_requests_today >= 5:
    raise RateLimitError("Too many OTP requests")
```

**5. Attempt limiting:**
```python
# âœ… GOOD: Max 3 failed attempts
if otp.attempts >= 3:
    otp.mark_failed()
    user.lock_account(duration_minutes=30)  # Temporary lockout
```

---

## TOTP Implementation

### How TOTP Works:

```
TOTP = Time-based One-Time Password

1. Server has secret: "ABC12XYZ9DEFGHIJ5KLMNOP8QRSTUV="
2. Server shares secret with authenticator app via QR code
3. Every 30 seconds, both generate same 6-digit code using:
   - Secret key
   - Current Unix timestamp
   - HMAC-SHA1 hash function
4. Code is valid for 30 seconds, then new code generated
5. User enters code to prove they have the secret

Advantages:
âœ… No internet needed (works offline)
âœ… No server needs to send OTP
âœ… Codes generated locally on phone
âœ… Fast (instant)
âœ… Cheap (no SMS cost)
âœ… Secure (HMAC-SHA1)

Disadvantages:
âŒ Need to keep phone with app
âŒ Phone can be lost/stolen
âŒ Need backup codes for recovery
âŒ Time synchronization issues
```

### TOTP Algorithm:
```python
import hmac
import hashlib
from base64 import b32decode
import struct
import time

def generate_totp_code(secret, current_timestamp=None):
    """Generate TOTP code"""
    if current_timestamp is None:
        current_timestamp = int(time.time())

    # Time counter (30-second intervals)
    time_counter = current_timestamp // 30

    # Convert counter to bytes
    counter_bytes = struct.pack('>Q', time_counter)

    # HMAC-SHA1
    secret_bytes = b32decode(secret)
    hmac_hash = hmac.new(
        secret_bytes,
        counter_bytes,
        hashlib.sha1
    ).digest()

    # Extract 4-byte dynamic code
    offset = hmac_hash[-1] & 0xf
    code_int = struct.unpack('>I', hmac_hash[offset:offset + 4])[0]
    code_int = code_int & 0x7fffffff

    # Get last 6 digits
    code = code_int % 1000000

    return str(code).zfill(6)

# User scans QR, phone generates codes automatically
code1 = generate_totp_code("ABC12XYZ9DEFGHIJ5KLMNOP8QRSTUV=")
# Output: "123456"

# 30 seconds later
code2 = generate_totp_code("ABC12XYZ9DEFGHIJ5KLMNOP8QRSTUV=")
# Output: "654321"
```

### Verification with Clock Skew:
```python
import pyotp

def verify_totp(secret, code, valid_window=1):
    """
    Verify TOTP code with clock skew tolerance

    valid_window=1 means:
    - Accept codes from 30 seconds ago
    - Accept codes from now
    - Accept codes from 30 seconds in future
    - Total window: 90 seconds
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=valid_window)

# User enters "123456" from phone
# Server might be few seconds ahead/behind
# valid_window allows for this small time difference
result = verify_totp(secret, "123456", valid_window=1)
# Returns: True or False
```

---

## Best Practices

### 1. **Multiple MFA Methods (Defense in Depth)**
```python
# âœ… GOOD: User can have multiple methods
user.mfa_settings.totp_enabled = True    # TOTP primary
user.mfa_settings.email_enabled = True   # Email backup
user.mfa_settings.sms_enabled = True     # SMS backup

# On login: Try TOTP first, if unavailable try email/SMS
```

### 2. **Backup Codes (Account Recovery)**
```python
# âœ… GOOD: Generate 10 backup codes
backup_codes = []
for _ in range(10):
    code = generate_backup_code()
    backup_codes.append(code)

# Display once, user saves to password manager
# If phone lost: user can use backup code to login

# Each code = one-time use
# After using all 10: user needs new codes
```

### 3. **Rate Limiting OTP Requests**
```python
# âœ… GOOD: Limit OTP generation
if OTP.objects.filter(
    user=user,
    created_at__gte=timezone.now() - timedelta(hours=1)
).count() >= 5:
    raise RateLimitError("Try again in 1 hour")
```

### 4. **Attempt Limiting with Lockout**
```python
# âœ… GOOD: Lock after 3 failed attempts
if otp.attempts >= 3:
    user.lock_account(duration_minutes=30)
    send_security_alert(user, "3 failed MFA attempts")
```

### 5. **Monitor Failed MFA Attempts**
```python
# âœ… GOOD: Alert on suspicious activity
failed_otps = OTP.objects.filter(
    user=user,
    is_used=False,
    attempts__gte=2,
    created_at__gte=timezone.now() - timedelta(hours=1)
)

if failed_otps.count() >= 3:
    send_email(user.email, subject="Security Alert: Multiple failed login attempts")
```

---

## Future Enhancements

### 1. **WebAuthn/FIDO2 Support**
```python
class WebAuthnCredential(models.Model):
    user = models.ForeignKey(User, ...)
    credential_id = models.BinaryField()
    public_key = models.BinaryField()
    counter = models.PositiveIntegerField()
    transports = models.JSONField(default=list)

    # Hardware security keys (Yubikey, etc)
    # Most secure MFA method
    # Also works as passwordless auth
```

### 2. **Passkeys (WebAuthn)**
```python
# Passkeys are WebAuthn credentials stored locally
# - Face ID / Fingerprint on phone
# - PIN on security key
# - Password on computer

# Login:
# 1. Enter email
# 2. Phone/key asks for biometric
# 3. No password needed!
# 4. No 6-digit code needed!

# More secure + better UX
```

### 3. **Push Notification MFA**
```python
class PushMFARequest(models.Model):
    user = models.ForeignKey(User, ...)
    device_token = models.CharField(max_length=500)
    challenge = models.CharField(max_length=255)

    # Instead of entering code:
    # 1. Server sends push notification to phone
    # 2. User sees "Approve login from New York?"
    # 3. User taps "Approve"
    # 4. Phone confirms with server
    # 5. Login complete

    # Faster than typing codes
    # Can see device/location context
    # Better UX
```

### 4. **Risk-Based OTP Delivery**
```python
class RiskBasedOTP(models.Model):
    user = models.ForeignKey(User, ...)
    risk_score = models.IntegerField()  # 0-100

    # Low risk (trusted device, normal location, normal time):
    # â†’ Don't send OTP, allow login

    # Medium risk (new device, unusual location):
    # â†’ Send email OTP (slower, more verification)

    # High risk (impossible travel, multiple failed logins):
    # â†’ Send SMS OTP + require security questions

    # Critical risk:
    # â†’ Require strong authentication + support contact
```

### 5. **Hardware Security Keys**
```python
class SecurityKey(models.Model):
    user = models.ForeignKey(User, ...)
    key_type = models.CharField(max_length=50)  # Yubikey, etc
    key_id = models.CharField(max_length=255)
    public_key = models.BinaryField()

    # Physical USB security key
    # Insert into computer, authenticate with physical button
    # Cannot be hacked remotely
    # Cannot be phished (bound to domain)
```

---

## Summary

The **OTP** app provides comprehensive one-time password management:

âœ… **OTP Generation & Verification**
- Time-limited codes (5-10 minutes)
- Attempt tracking and lockout
- Multiple purpose types
- Hashed storage (never plaintext)

âœ… **TOTP/Google Authenticator Support**
- Industry-standard algorithm
- Works offline
- No SMS costs
- Backup codes for recovery

âœ… **Multiple MFA Methods**
- Email OTP (worldwide, free)
- SMS OTP (fast, familiar)
- TOTP (most secure, offline)
- Backup codes (recovery)

âœ… **Security Features**
- Rate limiting
- Attempt limiting
- Account lockout
- Challenge tracking
- Recovery tracking

âœ… **Scalable Design**
- Proper indexing
- Automatic cleanup
- Audit logging
- Risk assessment

---

