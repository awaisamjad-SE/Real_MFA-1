# AUDIT_LOG APP - Complete Documentation

## ðŸ“‹ Table of Contents
1. [Overview](#overview)
2. [Models](#models)
3. [Audit Event Types](#audit-event-types)
4. [Risk Assessment](#risk-assessment)
5. [Anomaly Detection](#anomaly-detection)
6. [Database Design](#database-design)
7. [Best Practices](#best-practices)
8. [Query Examples](#query-examples)
9. [Future Enhancements](#future-enhancements)

---

## Overview

The **AUDIT_LOG** app provides comprehensive security audit trails:

**Key Features:**
- Session activity tracking (create, authenticate, revoke)
- Device tracking (add, verify, trust, compromise)
- MFA event tracking (enable, disable, verify, recovery)
- Risk scoring (0-100 scale)
- Anomaly detection (unusual locations, patterns)
- Approval workflows
- Daily aggregation for analytics
- Compliance (SOC2, HIPAA, PCI-DSS)
- Forensics investigation support
- Automatic cleanup of old logs

**Scale:**
- 1M users Ã— 100 sessions = 100M session events/month
- 1M users Ã— 10 devices = 10M device events/month
- Total: 300M+ audit records/year
- Storage: 50-100GB/year with compression

---

## Models

### 1. **BaseAuditLog Model (Abstract)**
**Not a table - parent for all audit models**

Base class for all audit logs with common fields.

**Key Fields:**
```
id (UUID)
user (ForeignKey)              # Which user?
action (String)                # What happened? (create, update, delete, verify)
action_type (String)           # Category (session, device, mfa, auth)

# Change Tracking
old_value (JSONField)          # Old value before change
new_value (JSONField)          # New value after change
changed_by (String)            # Who changed it? (user/system/admin)

# Request Context
ip_address (IP)                # Where from?
user_agent (Text)              # Browser/device info
location (String)              # Geolocation (country, city)
latitude (Float)               # Exact location
longitude (Float)              # Exact location

# Metadata
metadata (JSONField)           # Extra context
error_message (Text)           # If failed, why?

# Risk Assessment
risk_level (Choice)            # Low, Medium, High, Critical

# Timestamps
created_at (DateTime)          # When happened?
```

**Risk Levels:**
```
Low       - Normal activity
Medium    - Unusual but acceptable
High      - Suspicious, needs review
Critical  - Security incident
```

---

### 2. **SessionAuditLog Model**
**Database Table:** `session_audit_logs`

Track all session-related events.

**Key Fields:**
```
id (UUID)
user (ForeignKey)              # Which user?
session (ForeignKey)           # Which session?
device (ForeignKey)            # Which device?

# Action
action (Choice)                # Session action

# Details
session_type (String)          # web, mobile, api, desktop
mfa_verified (Boolean)         # Was MFA verified?
mfa_method (String)            # Which MFA method?

# Location
country (String)               # Country
city (String)                  # City
ip_address (IP)                # IP address
latitude (Float)               # Location
longitude (Float)              # Location

# Risk Assessment
risk_level (Choice)            # Low, Medium, High, Critical
is_anomalous (Boolean)         # Unusual activity?
anomaly_reasons (List)         # Why anomalous?

# Session Duration
session_duration_seconds (Int) # How long was session?
total_requests (Int)           # Total API requests

# Approval
requires_review (Boolean)      # Needs admin review?
review_status (Choice)         # Pending, Approved, Rejected
reviewed_by (ForeignKey)       # Who reviewed?
review_notes (Text)            # Review comments

# Timestamps
created_at (DateTime)          # When happened?
```

**Session Actions (19 types):**
```
'session_created'           - New session started
'session_authenticated'     - User authenticated
'session_mfa_verified'      - MFA verified
'session_refreshed'         - Token refreshed
'session_revoked'           - Session ended
'session_expired'           - Session timed out
'session_suspicious'        - Marked suspicious
'refresh_token_rotated'     - New refresh token
'refresh_token_reused'      - Old token reused (attack)
'jwt_validated'             - JWT token validated
'jwt_expired'               - JWT expired
'jwt_blacklisted'           - Token blacklisted
'device_verified_in_session' - Device verified
'mfa_challenge_created'     - MFA challenge started
'mfa_challenge_verified'    - MFA challenge passed
'rate_limit_exceeded'       - Too many requests
'ip_changed'                - Different IP detected
'location_changed'          - Different location
'browser_changed'           - Different browser
```

**Methods:**
```python
audit = SessionAuditLog.objects.get(id=audit_id)

# Check if requires review
if audit.requires_review:
    print("This needs admin review")

# Mark as reviewed
audit.mark_reviewed(
    status='approved',
    reviewed_by=admin_user,
    notes='Legitimate activity'
)

# Check risk level
if audit.risk_level == 'critical':
    alert_security_team()
```

**Indexes:**
- user + created_at (find user's recent events)
- session + created_at (track session activity)
- risk_level + created_at (find high-risk events)

---

### 3. **DeviceAuditLog Model**
**Database Table:** `device_audit_logs`

Track all device-related events.

**Key Fields:**
```
id (UUID)
user (ForeignKey)              # Which user?
device (ForeignKey)            # Which device?
session (ForeignKey)           # Which session?

# Action
action (Choice)                # Device action

# Device Details
device_fingerprint (String)    # Device identifier
device_type (String)           # Phone, laptop, etc
browser (String)               # Chrome, Safari, etc
os (String)                    # Windows, iOS, etc

# Risk Assessment
risk_score (Int 0-100)         # 0=safe, 100=extremely risky
previous_risk_score (Int)      # Before this event
is_anomalous (Boolean)         # Unusual activity?
anomaly_reasons (List)         # Why anomalous?

# Location
country (String)               # Country
city (String)                  # City
latitude (Float)               # Exact location
longitude (Float)              # Exact location

# Device Status Change
trust_state_change (String)    # None â†’ Trusted, Verified â†’ Trusted
verified_at (DateTime)         # Device verification time
trusted_at (DateTime)          # Device trust time
compromised_at (DateTime)      # When marked compromised?

# Verification
verification_method (String)   # Email, SMS, prompt, biometric

# Time Tracking
link_duration_seconds (Int)    # How long linked to user?

# IP Tracking
ip_address (IP)                # Device IP
previous_ip (IP)               # Last known IP

# Timestamps
created_at (DateTime)          # When happened?
```

**Device Actions (20+ types):**
```
'device_registered'            - New device added
'device_verified'              - Device verified
'device_trusted'               - Device trusted
'device_revoked'               - Device revoked
'device_compromised'           - Marked compromised
'device_flagged'               - Suspicious flag
'fingerprint_changed'          - Fingerprint changed
'browser_changed'              - Browser changed
'os_changed'                   - OS updated
'location_changed'             - New location
'ip_changed'                   - New IP address
'login_successful'             - Successful login
'login_failed'                 - Failed login
'mfa_required'                 - MFA required
'mfa_verified'                 - MFA passed
'risk_score_updated'           - Risk increased
'can_skip_mfa'                 - MFA skip enabled
'mfa_skip_disabled'            - MFA skip disabled
'trust_expired'                - Trust period ended
'device_retired'               - Device no longer used
```

**Methods:**
```python
audit = DeviceAuditLog.objects.get(id=audit_id)

# Check if anomalous
if audit.is_anomalous:
    print(f"Anomalies: {audit.anomaly_reasons}")
    # Output: ['Location change > 1000km', 'New device type']

# Get risk history
risk_history = DeviceAuditLog.objects.filter(
    device=audit.device
).order_by('created_at').values('risk_score', 'created_at')

# Plot risk trend over time
```

**Risk Score Calculation:**
```python
risk_score = 0

# Base factors
risk_score += 10 if new_location else 0          # +10 new country
risk_score += 5 if ip_changed else 0             # +5 new IP
risk_score += 20 if fingerprint_changed else 0   # +20 clear fingerprint change

# Account history
risk_score += 15 if recent_account_lockout else 0  # +15 recent lockout
risk_score += 10 if recent_failed_mfa else 0       # +10 failed MFA

# Device age
days_since_verify = (now - verified_at).days
risk_score += days_since_verify // 30             # +1 per 30 days unverified

# Capped at 100
risk_score = min(risk_score, 100)

# Risk level
if risk_score < 20: risk_level = 'Low'
elif risk_score < 50: risk_level = 'Medium'
elif risk_score < 75: risk_level = 'High'
else: risk_level = 'Critical'
```

---

### 4. **SessionDeviceLinkAuditLog Model**
**Database Table:** `session_device_link_audit_logs`

Track session-device relationship changes.

**Key Fields:**
```
id (UUID)
user (ForeignKey)              # Which user?
session (ForeignKey)           # Which session?
device (ForeignKey)            # Which device?

# Link Status
link_action (Choice)           # Created, verified, trusted, revoked
previous_device (ForeignKey)   # Previous device (if changed)

# Verification
verified_at (DateTime)         # When verified?
trusted_at (DateTime)          # When trusted?
revoked_at (DateTime)          # When revoked?

# Link Duration
link_duration_seconds (Int)    # Session-device connection time

# Context
context (JSONField)            # Extra context about link

# Timestamps
created_at (DateTime)          # When happened?
```

**Use Cases:**
```
1. User A logs in from Device 1
   - SessionDeviceLinkAuditLog: Device 1 linked

2. System verifies Device 1
   - SessionDeviceLinkAuditLog: verified_at = now

3. System marks Device 1 as trusted
   - SessionDeviceLinkAuditLog: trusted_at = now

4. Session ends
   - SessionDeviceLinkAuditLog: revoked_at = now, duration = 2 hours
```

---

### 5. **MFAAuditLog Model**
**Database Table:** `mfa_audit_logs`

Track MFA-related events.

**Key Fields:**
```
id (UUID)
user (ForeignKey)              # Which user?
device (ForeignKey)            # Which device?

# Action
action (Choice)                # MFA action

# MFA Method
mfa_method (Choice)            # TOTP, Email, SMS, Backup
primary_method (Boolean)       # Is this the primary?

# Challenge Tracking
challenge_id (UUID)            # Which MFA challenge?
verification_attempts (Int)    # How many tries?
max_attempts (Int)             # Max allowed tries?

# Code Details
code_length (Int)              # 6-8 digits
code_hash (String)             # Hashed code (never plaintext)

# Recovery
recovery_method (String)       # backup_code, email, sms, support

# Risk Assessment
risk_level (Choice)            # Low, Medium, High, Critical
is_anomalous (Boolean)         # Unusual MFA activity?
anomaly_reasons (List)         # Why anomalous?

# Rate Limiting
request_count_last_hour (Int)  # OTP requests in past hour
rate_limit_status (String)     # OK, Warning, Blocked

# Timestamps
created_at (DateTime)          # When happened?
```

**MFA Actions (18+ types):**
```
'mfa_enabled'                  - MFA turned on
'mfa_disabled'                 - MFA turned off
'primary_method_changed'       - Changed default method
'method_added'                 - New MFA method added
'method_removed'               - MFA method removed
'totp_setup'                   - TOTP configured
'totp_verified'                - TOTP verified
'backup_codes_generated'       - New backup codes
'backup_code_used'             - Backup code used
'email_otp_sent'               - Email OTP sent
'email_otp_verified'           - Email OTP verified
'sms_otp_sent'                 - SMS OTP sent
'sms_otp_verified'             - SMS OTP verified
'challenge_created'            - MFA challenge created
'challenge_verified'           - Challenge verified
'challenge_failed'             - Challenge failed
'challenge_expired'            - Challenge expired
'recovery_attempt'             - Account recovery attempt
```

**Methods:**
```python
audit = MFAAuditLog.objects.get(id=audit_id)

# Check if rate limited
if audit.rate_limit_status == 'blocked':
    # User has requested too many OTPs
    # Lock account for 30 minutes
    lock_account(audit.user)

# Get MFA event history
mfa_history = MFAAuditLog.objects.filter(
    user=audit.user,
    created_at__gte=timezone.now() - timedelta(days=30)
)

# Check for unusual activity
suspicious = mfa_history.filter(
    is_anomalous=True,
    risk_level__in=['high', 'critical']
).count()

if suspicious > 5:
    alert_user("Unusual MFA activity detected")
```

---

### 6. **AuditLogSummary Model**
**Database Table:** `audit_log_summaries`

Daily aggregation for performance.

**Key Fields:**
```
id (UUID)
user (ForeignKey)              # Which user?
date (Date)                    # Which day?

# Activity Counts
total_sessions (Int)           # New sessions created
total_devices (Int)            # New devices added
total_failed_logins (Int)      # Failed login attempts
total_mfa_challenges (Int)     # MFA challenges issued
total_api_calls (Int)          # API requests made

# Risk Statistics
low_risk_events (Int)          # Count
medium_risk_events (Int)       # Count
high_risk_events (Int)         # Count
critical_risk_events (Int)     # Count

# Geographic Stats
countries_accessed (Int)       # How many countries?
unique_ips (Int)               # How many IPs?
unique_devices (Int)           # How many devices?

# MFA Stats
mfa_enabled_count (Int)        # Times enabled
mfa_disabled_count (Int)       # Times disabled
backup_codes_generated (Int)   # How many?
rate_limit_exceeded (Int)      # How many times?

# Event Tracking
anomalies_detected (Int)       # Unusual activities
approvals_required (Int)       # Events needing review
approvals_completed (Int)      # Reviews done

# Timestamps
created_at (DateTime)          # Summary creation time
```

**Usage:**
```python
# Get today's summary
today = timezone.now().date()
summary = AuditLogSummary.objects.get(
    user=user,
    date=today
)

# Quick risk assessment
total_high_risk = summary.high_risk_events + summary.critical_risk_events

if total_high_risk > 3:
    alert_user("Multiple suspicious activities detected today")

# Get weekly summary
week_start = timezone.now().date() - timedelta(days=7)
week_data = AuditLogSummary.objects.filter(
    user=user,
    date__gte=week_start
).aggregate(
    total_high_risk=Sum('high_risk_events') + Sum('critical_risk_events'),
    total_api_calls=Sum('total_api_calls')
)
```

---

## Audit Event Types

### Session Audit Event Examples:

```python
# Event 1: Login successful
SessionAuditLog.objects.create(
    user=user,
    session=session,
    action='session_authenticated',
    risk_level='low',
    ip_address='192.168.1.1',
    country='USA',
    city='New York'
)

# Event 2: Suspicious location
SessionAuditLog.objects.create(
    user=user,
    session=session,
    action='session_suspicious',
    risk_level='high',
    anomaly_reasons=[
        'Location > 1000km from last login',
        'Time impossible (2 countries, 30 min)',
        'New device'
    ],
    requires_review=True
)

# Event 3: Token rotation
SessionAuditLog.objects.create(
    user=user,
    session=session,
    action='refresh_token_rotated',
    old_value={'refresh_token': 'old_...'},
    new_value={'refresh_token': 'new_...'},
    risk_level='low'
)
```

### Device Audit Event Examples:

```python
# Event 1: New device registered
DeviceAuditLog.objects.create(
    user=user,
    device=device,
    action='device_registered',
    device_type='iPhone',
    os='iOS 17',
    browser='Safari',
    risk_score=0,
    country='Canada'
)

# Event 2: Device compromised
DeviceAuditLog.objects.create(
    user=user,
    device=device,
    action='device_compromised',
    risk_score=95,
    anomaly_reasons=[
        'Jailbroken device detected',
        'Malware signatures found'
    ],
    requires_review=True
)

# Event 3: Location change
DeviceAuditLog.objects.create(
    user=user,
    device=device,
    action='location_changed',
    previous_location='USA',
    new_location='UK',
    latitude=51.5074,
    longitude=-0.1278,
    risk_score=45
)
```

---

## Risk Assessment

### Risk Scoring Algorithm:

```python
def calculate_risk_score(user, device, session, action):
    """
    Calculate risk score (0-100) based on multiple factors
    """
    risk = 0

    # Location-based risks
    previous_location = get_last_location(user, device)
    if is_impossible_travel(previous_location, current_location):
        risk += 40  # Physically impossible
    elif is_different_country(previous_location, current_location):
        risk += 20  # Different country
    elif is_different_city(previous_location, current_location):
        risk += 10  # Different city

    # Device risks
    if device.is_compromised:
        risk += 35  # Already marked compromised
    if device.is_new(created_less_than=7):
        risk += 15  # Very new device
    if device.not_verified(for_days=30):
        risk += 10  # Unverified for 30 days

    # Account history
    failed_logins = get_failed_logins_last_hour(user)
    if failed_logins > 5:
        risk += 25  # Many failed attempts

    if user.account_locked:
        risk += 30  # Account is locked

    # Time-based risks
    if is_unusual_time_for_user(user, current_time):
        risk += 10  # User normally sleeps now

    # Return capped at 100
    return min(risk, 100)
```

### Risk Level Thresholds:

```
Score 0-25:    LOW (âœ… Normal activity)
Score 26-50:   MEDIUM (âš ï¸ Unusual but acceptable)
Score 51-75:   HIGH (â›” Suspicious, needs review)
Score 76-100:  CRITICAL (ðŸš¨ Security incident)
```

### Action Based on Risk Level:

```python
if risk_level == 'low':
    # Allow immediately
    pass

elif risk_level == 'medium':
    # Allow but notify user
    send_notification(user, "Login from new location")

elif risk_level == 'high':
    # Require MFA or additional verification
    require_mfa_challenge(user)
    alert_security_team(user)

elif risk_level == 'critical':
    # Block and require manual review
    block_session(session)
    require_admin_approval(user, session)
    disable_account_until_verified(user)
```

---

## Anomaly Detection

### Impossible Travel Detection:

```python
def is_impossible_travel(location_1, location_2, time_diff_minutes):
    """
    Detect if travel between locations is physically possible
    """
    distance_km = haversine_distance(
        location_1['latitude'],
        location_1['longitude'],
        location_2['latitude'],
        location_2['longitude']
    )

    # Max flight speed: 900 km/h
    max_travel_km = (time_diff_minutes / 60) * 900

    return distance_km > max_travel_km  # True = Impossible
```

### Example:
```
Location 1: New York (40.7128Â°N, 74.0060Â°W)
Location 2: Tokyo (35.6762Â°N, 139.6503Â°E)
Distance: ~10,850 km
Time gap: 30 minutes

Max possible distance in 30 min: (30/60) * 900 = 450 km
10,850 km > 450 km â†’ IMPOSSIBLE TRAVEL âœ—
```

### Velocity-Based Detection:

```python
def get_velocity_anomalies(user):
    """
    Find sessions with impossible velocity
    """
    sessions = Session.objects.filter(user=user).order_by('created_at')
    anomalies = []

    for i in range(len(sessions) - 1):
        s1 = sessions[i]
        s2 = sessions[i + 1]

        distance = haversine_distance(s1.latitude, s1.longitude,
                                      s2.latitude, s2.longitude)
        time_gap = (s2.created_at - s1.created_at).total_seconds() / 3600  # hours

        velocity = distance / time_gap  # km/hour

        # Commercial flight max: 900 km/h
        if velocity > 900:
            anomalies.append({
                'session_1': s1.id,
                'session_2': s2.id,
                'velocity': velocity,
                'reason': 'Faster than possible travel'
            })

    return anomalies
```

---

## Database Design

### Table Structure:

```
audit_log_sessions
â”œâ”€â”€ id (UUID, PK)
â”œâ”€â”€ user_id (UUID, FK â†’ users)
â”œâ”€â”€ session_id (UUID, FK â†’ sessions)
â”œâ”€â”€ device_id (UUID, FK â†’ devices)
â”œâ”€â”€ action (VARCHAR)
â”œâ”€â”€ risk_level (VARCHAR)
â”œâ”€â”€ is_anomalous (BOOLEAN)
â”œâ”€â”€ requires_review (BOOLEAN)
â”œâ”€â”€ created_at (TIMESTAMP)
â””â”€â”€ Indexes:
    â”œâ”€â”€ user_id + created_at
    â”œâ”€â”€ session_id
    â”œâ”€â”€ risk_level + created_at
    â””â”€â”€ requires_review + created_at

audit_log_devices
â”œâ”€â”€ id (UUID, PK)
â”œâ”€â”€ user_id (UUID, FK â†’ users)
â”œâ”€â”€ device_id (UUID, FK â†’ devices)
â”œâ”€â”€ action (VARCHAR)
â”œâ”€â”€ risk_score (INT)
â”œâ”€â”€ is_anomalous (BOOLEAN)
â”œâ”€â”€ created_at (TIMESTAMP)
â””â”€â”€ Indexes:
    â”œâ”€â”€ user_id + created_at
    â”œâ”€â”€ device_id
    â”œâ”€â”€ risk_score DESC
    â””â”€â”€ is_anomalous + created_at

audit_log_mfa
â”œâ”€â”€ id (UUID, PK)
â”œâ”€â”€ user_id (UUID, FK â†’ users)
â”œâ”€â”€ device_id (UUID, FK â†’ devices)
â”œâ”€â”€ action (VARCHAR)
â”œâ”€â”€ mfa_method (VARCHAR)
â”œâ”€â”€ challenge_id (UUID)
â”œâ”€â”€ verification_attempts (INT)
â”œâ”€â”€ created_at (TIMESTAMP)
â””â”€â”€ Indexes:
    â”œâ”€â”€ user_id + created_at
    â”œâ”€â”€ challenge_id
    â”œâ”€â”€ mfa_method + created_at
    â””â”€â”€ verification_attempts

audit_log_summaries
â”œâ”€â”€ id (UUID, PK)
â”œâ”€â”€ user_id (UUID, FK â†’ users)
â”œâ”€â”€ date (DATE)
â”œâ”€â”€ total_sessions (INT)
â”œâ”€â”€ total_devices (INT)
â”œâ”€â”€ high_risk_events (INT)
â”œâ”€â”€ critical_risk_events (INT)
â””â”€â”€ Indexes:
    â”œâ”€â”€ user_id + date (UNIQUE)
    â”œâ”€â”€ date
    â””â”€â”€ high_risk_events DESC
```

### Storage Estimates:

```
1M users Ã— 100 sessions/user/month = 100M session events
1M users Ã— 10 devices/user/month = 10M device events
1M users Ã— 20 MFA events/user/month = 20M MFA events
Total: ~130M events/month = 1.56B/year

Per event: ~500 bytes (including JSON fields)
Storage: 1.56B Ã— 500 bytes = 780 GB/year

With compression (40%): 312 GB/year
With archival after 1 year: 312 GB active + archive
```

### Cleanup Strategy:

```python
# Keep 1 year active
# Archive older than 1 year to S3
# Delete after 7 years (compliance requirement)

def cleanup_audit_logs():
    """
    Run daily to maintain database size
    """
    cutoff_date = timezone.now() - timedelta(days=365)

    # Archive to S3
    old_logs = SessionAuditLog.objects.filter(
        created_at__lt=cutoff_date
    )

    for log in old_logs:
        export_to_s3(log)

    # Delete after 7 years
    delete_date = timezone.now() - timedelta(days=365*7)
    SessionAuditLog.objects.filter(
        created_at__lt=delete_date
    ).delete()
```

---

## Best Practices

### 1. **Always Log Security Events**
```python
# âœ… GOOD: Log every sensitive action
SessionAuditLog.objects.create(
    user=user,
    session=session,
    action='session_authenticated',
    ip_address=request.META['REMOTE_ADDR'],
    user_agent=request.META['HTTP_USER_AGENT']
)

# Log MFA verification
MFAAuditLog.objects.create(
    user=user,
    action='mfa_verified',
    mfa_method='totp'
)
```

### 2. **Calculate Risk Scores**
```python
# âœ… GOOD: Assess risk for every event
risk_score = calculate_risk_score(
    user=user,
    device=device,
    location=current_location,
    action='login'
)

if risk_score > 75:
    require_additional_verification(user)
```

### 3. **Detect Anomalies**
```python
# âœ… GOOD: Find unusual patterns
anomalies = detect_anomalies(
    user=user,
    current_event=login_event
)

if anomalies:
    DeviceAuditLog.objects.create(
        user=user,
        device=device,
        is_anomalous=True,
        anomaly_reasons=anomalies
    )
```

### 4. **Clean Up Old Logs**
```python
# âœ… GOOD: Archive and delete after retention
# Run daily via Celery task
cleanup_audit_logs()
```

### 5. **Query Efficiently**
```python
# âœ… GOOD: Use indexes
from django.db.models import Q

# Find high-risk events for user in past 30 days
high_risk = SessionAuditLog.objects.filter(
    user=user,
    created_at__gte=timezone.now() - timedelta(days=30),
    risk_level__in=['high', 'critical']
)

# Find anomalies across all devices
anomalies = DeviceAuditLog.objects.filter(
    user=user,
    is_anomalous=True
).select_related('device')
```

---

## Query Examples

### 1. **Find Impossible Travel**
```python
def find_impossible_travel(user):
    """
    Find sessions with impossible travel
    """
    sessions = Session.objects.filter(
        user=user
    ).order_by('created_at')

    impossible = []
    for i in range(len(sessions) - 1):
        s1, s2 = sessions[i], sessions[i+1]

        if is_impossible_travel(
            (s1.latitude, s1.longitude),
            (s2.latitude, s2.longitude),
            (s2.created_at - s1.created_at).total_seconds()
        ):
            impossible.append({
                'session_1': s1.id,
                'session_2': s2.id,
                'time_gap': s2.created_at - s1.created_at
            })

    return impossible
```

### 2. **Find Account Compromise Indicators**
```python
def find_compromise_indicators(user):
    """
    Find signs of account compromise
    """
    indicators = {
        'failed_logins': 0,
        'new_devices': 0,
        'unusual_locations': 0,
        'mfa_disabled': False,
        'risk_score': 0
    }

    # Recent failed logins
    indicators['failed_logins'] = SessionAuditLog.objects.filter(
        user=user,
        action='login_failed',
        created_at__gte=timezone.now() - timedelta(hours=24)
    ).count()

    # New devices in past 24 hours
    indicators['new_devices'] = DeviceAuditLog.objects.filter(
        user=user,
        action='device_registered',
        created_at__gte=timezone.now() - timedelta(hours=24)
    ).count()

    # High risk events
    indicators['risk_score'] = DeviceAuditLog.objects.filter(
        user=user,
        created_at__gte=timezone.now() - timedelta(hours=24)
    ).aggregate(Max('risk_score'))['risk_score__max'] or 0

    # Check if MFA was disabled
    mfa_disabled = MFAAuditLog.objects.filter(
        user=user,
        action='mfa_disabled',
        created_at__gte=timezone.now() - timedelta(hours=24)
    ).exists()
    indicators['mfa_disabled'] = mfa_disabled

    return indicators
```

### 3. **Generate Daily Summary**
```python
def generate_daily_summary(user, date):
    """
    Create daily audit log summary
    """
    summary = AuditLogSummary.objects.create(
        user=user,
        date=date
    )

    # Count events
    summary.total_sessions = SessionAuditLog.objects.filter(
        user=user,
        action='session_created',
        created_at__date=date
    ).count()

    summary.high_risk_events = (
        SessionAuditLog.objects.filter(
            user=user,
            risk_level='high',
            created_at__date=date
        ).count() +
        DeviceAuditLog.objects.filter(
            user=user,
            risk_level='high',
            created_at__date=date
        ).count()
    )

    summary.save()
    return summary
```

---

## Future Enhancements

### 1. **ML-Based Anomaly Detection**
```python
from sklearn.ensemble import IsolationForest

def ml_detect_anomalies(user):
    """
    Use ML to find unusual patterns
    """
    # Collect features
    features = [
        session.latitude,
        session.longitude,
        session.hour,  # time of day
        session.day,   # day of week
        session.duration,
        session.api_calls
    ]

    # Train isolation forest
    model = IsolationForest()
    outliers = model.fit_predict(features)

    # Mark anomalous sessions
    for i, is_anomalous in enumerate(outliers):
        if is_anomalous == -1:
            SessionAuditLog.objects.create(
                user=user,
                is_anomalous=True,
                anomaly_reasons=['ML model detected outlier']
            )
```

### 2. **Real-Time Alerting**
```python
class AlertManager:
    def trigger_alert(self, user, risk_level, reason):
        """
        Send real-time alert to user
        """
        if risk_level in ['high', 'critical']:
            # Send push notification
            send_push_notification(user, f"Suspicious activity: {reason}")

            # Send email
            send_email(user, f"Login alert: {reason}")

            # Alert admin
            alert_security_team(user)
```

### 3. **Threat Intelligence Integration**
```python
def check_threat_intelligence(ip_address):
    """
    Check IP against threat databases
    """
    # Query AbuseIPDB, Shodan, etc
    is_suspicious = query_threat_db(ip_address)

    if is_suspicious:
        return {
            'ip_reputation': 'bad',
            'abuse_reports': 150,
            'risk_score': 85
        }
```

### 4. **Automated Response**
```python
class AutomatedResponse:
    def handle_critical_event(self, audit_log):
        """
        Automatically respond to critical events
        """
        if audit_log.risk_level == 'critical':
            # Revoke all sessions
            Session.objects.filter(user=audit_log.user).update(
                status='revoked'
            )

            # Require MFA
            require_mfa(audit_log.user)

            # Force password change
            require_password_change(audit_log.user)

            # Email user
            send_security_alert(audit_log.user)
```

### 5. **Compliance Reporting**
```python
def generate_compliance_report(user, days=90):
    """
    Generate SOC2/HIPAA/PCI-DSS compliance report
    """
    report = {
        'total_logins': SessionAuditLog.objects.filter(
            user=user,
            action='session_authenticated',
            created_at__gte=timezone.now() - timedelta(days=days)
        ).count(),

        'mfa_verification_rate': calculate_mfa_rate(user, days),
        'critical_events': SessionAuditLog.objects.filter(
            user=user,
            risk_level='critical',
            created_at__gte=timezone.now() - timedelta(days=days)
        ).count(),

        'avg_response_time': calculate_avg_incident_response(user, days),

        'failed_audit_requirements': find_failed_requirements(user, days)
    }

    return report
```

---

## Summary

The **AUDIT_LOG** app provides:

âœ… **Comprehensive Tracking**
- Session events (19+ types)
- Device events (20+ types)
- MFA events (18+ types)
- Relationship changes

âœ… **Risk Assessment**
- Risk scoring (0-100)
- Risk level categorization
- Automatic risk calculation

âœ… **Anomaly Detection**
- Impossible travel detection
- Velocity-based anomalies
- Pattern recognition

âœ… **Compliance**
- SOC2, HIPAA, PCI-DSS support
- 7-year retention
- Detailed audit trails

âœ… **Performance**
- Daily aggregation
- Index optimization
- Archival strategy
- 300M+ events/year support

âœ… **Security**
- Risk-based blocking
- Automated response
- Alert integration
- Forensics support

---

