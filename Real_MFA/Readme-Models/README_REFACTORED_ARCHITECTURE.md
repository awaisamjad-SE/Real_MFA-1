# REFACTORED ARCHITECTURE - Device & Session Separation

## Summary of Changes

Device and Session models have been extracted from the **accounts** app into dedicated apps for better separation of concerns and scalability.

---

## App Structure After Refactoring

```
accounts/
  â”œâ”€â”€ models.py (User, Profile, MFASettings, MFAMethodPreference,
  â”‚             MFAChangeLog, PasswordHistory, RefreshTokenRecord, AuditLog)
  â”œâ”€â”€ admin.py
  â”œâ”€â”€ views.py
  â””â”€â”€ migrations/

devices/  âœ¨ NEW APP
  â”œâ”€â”€ models.py (Device, TrustedDevice)
  â”œâ”€â”€ admin.py
  â”œâ”€â”€ views.py
  â””â”€â”€ migrations/

sessions/  âœ¨ NEW APP
  â”œâ”€â”€ models.py (Session)
  â”œâ”€â”€ admin.py
  â”œâ”€â”€ views.py
  â””â”€â”€ migrations/

otp/
  â”œâ”€â”€ models.py
  â”œâ”€â”€ admin.py
  â””â”€â”€ ...

notifications/
  â”œâ”€â”€ models.py
  â”œâ”€â”€ admin.py
  â””â”€â”€ ...

audit_log/
  â”œâ”€â”€ models.py
  â”œâ”€â”€ admin.py
  â””â”€â”€ ...
```

---

## Models Location Changes

### âœ… MOVED TO DEVICES APP

```python
# From: accounts/models.py
# To: devices/models.py

class Device(TimeStampedModel, SoftDeleteModel):
    """Track user devices with fingerprinting, verification, and trust management"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # ... all device fields ...

class TrustedDevice(TimeStampedModel, SoftDeleteModel):
    """Manage device trust for MFA bypass"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    # ... all trust fields ...
```

**Reason:** Device management is a specialized concern separate from user account management.

### âœ… MOVED TO SESSIONS APP

```python
# From: accounts/models.py
# To: sessions/models.py

class Session(TimeStampedModel):
    """Track active user sessions with JWT tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    device = models.ForeignKey(Device, on_delete=models.SET_NULL)
    # ... all session fields ...
```

**Reason:** Session lifecycle is independent and benefits from isolated management and scaling.

### âœ… REMAINED IN ACCOUNTS APP

```python
# Stays in: accounts/models.py

class User(AbstractUser, SoftDeleteModel)
class Profile(TimeStampedModel)
class MFASettings(TimeStampedModel)
class MFAMethodPreference(TimeStampedModel)
class MFAChangeLog(TimeStampedModel)
class PasswordHistory(TimeStampedModel)
class RefreshTokenRecord(TimeStampedModel)
class AuditLog(TimeStampedModel)
```

---

## ForeignKey Reference Updates

### In accounts/models.py

```python
# OLD:
class RefreshTokenRecord(TimeStampedModel):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    device = models.ForeignKey(Device, null=True, blank=True)

# NEW (String references):
class RefreshTokenRecord(TimeStampedModel):
    session = models.ForeignKey('sessions.Session', on_delete=models.CASCADE)
    device = models.ForeignKey('devices.Device', null=True, blank=True)

# OLD:
class AuditLog(TimeStampedModel):
    device = models.ForeignKey(Device, null=True, blank=True)

# NEW (String reference):
class AuditLog(TimeStampedModel):
    device = models.ForeignKey('devices.Device', null=True, blank=True)
```

### In otp/models.py

```python
# OLD:
class MFAChallenge(TimeStampedModel):
    verified_device = models.ForeignKey('accounts.Device', ...)

# NEW:
class MFAChallenge(TimeStampedModel):
    verified_device = models.ForeignKey('devices.Device', ...)
```

### In audit_log/models.py

```python
# OLD:
class SessionAuditLog(BaseAuditLog):
    session = models.ForeignKey('accounts.Session', ...)
    device = models.ForeignKey('accounts.Device', ...)

# NEW:
class SessionAuditLog(BaseAuditLog):
    session = models.ForeignKey('sessions.Session', ...)
    device = models.ForeignKey('devices.Device', ...)

# Applied to all audit log models:
# - SessionAuditLog
# - DeviceAuditLog
# - SessionDeviceLinkAuditLog
# - MFAAuditLog
```

---

## Django Settings Update

### config/settings.py

```python
# OLD:
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'mfa_auth'
]

# NEW:
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'accounts',     # âœ¨ NEW
    'devices',      # âœ¨ NEW
    'sessions',     # âœ¨ NEW
    'otp',
    'notifications',
    'audit_log',
    'mfa_auth'
]
```

