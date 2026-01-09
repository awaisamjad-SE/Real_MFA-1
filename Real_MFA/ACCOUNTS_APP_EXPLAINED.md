# 📚 Accounts App - Complete File-by-File Explanation

This document explains **every file** in the `accounts` app in a simple, beginner-friendly way with real code examples from your project.

---

## 📋 Table of Contents

1. [backends.py - The Security Guard](#1-backendspy---the-security-guard-)
2. [models.py - The Database Blueprint](#2-modelspy---the-database-blueprint-)
3. [admin.py - The Control Panel](#3-adminpy---the-control-panel-)
4. [serializers.py - The Translator](#4-serializerspy---the-translator-)
5. [views.py - The Request Handler](#5-viewspy---the-request-handler-)
6. [urls.py - The Address Book](#6-urlspy---the-address-book-)
7. [signals.py - The Automatic Helper](#7-signalspy---the-automatic-helper-)
8. [validators.py - The Rule Checker](#8-validatorspy---the-rule-checker-)
9. [redis_utils.py - The Memory Box](#9-redis_utilspy---the-memory-box-)
10. [apps.py - The App ID Card](#10-appspy---the-app-id-card-)
11. [How They All Work Together](#11-how-they-all-work-together-)

---

## 1. backends.py - The Security Guard 🛡️

### What is it?

Think of `backends.py` as a **security guard at a building entrance**. When someone wants to enter (login), the guard checks their ID (username/password) and decides if they can come in.

### Why do we need it?

By default, Django only knows how to check **username + password**. But in our app, users login with **email + password**. So we create a custom "security guard" that understands email-based login.

### Real Example - How a Kid Would Understand

```
👦 User: "Hi, I'm john@gmail.com and my password is secret123"

🛡️ Backend (Security Guard):
   1. "Let me check if john@gmail.com exists..." ✅ Found!
   2. "Is the password 'secret123' correct?" ✅ Yes!
   3. "Is this account active (not banned)?" ✅ Yes!
   4. "Welcome in, John!"
```

### Your Code Explained

```python
# filepath: accounts/backends.py

class EmailBackend(ModelBackend):
    """
    This is our custom security guard.
    It checks email instead of username.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        This method is called every time someone tries to login.
        
        Parameters:
        - username: Actually the email (we named it username for compatibility)
        - password: The password they typed
        """
        try:
            # Step 1: Try to find user by email
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            try:
                # Step 2: If email not found, try username
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                # Step 3: User not found at all
                return None  # "Sorry, you can't enter"
        
        # Step 4: Check if password is correct
        if user.check_password(password) and self.user_can_authenticate(user):
            return user  # "Welcome! Here's your user object"
        
        return None  # "Wrong password, can't enter"
    
    def get_user(self, user_id):
        """
        This is called on EVERY request after login.
        Django says: "This session belongs to user #123, get me their info"
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
```

### Where is it configured?

In `settings.py`:

```python
AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailBackend',  # Our custom guard (first priority)
    'django.contrib.auth.backends.ModelBackend',  # Default guard (backup)
]
```

### When is it called?

| Scenario | What Happens |
|----------|--------------|
| User clicks "Login" | `authenticate()` is called |
| User loads any page after login | `get_user()` is called |
| Admin panel login | `authenticate()` is called |
| API login endpoint | `authenticate()` is called |

---

## 2. models.py - The Database Blueprint 📐

### What is it?

`models.py` is like a **blueprint for a house**. It defines what information we store about users and how it's organized in the database.

### Why do we need it?

Without models, we'd have no way to save user data. Models tell Django:
- What columns to create in the database
- What type of data each column holds
- How different tables relate to each other

### Real Example - How a Kid Would Understand

```
Imagine a filing cabinet with drawers:

📁 USERS Drawer:
   ┌─────────────────────────────────────────────────┐
   │ id: abc-123                                     │
   │ email: john@gmail.com                           │
   │ username: john_doe                              │
   │ password: ******* (encrypted)                   │
   │ role: user                                      │
   │ email_verified: No                              │
   │ mfa_enabled: No                                 │
   │ created_at: 2026-01-07                          │
   └─────────────────────────────────────────────────┘

📁 PROFILES Drawer (connected to Users):
   ┌─────────────────────────────────────────────────┐
   │ user_id: abc-123 (connects to John)             │
   │ phone_number: +923001234567                     │
   │ profile_picture: /images/john.jpg               │
   └─────────────────────────────────────────────────┘
```

### Your Code Explained

```python
# filepath: accounts/models.py

class User(AbstractUser, SoftDeleteModel):
    """
    Our custom User model - stores all user information
    
    AbstractUser: Gives us username, password, is_active, etc. for free
    SoftDeleteModel: Allows "deleting" without actually removing data
    """
    
    # ROLE CHOICES - Like job titles
    ROLE_CHOICES = [
        ('admin', 'Admin'),      # Can do everything
        ('manager', 'Manager'),  # Can manage some things
        ('user', 'User'),        # Normal user
    ]
    
    # PRIMARY FIELDS
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    # ↑ Unique ID like "abc-123-def-456" instead of just "1, 2, 3"
    
    email = models.EmailField(unique=True, db_index=True)
    # ↑ unique=True means no two users can have same email
    # ↑ db_index=True makes searching by email faster
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    # ↑ Can only be 'admin', 'manager', or 'user'
    
    # SECURITY FIELDS
    email_verified = models.BooleanField(default=False)
    # ↑ True/False - Has user clicked verification link?
    
    mfa_enabled = models.BooleanField(default=False)
    # ↑ True/False - Is 2-factor auth enabled?
    
    failed_login_attempts = models.PositiveIntegerField(default=0)
    # ↑ Counts failed logins. After 5, lock the account!
    
    account_locked_until = models.DateTimeField(null=True, blank=True)
    # ↑ If locked, when can they try again?
    
    # This tells Django to use email for login, not username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']


class Profile(TimeStampedModel):
    """
    Extra user info in a separate table.
    Why separate? Because not all users need all these fields.
    """
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    # ↑ OneToOne = Each user has exactly ONE profile
    # ↑ on_delete=CASCADE = Delete profile when user is deleted
    # ↑ related_name='profile' = Access via user.profile
    
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)


class PasswordHistory(TimeStampedModel):
    """
    Keeps track of old passwords.
    Why? So users can't reuse their last 5 passwords!
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_history')
    # ↑ ForeignKey = One user can have MANY password histories
    
    password_hash = models.CharField(max_length=255)
    # ↑ Stores the encrypted password (never plain text!)
    
    changed_from_ip = models.GenericIPAddressField(null=True)
    # ↑ From which IP address was password changed?
```

### How to use models?

```python
# Create a new user
user = User.objects.create_user(
    email='john@gmail.com',
    username='john_doe',
    password='secret123'
)

# Find a user
user = User.objects.get(email='john@gmail.com')

# Update a user
user.email_verified = True
user.save()

# Access profile
phone = user.profile.phone_number

# Check password history
old_passwords = user.password_history.all()
```

---

## 3. admin.py - The Control Panel 🎛️

### What is it?

`admin.py` configures the **Django Admin Panel** - a ready-made control panel where admins can manage users without writing code.

### Why do we need it?

Without `admin.py`, the admin panel wouldn't know:
- How to display our custom User model
- Which fields to show in the list
- Which fields can be edited
- How to organize the edit form

### Real Example - How a Kid Would Understand

```
Imagine a TV remote control. admin.py decides:

📺 What buttons to show:
   [Email] [Username] [Role] [Verified?] [MFA?] [Active?]

🔍 What filters to have:
   - Filter by Role: [All] [Admin] [Manager] [User]
   - Filter by Verified: [All] [Yes] [No]

📝 When editing, what sections to show:
   - Basic Info (email, username)
   - Security (MFA settings)
   - Permissions (is_staff, is_superuser)
```

### Your Code Explained

```python
# filepath: accounts/admin.py

class ProfileInline(admin.StackedInline):
    """
    This shows Profile fields INSIDE the User edit page.
    Instead of going to a separate page for Profile,
    you see it right there with User.
    
    StackedInline = Fields stacked vertically
    TabularInline = Fields in a table row (more compact)
    """
    model = Profile
    can_delete = False  # Don't allow deleting profile
    fk_name = 'user'    # Which field connects to User
    extra = 0           # Don't show empty forms for new profiles


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """
    Customize how Users appear in admin panel.
    We extend DjangoUserAdmin because it already has password handling built-in.
    """
    
    # Include Profile editing inside User page
    inlines = [ProfileInline]
    
    # Columns shown in the list view
    list_display = (
        'email',           # john@gmail.com
        'username',        # john_doe
        'role',            # user/admin/manager
        'email_verified',  # ✓ or ✗
        'mfa_enabled',     # ✓ or ✗
        'is_active',       # ✓ or ✗
        'created_at',      # 2026-01-07
    )
    
    # Sidebar filters
    list_filter = (
        'role',            # Filter: Show only admins
        'email_verified',  # Filter: Show only verified
        'mfa_enabled',     # Filter: Show only MFA users
        'is_active',       # Filter: Show only active
    )
    
    # Search box searches these fields
    search_fields = ('email', 'username', 'first_name', 'last_name')
    
    # Default sorting
    ordering = ('email',)
    
    # Fields that can't be edited (just displayed)
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_login')
    
    # How the edit form is organized
    fieldsets = (
        # Section 1: Basic Info
        (None, {'fields': ('id', 'email', 'username', 'password')}),
        
        # Section 2: Role & Status
        ('Role & Status', {'fields': ('role', 'is_active', 'is_deleted')}),
        
        # Section 3: Verification & MFA
        ('Verification & MFA', {'fields': ('email_verified', 'mfa_enabled', 'mfa_method')}),
        
        # Section 4: Security
        ('Security', {'fields': (
            'failed_login_attempts',
            'account_locked_until',
            'password_changed_at',
        )}),
        
        # Section 5: Permissions
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups')}),
    )
    
    # Form for ADDING new user (different from editing)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),  # Make it wide
            'fields': ('email', 'username', 'role', 'password1', 'password2'),
        }),
    )


@admin.register(PasswordHistory)
class PasswordHistoryAdmin(admin.ModelAdmin):
    """
    Password history is READ-ONLY.
    Admins can see it but can't add or modify.
    """
    
    list_display = ('user', 'created_at', 'changed_from_ip')
    readonly_fields = ('user', 'password_hash', 'changed_from_ip', 'created_at')
    
    def has_add_permission(self, request):
        return False  # Can't add new password history manually
```

### Visual Result

```
ADMIN PANEL
═══════════════════════════════════════════════════════════════

Users List:
┌──────────────────┬───────────┬────────┬──────────┬─────────┐
│ Email            │ Username  │ Role   │ Verified │ Active  │
├──────────────────┼───────────┼────────┼──────────┼─────────┤
│ john@gmail.com   │ john_doe  │ User   │    ✓     │   ✓     │
│ admin@site.com   │ admin     │ Admin  │    ✓     │   ✓     │
│ test@gmail.com   │ tester    │ User   │    ✗     │   ✓     │
└──────────────────┴───────────┴────────┴──────────┴─────────┘

Filters:          Search: [_______________] [🔍]
☐ Admin
☐ Manager  
☑ User
```

---

## 4. serializers.py - The Translator 🔄

### What is it?

`serializers.py` is like a **translator between two languages**:
- **Language 1**: JSON (what the API sends/receives)
- **Language 2**: Python objects (what Django understands)

### Why do we need it?

When a user sends registration data as JSON:
```json
{"email": "john@gmail.com", "password": "secret123"}
```

Django doesn't understand JSON directly. Serializers:
1. **Validate** the data (is email format correct?)
2. **Convert** JSON → Python objects
3. **Create** database records
4. **Convert** Python objects → JSON for the response

### Real Example - How a Kid Would Understand

```
📥 INCOMING (from user's browser):
   JSON: {"email": "john@gmail.com", "password": "secret123"}

🔄 SERIALIZER (translator):
   1. "Is email valid?" ✓
   2. "Is password at least 8 characters?" ✓
   3. "Does this email already exist?" ✗ (it's new)
   4. Create User object in database
   
📤 OUTGOING (back to browser):
   JSON: {"id": "abc-123", "message": "Registration successful!"}
```

### Your Code Explained

```python
# filepath: accounts/serializers.py

class DeviceDataSerializer(serializers.Serializer):
    """
    Validates device information sent during registration.
    This is a NESTED serializer (used inside RegisterSerializer).
    """
    
    fingerprint_hash = serializers.CharField(
        max_length=255, 
        min_length=10,  # At least 10 characters
        validators=[validate_fingerprint]  # Custom validation
    )
    device_type = serializers.ChoiceField(
        choices=['mobile', 'tablet', 'desktop', 'unknown'],
        default='unknown'
    )
    browser = serializers.CharField(max_length=100, required=False)
    os = serializers.CharField(max_length=100, required=False)


class RegisterSerializer(serializers.Serializer):
    """
    Handles user registration.
    
    INPUT (from user):
    {
        "username": "john_doe",
        "email": "john@gmail.com",
        "password": "secret123",
        "password2": "secret123",
        "device": {
            "fingerprint_hash": "abc123...",
            "device_type": "mobile"
        }
    }
    """
    
    # Define expected fields and their rules
    username = serializers.CharField(
        max_length=150,
        validators=[validate_unique_username]  # Must be unique
    )
    
    email = serializers.EmailField(
        validators=[validate_unique_email]  # Must be unique
    )
    
    password = serializers.CharField(
        write_only=True,  # Never include in response!
        min_length=8
    )
    
    password2 = serializers.CharField(write_only=True, min_length=8)
    
    device = DeviceDataSerializer()  # Nested serializer
    
    def validate(self, attrs):
        """
        Cross-field validation.
        Called after individual field validation.
        """
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Passwords do not match."
            })
        return attrs
    
    def create(self, validated_data):
        """
        Create the user after validation passes.
        Called when you do serializer.save()
        """
        # Extract nested device data
        device_data = validated_data.pop('device')
        password = validated_data.pop('password')
        validated_data.pop('password2')
        
        # Create user
        user = User(email_verified=False, **validated_data)
        user._skip_verification_email = True  # Signal won't send duplicate
        user.set_password(password)  # Hash the password!
        user.save()
        
        # Create device record
        Device.objects.create(user=user, **device_data)
        
        # Send verification email
        send_verification_email.delay(str(user.id))
        
        return user
```

### Validation Flow

```
📥 Input: {"email": "bad-email", "password": "123"}

Step 1: Field Validation
   ├── email: "bad-email" → ❌ Invalid email format
   ├── password: "123" → ❌ Too short (min 8)
   └── STOP! Return errors.

📥 Input: {"email": "john@gmail.com", "password": "secret123", ...}

Step 1: Field Validation
   ├── email: "john@gmail.com" → ✓ Valid format
   ├── email validator: → ❌ Already exists!
   └── STOP! Return error.

📥 Input: {"email": "new@gmail.com", "password": "secret123", "password2": "different"}

Step 1: Field Validation → All ✓
Step 2: validate() method
   └── password != password2 → ❌ Don't match!
   └── STOP! Return error.

📥 Input: (all correct data)

Step 1: Field Validation → All ✓
Step 2: validate() → ✓
Step 3: create() → Create user in database
📤 Output: {"id": "abc-123", "email": "new@gmail.com", "message": "Success!"}
```

---

## 5. views.py - The Request Handler 📬

### What is it?

`views.py` contains functions that **receive web requests and return responses**. It's like a **receptionist** who takes your request and gives you what you need.

### Why do we need it?

When someone visits `/api/auth/register/`, Django needs to know:
- What code to run
- What data to expect
- What response to send back

Views connect URLs to actual functionality.

### Real Example - How a Kid Would Understand

```
📨 Customer: "I want to register!"
   URL: POST /api/auth/register/
   Data: {"email": "john@gmail.com", ...}

👩‍💼 Receptionist (View):
   1. "Let me check if you're sending too many requests..." ✓ OK
   2. "Let me validate your data..." ✓ OK
   3. "Let me create your account..." ✓ Done!
   4. "Here's your response!" → 201 Created

📨 Customer: "I want to verify my email!"
   URL: POST /api/auth/verify-email/
   Data: {"uid": "abc...", "token": "xyz..."}

👩‍💼 Receptionist (View):
   1. "Let me check that token..." ✓ Valid!
   2. "Marking your email as verified..." ✓ Done!
   3. "Here's your response!" → 200 OK
```

### Your Code Explained

```python
# filepath: accounts/views.py

@api_view(['POST'])  # Only accept POST requests
@permission_classes([AllowAny])  # Anyone can access (no login required)
def register(request):
    """
    Handle user registration.
    
    URL: POST /api/auth/register/
    """
    
    # Step 1: Check rate limit (max 3 per minute)
    throttle = RegistrationRateThrottle()
    if not throttle.allow_request(request, None):
        return Response(
            {"error": "Too many attempts. Try again later."},
            status=status.HTTP_429_TOO_MANY_REQUESTS  # 429
        )
    
    # Step 2: Validate data using serializer
    serializer = RegisterSerializer(data=request.data)
    
    if serializer.is_valid():
        # Step 3: Create user (serializer.save() calls create())
        user = serializer.save()
        
        # Step 4: Return success response
        return Response(
            {
                "id": str(user.id),
                "email": user.email,
                "message": "Registration successful. Check your email."
            },
            status=status.HTTP_201_CREATED  # 201
        )
    
    # Validation failed - return errors
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """
    Verify user's email with token from link.
    
    URL: POST /api/auth/verify-email/
    Input: {"uid": "base64_user_id", "token": "verification_token"}
    """
    
    serializer = EmailVerificationSerializer(data=request.data)
    
    if serializer.is_valid():
        serializer.save()  # Marks email as verified
        return Response(
            {"message": "Email verified successfully!"},
            status=status.HTTP_200_OK
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

### Rate Limiting Explained

```python
class RegistrationRateThrottle(BaseThrottle):
    """
    Prevents spam registrations.
    Max 3 registrations per minute per IP address.
    """
    
    RATE_LIMIT = 3   # Max 3 attempts
    WINDOW = 60      # Per 60 seconds
    
    def allow_request(self, request, view):
        ip = self.get_ip(request)  # Get user's IP
        
        # Check cache: How many times has this IP registered?
        key = f'reg_throttle:ip:{ip}'
        count = cache.get(key, 0)
        
        if count >= self.RATE_LIMIT:
            return False  # "Sorry, too many attempts!"
        
        # Increment counter
        cache.set(key, count + 1, self.WINDOW)
        return True  # "OK, you can proceed"
```

### HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Email verified successfully |
| 201 | Created | User registered successfully |
| 400 | Bad Request | Invalid data (validation failed) |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Something went wrong on our side |

---

## 6. urls.py - The Address Book 📖

### What is it?

`urls.py` is like an **address book** that maps URLs to views. When someone visits a URL, Django looks it up here to find which view to call.

### Why do we need it?

Without URL routing, Django wouldn't know that:
- `/api/auth/register/` → should call `register()` view
- `/api/auth/verify-email/` → should call `verify_email()` view

### Your Code Explained

```python
# filepath: accounts/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Registration
    path('auth/register/', views.register, name='register'),
    #     ↑ URL path       ↑ View function  ↑ Name for reverse lookup
    
    # Email verification
    path('auth/verify-email/', views.verify_email, name='verify-email'),
    
    # Resend verification
    path('auth/resend-verification-email/', views.resend_verification_email, name='resend-verification-email'),
    
    # Demo APIs
    path('demo/pakistani-names/', views.demo_pakistani_names, name='demo-pakistani-names'),
    path('demo/heavy-data/', views.demo_heavy_data, name='demo-heavy-data'),
]
```

### How it connects to the main project

```python
# filepath: Real_MFA/urls.py (main project)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('accounts.urls')),  # All accounts URLs start with /api/
    #          ↑ Include all URLs from accounts app
]
```

### URL Resolution Flow

```
User visits: http://localhost:8000/api/auth/register/

Step 1: Django checks Real_MFA/urls.py
   └── 'api/' matches → go to accounts.urls

Step 2: Django checks accounts/urls.py
   └── 'auth/register/' matches → call views.register()

Step 3: views.register() runs and returns response
```

---

## 7. signals.py - The Automatic Helper 🤖

### What is it?

Signals are like **automatic triggers**. When something happens (user created), Django automatically runs some code (create profile, send email).

### Why do we need it?

Instead of remembering to create a Profile every time we create a User, signals do it automatically. It's like having a helpful robot:

```
🤖 "I noticed you created a new user. Let me automatically:
    1. Create their profile
    2. Send them a verification email"
```

### Your Code Explained

```python
# filepath: accounts/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
#         ↑ Listen to this signal
#                    ↑ Only when User model is saved
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create Profile when User is created.
    
    Parameters:
    - sender: The model class (User)
    - instance: The actual user object that was saved
    - created: True if new user, False if just updated
    """
    if created:  # Only for NEW users
        Profile.objects.create(user=instance)
        # Now user.profile automatically exists!


@receiver(post_save, sender=User)
def send_verification_email_on_create(sender, instance, created, **kwargs):
    """
    Automatically send verification email when User is created.
    
    This helps when admin creates user from admin panel.
    """
    # Only for new users
    if not created:
        return
    
    # Skip if already verified
    if instance.email_verified:
        return
    
    # Skip if API already handles it
    if getattr(instance, '_skip_verification_email', False):
        return
    
    # Generate token and send email
    token = default_token_generator.make_token(instance)
    VerificationTokenManager.store_token(instance.id, token)
    send_verification_email.delay(str(instance.id))
```

### Signal Flow Diagram

```
User.objects.create_user(email='john@gmail.com', ...)
                    │
                    ▼
            Django saves to database
                    │
                    ▼
        ┌─── post_save signal fires ───┐
        │                              │
        ▼                              ▼
create_user_profile()    send_verification_email_on_create()
        │                              │
        ▼                              ▼
Profile.objects.create()      send_verification_email.delay()
```

### Where are signals connected?

In `apps.py`:

```python
class AccountsConfig(AppConfig):
    name = 'accounts'
    
    def ready(self):
        import accounts.signals  # Connect signals when app loads
```

---

## 8. validators.py - The Rule Checker ✅

### What is it?

Validators are **functions that check if data follows the rules**. They're like a teacher checking homework.

### Why do we need it?

Before saving data, we want to make sure:
- Email isn't already taken
- Username isn't already taken
- Phone number has correct format
- Device fingerprint is valid

### Your Code Explained

```python
# filepath: accounts/validators.py

from django.core.exceptions import ValidationError

def validate_unique_username(value):
    """
    Check if username already exists.
    
    Usage: validators=[validate_unique_username]
    """
    from .models import User
    
    if User.objects.filter(username=value).exists():
        raise ValidationError("Username already taken.")
    
    return value  # Return value if valid


def validate_unique_email(value):
    """Check if email already exists."""
    from .models import User
    
    if User.objects.filter(email=value).exists():
        raise ValidationError("Email already registered.")
    
    return value


def validate_phone_format(value):
    """
    Validate phone number format.
    Must be 9-15 digits, optionally starting with +
    
    Valid: +923001234567, 03001234567
    Invalid: abc, 123, +1
    """
    import re
    
    if value and not re.match(r'^\+?1?\d{9,15}$', value):
        raise ValidationError("Phone must be 9-15 digits.")
    
    return value


def validate_fingerprint(value):
    """
    Device fingerprint must be at least 10 characters.
    This helps prevent fake fingerprints.
    """
    if not value or len(value) < 10:
        raise ValidationError("Invalid device fingerprint hash.")
    
    return value
```

### How validators are used

```python
# In serializers.py
class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(
        validators=[validate_unique_username]  # ← Used here!
    )
    email = serializers.EmailField(
        validators=[validate_unique_email]  # ← Used here!
    )
```

### Validation Flow

```
Input: {"username": "john_doe", "email": "john@gmail.com"}

Step 1: validate_unique_username("john_doe")
   └── Does "john_doe" exist in database?
       ├── YES → raise ValidationError("Username already taken")
       └── NO  → return "john_doe" ✓

Step 2: validate_unique_email("john@gmail.com")
   └── Does "john@gmail.com" exist in database?
       ├── YES → raise ValidationError("Email already registered")
       └── NO  → return "john@gmail.com" ✓
```

---

## 9. redis_utils.py - The Memory Box 🗃️

### What is it?

`redis_utils.py` contains utilities for storing temporary data in **Redis** (a super-fast in-memory database). It's like a temporary locker.

### Why do we need it?

Some data is temporary and doesn't need to be in the main database:
- Verification tokens (expire in 24 hours)
- Rate limit counters (expire in 1 minute)
- Cooldown timers (expire in 60 seconds)

Redis is perfect because it automatically deletes expired data.

### Real Example - How a Kid Would Understand

```
🗃️ REDIS LOCKER ROOM

Locker "verification_token:abc-123":
   Content: "xyz789token"
   Expires: In 24 hours
   (Automatically cleaned out after expiry)

Locker "resend_limit:abc-123":
   Content: "2" (user has resent 2 times)
   Expires: In 1 hour
   (After 1 hour, counter resets to 0)

Locker "resend_cooldown:abc-123":
   Content: "1" (cooldown active)
   Expires: In 60 seconds
   (User must wait before resending)
```

### Your Code Explained

```python
# filepath: accounts/redis_utils.py

class VerificationTokenManager:
    """
    Manages email verification tokens.
    Tokens are stored in Redis, not in the database.
    """
    
    @staticmethod
    def store_token(user_id, token, expires_in=86400):
        """
        Store a verification token.
        
        expires_in: 86400 seconds = 24 hours
        """
        key = f"verification_token:{user_id}"
        redis_client.setex(key, expires_in, token)
        #                  ↑ key
        #                       ↑ seconds until expiry
        #                                   ↑ value to store
    
    @staticmethod
    def verify_token(user_id, token):
        """
        Check if token matches what we stored.
        """
        key = f"verification_token:{user_id}"
        stored_token = redis_client.get(key)
        return stored_token == token
    
    @staticmethod
    def invalidate_token(user_id):
        """
        Delete token after successful verification.
        (So it can't be used again)
        """
        key = f"verification_token:{user_id}"
        redis_client.delete(key)


class ResendLimiter:
    """
    Limits how many times a user can resend verification email.
    Max 4 times per hour.
    """
    
    @staticmethod
    def can_resend(user_id):
        """Check if user can resend."""
        key = f"resend_limit:{user_id}"
        current_count = redis_client.get(key)
        
        if current_count is None:
            return True, "Can resend"  # First time
        
        if int(current_count) >= 4:
            ttl = redis_client.ttl(key)  # Time until reset
            return False, f"Max reached. Try in {ttl} seconds."
        
        return True, "Can resend"
    
    @staticmethod
    def record_resend(user_id):
        """Record a resend attempt."""
        key = f"resend_limit:{user_id}"
        count = redis_client.incr(key)  # Add 1 to counter
        
        if count == 1:
            redis_client.expire(key, 3600)  # Expire in 1 hour


class CooldownManager:
    """
    60-second cooldown between resends.
    Prevents spamming the resend button.
    """
    
    @staticmethod
    def can_resend_now(user_id):
        key = f"resend_cooldown:{user_id}"
        
        if redis_client.exists(key):
            ttl = redis_client.ttl(key)
            return False, f"Wait {ttl} seconds"
        
        return True, "Can resend"
    
    @staticmethod
    def set_cooldown(user_id):
        key = f"resend_cooldown:{user_id}"
        redis_client.setex(key, 60, "1")  # 60 second cooldown
```

### Redis vs Database

| Feature | Redis | Database |
|---------|-------|----------|
| Speed | Super fast (memory) | Slower (disk) |
| Persistence | Data can be lost | Data is permanent |
| Expiry | Auto-delete after time | Manual deletion needed |
| Best for | Temporary data, caching | Permanent data |

---

## 10. apps.py - The App ID Card 🪪

### What is it?

`apps.py` is the **identity card** of your Django app. It tells Django basic information about the app.

### Why do we need it?

Django needs to know:
- What's the app's name?
- What type of auto-field to use for IDs?
- What code to run when the app starts?

### Your Code Explained

```python
# filepath: accounts/apps.py

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """
    Configuration for the accounts app.
    """
    
    default_auto_field = 'django.db.models.BigAutoField'
    # ↑ Use BigAutoField for auto-generated IDs
    # (Though we use UUID, this is for any auto fields)
    
    name = 'accounts'
    # ↑ The name of the app (must match the folder name)
    
    def ready(self):
        """
        Called when Django starts up and this app is loaded.
        Perfect place to connect signals!
        """
        import accounts.signals  # This connects all our signals
```

### Where is it registered?

In `settings.py`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    ...
    'accounts.apps.AccountsConfig',  # ← Our app
    'devices',
    'notification',
]
```

---

## 11. How They All Work Together 🔗

### The Complete Registration Flow

```
👤 User submits registration form
         │
         ▼
    ┌─────────────────────────────────────────────────────────┐
    │  urls.py                                                │
    │  'api/auth/register/' → views.register                  │
    └─────────────────────────────────────────────────────────┘
         │
         ▼
    ┌─────────────────────────────────────────────────────────┐
    │  views.py - register()                                  │
    │  1. Check rate limit (redis_utils)                      │
    │  2. Validate data (serializers.py)                      │
    │  3. Create user (models.py)                             │
    └─────────────────────────────────────────────────────────┘
         │
         ▼
    ┌─────────────────────────────────────────────────────────┐
    │  serializers.py - RegisterSerializer                    │
    │  1. Validate fields (validators.py)                     │
    │  2. Create User and Device (models.py)                  │
    │  3. Send verification email (celery_tasks.py)           │
    └─────────────────────────────────────────────────────────┘
         │
         ▼
    ┌─────────────────────────────────────────────────────────┐
    │  signals.py                                             │
    │  post_save signal fires:                                │
    │  1. create_user_profile() → Profile created             │
    │  2. send_verification_email_on_create() → (skipped,     │
    │     because serializer already sent it)                 │
    └─────────────────────────────────────────────────────────┘
         │
         ▼
    ┌─────────────────────────────────────────────────────────┐
    │  redis_utils.py                                         │
    │  Store verification token with 24h expiry               │
    └─────────────────────────────────────────────────────────┘
         │
         ▼
    📧 Email sent with verification link
         │
         ▼
    👤 User clicks link, frontend extracts uid + token
         │
         ▼
    ┌─────────────────────────────────────────────────────────┐
    │  views.py - verify_email()                              │
    │  1. Validate uid + token                                │
    │  2. Mark email_verified = True                          │
    │  3. Return success                                      │
    └─────────────────────────────────────────────────────────┘
         │
         ▼
    ✅ User is now verified and can login!
```

### File Dependency Chart

```
                    settings.py
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    backends.py      apps.py        urls.py
         │               │               │
         │               ▼               ▼
         │          signals.py      views.py
         │               │               │
         └───────┬───────┴───────────────┘
                 │
                 ▼
             models.py
                 │
         ┌───────┴───────┐
         │               │
         ▼               ▼
   validators.py    serializers.py
                         │
                         ▼
                   redis_utils.py
```

---

## Summary Table

| File | Purpose | Like... |
|------|---------|---------|
| `backends.py` | Handle login authentication | Security guard |
| `models.py` | Define database structure | House blueprint |
| `admin.py` | Configure admin panel | Control panel |
| `serializers.py` | Validate & transform data | Translator |
| `views.py` | Handle API requests | Receptionist |
| `urls.py` | Map URLs to views | Address book |
| `signals.py` | Auto-run code on events | Automatic helper robot |
| `validators.py` | Check data rules | Homework checker |
| `redis_utils.py` | Temporary data storage | Locker room |
| `apps.py` | App configuration | ID card |

---

## Quick Reference

### How to find what you need:

| I want to... | Go to... |
|--------------|----------|
| Change login behavior | `backends.py` |
| Add a new field to User | `models.py` |
| Change admin panel display | `admin.py` |
| Add new API endpoint | `views.py` + `urls.py` |
| Validate input data | `validators.py` or `serializers.py` |
| Auto-run code on save | `signals.py` |
| Store temporary data | `redis_utils.py` |

---

*Created for Real MFA Project - 2026*