---

## Relationship Diagram (After Refactoring)

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                   ACCOUNTS APP                      â”‚
â”‚ (User, Profile, MFASettings, PasswordHistory)       â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”˜
                 â”‚ OneToOne                        â”‚ OneToOne
        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”            â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”
        â”‚   DEVICES APP    â”‚            â”‚  SESSIONS APP     â”‚
        â”‚ (Device,         â”‚            â”‚ (Session)         â”‚
        â”‚  TrustedDevice)  â”‚            â”‚                   â”‚
        â”‚                 â”‚            â”‚ - user FK â†’ User  â”‚
        â”‚ - user FK       â”‚            â”‚ - device FK       â”‚
        â”‚   â†’ User        â”‚            â”‚   â†’ Device        â”‚
        â”‚                 â”‚            â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
        â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                 â”‚
        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
        â”‚                   â”‚
    â”Œâ”€â”€â”€â–¼â”€â”€â”€â”€â”         â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”
    â”‚OTP APP â”‚         â”‚AUDIT_LOGâ”‚
    â”‚(MFA)   â”‚         â”‚APP      â”‚
    â””â”€â”€â”€â”€â”€â”€â”€â”€â”˜         â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”˜
                             â”‚
                    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                    â”‚ Audit Models:    â”‚
                    â”‚ - Session Audit  â”‚
                    â”‚ - Device Audit   â”‚
                    â”‚ - MFA Audit      â”‚
                    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## Benefits of This Architecture

### 1. **Separation of Concerns**
- Device management isolated from account management
- Session management is independent and specialized
- Each app has a single responsibility

### 2. **Better Scalability**
- Can scale devices independently
- Session service can be separated/replicated
- Independent database tuning per service

### 3. **Easier Testing**
- Test device logic without account logic
- Mock sessions independently
- Cleaner test fixtures

### 4. **Microservices Ready**
- Can extract devices service to separate Django instance
- Can extract sessions service separately
- Independent caching strategies per service

### 5. **Cleaner Imports**
```python
# Instead of:
from accounts.models import User, Device, Session

# Now:
from accounts.models import User
from devices.models import Device
from sessions.models import Session
```

### 6. **Future Features**
- Rate limiting per service
- Independent versioning
- Specialized middleware per service
- Service-specific caching

---

## Migration Strategy

### Step 1: Create Migrations
```bash
python manage.py makemigrations accounts
python manage.py makemigrations devices
python manage.py makemigrations sessions
python manage.py makemigrations otp
python manage.py makemigrations audit_log
```

### Step 2: Verify Migration Order
- accounts (removes Device, Session, TrustedDevice)
- devices (creates Device, TrustedDevice)
- sessions (creates Session)
- otp (updates ForeignKey references)
- audit_log (updates ForeignKey references)

### Step 3: Apply Migrations
```bash
python manage.py migrate accounts
python manage.py migrate devices
python manage.py migrate sessions
python manage.py migrate otp
python manage.py migrate audit_log
```

### Step 4: Verify Data
```bash
python manage.py shell
>>> from devices.models import Device
>>> from sessions.models import Session
>>> Device.objects.count()
>>> Session.objects.count()
```

---

## Import Updates Needed

### In Your Views/Serializers

```python
# OLD:
from accounts.models import User, Device, Session

# NEW:
from accounts.models import User
from devices.models import Device
from sessions.models import Session
```

### In Your Tests

```python
# OLD:
from accounts.models import Device, Session

# NEW:
from devices.models import Device
from sessions.models import Session
```

### In Your Admin

```python
# OLD:
from accounts.models import Device, Session

# NEW (if you want to register these in admin):
from devices.models import Device
from sessions.models import Session
```

---

## Database Tables (No Changes)

Table names remain the same:
- `devices` (Device model)
- `trusted_devices` (TrustedDevice model)
- `sessions` (Session model)

No data migration needed - just code organization.

---

## Deployment Considerations

### Zero-Downtime Deployment

1. **Deploy code changes first** (new app structure)
2. **Run migrations** in order
3. **Update imports** in views/serializers
4. **Restart application**

No database downtime required - tables already exist with correct names.

---

## Backwards Compatibility

### Old Imports Still Available (via lazy loading)

```python
# This still works (temporarily):
from accounts.models import Device  # String reference works

# But better to update to:
from devices.models import Device
```

---

## Summary Checklist

âœ… Device model moved to devices/models.py
âœ… TrustedDevice model moved to devices/models.py
âœ… Session model moved to sessions/models.py
âœ… All ForeignKey references updated to string references
âœ… accounts/models.py cleaned up
âœ… config/settings.py updated with new INSTALLED_APPS
âœ… otp/models.py updated with string references
âœ… audit_log/models.py updated with string references

---

