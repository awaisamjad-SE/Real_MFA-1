# Accounts App - Complete File Breakdown

## ðŸ“‹ Overview
The accounts app is the **core authentication and user management system** with MFA (Multi-Factor Authentication) support, role-based access control, profile management, and security features.

---

## ðŸŽ¯ Top Topics by Category

### **1. Core Authentication**
- `models.py` - User model with roles, security fields, and profile
- `backends.py` - Email-based authentication backend
- `auth_views.py` - Login/logout endpoints
- `auth_serializers.py` - Login/logout data validation

### **2. User Registration & Verification**
- `registration_views.py` - User signup with rate limiting
- `verification_views.py` - Email verification endpoints
- `verification_serializers.py` - Verification data validation

### **3. Password Management**
- `password_views.py` - Password reset, change endpoints
- `password_serializers.py` - Password validation logic
- `password_urls.py` - Password-related URL routing

### **4. User Profile**
- `profile_views.py` - Profile CRUD operations
- `profile_serializers.py` - Profile data validation
- `profile_urls.py` - Profile URL routing

### **5. Admin Features**
- `admin_views.py` - Admin user management endpoints
- `admin_serializers.py` - Admin-specific serializers
- `admin_urls.py` - Admin URL routing
- `admin.py` - Django admin panel configuration

### **6. Utilities & Infrastructure**
- `redis_utils.py` - Rate limiting and token caching
- `validators.py` - Reusable validation functions
- `signals.py` - Auto-create profiles, send emails
- `urls.py` - Main URL configuration for accounts

---

## ðŸ“„ File-by-File Explanation

### **1. models.py** ðŸ—ï¸
**What:** Defines the database schema for users and profiles
**Why:** Custom User model needed for email login, roles (admin/manager/user), MFA fields, and soft delete
**How:**
- `User` model extends AbstractUser with UUID primary key, email as username, role-based access
- Security fields: `email_verified`, `mfa_enabled`, `failed_login_attempts`, `account_locked_until`
- `Profile` model for bio, phone, profile picture, address
- `TimeStampedModel` & `SoftDeleteModel` abstract classes for reusability
- `UserManager` for custom user creation logic

**Interview Answer:** "Custom User model with email authentication, role-based access (admin/manager/user), MFA support, and account lockout mechanism. Profile separated for clean architecture."

---

### **2. backends.py** ðŸ”
**What:** Custom authentication backend for Django
**Why:** Django defaults to username login; we need email-based login with verification check
**How:**
- `EmailBackend` overrides `authenticate()` method
- Checks email first, falls back to username
- Blocks login if `email_verified=False`
- Used in `AUTHENTICATION_BACKENDS` setting

**Interview Answer:** "Custom authentication backend that allows login with email instead of username. It enforces email verification before allowing authentication."

---

### **3. auth_views.py** ðŸšª
**What:** Login and logout API endpoints
**Why:** Handle user authentication flow with device tracking and MFA
**How:**
- `POST /api/auth/login/` - Validates credentials, checks device trust, initiates MFA if needed
- `POST /api/auth/logout/` - Invalidates tokens, logs event
- Rate limiting: 5 login attempts per minute
- Returns tokens + user data on success

**Interview Answer:** "Login endpoint authenticates users, tracks device fingerprints, triggers MFA if device is untrusted, and returns JWT tokens. Logout invalidates the refresh token."

---

### **4. auth_serializers.py** âœ…
**What:** Data validation for login/logout requests
**Why:** Validate input, implement business logic, sanitize data
**How:**
- `LoginSerializer` - Validates identifier (email/username), password, device info
- `MFAVerifyLoginSerializer` - Validates OTP code during login
- `LogoutSerializer` - Validates refresh token for logout
- Uses Django REST Framework serializers

**Interview Answer:** "Serializers validate login data, enforce password rules, check device fingerprints, and handle MFA OTP validation during authentication."

---

### **5. registration_views.py** ðŸ“
**What:** User registration endpoint
**Why:** Allow new users to sign up with rate limiting
**How:**
- `POST /api/auth/register/` - Creates user, sends verification email
- Rate limit: 2 registrations per minute per IP
- Device info captured during registration
- Sets `email_verified=False` by default
- Uses Celery to send async verification email

**Interview Answer:** "Registration endpoint creates users with email verification workflow. Rate-limited to prevent abuse. Captures device fingerprint during signup."

---

### **6. verification_views.py** âœ‰ï¸
**What:** Email verification and resend endpoints
**Why:** Ensure email ownership before allowing login
**How:**
- `POST /api/auth/verify-email/` - Validates token, marks email verified
- `POST /api/auth/resend-verification/` - Resends verification email (rate limited)
- Uses Redis for token storage (6-hour expiry)
- Invalidates token after verification

**Interview Answer:** "Email verification endpoint validates tokens from verification emails. Tokens stored in Redis with 6-hour expiry. Resend endpoint is rate-limited to prevent spam."

---

### **7. verification_serializers.py** ðŸ”
**What:** Validation for verification endpoints
**Why:** Validate email and token format
**How:**
- `EmailVerificationSerializer` - Validates token, checks expiry
- `ResendVerificationSerializer` - Validates email format
- Checks if user exists and isn't already verified

**Interview Answer:** "Validates verification tokens, checks expiry, and ensures users aren't re-verifying already verified emails."

---

### **8. password_views.py** ðŸ”‘
**What:** Password reset and change endpoints
**Why:** Allow users to recover/change passwords securely
**How:**
- `POST /api/password/forgot/` - Sends reset email
- `POST /api/password/reset/` - Validates token, resets password
- `POST /api/password/change/` - Changes password for authenticated user
- Uses Django's default token generator
- Rate limited to prevent abuse

**Interview Answer:** "Password reset uses email-based token system. Change password requires old password verification. All actions logged in audit logs."

---

### **9. password_serializers.py** ðŸ›¡ï¸
**What:** Password validation logic
**Why:** Enforce password strength, match confirmation
**How:**
- `ForgotPasswordSerializer` - Validates email
- `ResetPasswordSerializer` - Validates token, new password, password2 match
- `ChangePasswordSerializer` - Validates old password, new password rules
- Uses regex for password strength

**Interview Answer:** "Enforces password complexity (uppercase, lowercase, digits, special chars, min 8 length). Validates password confirmation matching."

---

### **10. password_urls.py** ðŸ”—
**What:** URL routing for password endpoints
**Why:** Organize password-related routes
**How:**
- Maps `/forgot/`, `/reset/`, `/change/` to respective views
- Included in main accounts URLs with prefix

**Interview Answer:** "URL configuration for password management endpoints - forgot, reset, and change."

---

### **11. profile_views.py** ðŸ‘¤
**What:** User profile CRUD operations
**Why:** Manage user profile information
**How:**
- `GET /api/profile/me/` - Get current user's profile
- `PUT/PATCH /api/profile/me/` - Update profile
- `PUT /api/profile/me/picture/` - Update profile picture
- Only authenticated users can access
- Auto-creates profile if missing

**Interview Answer:** "Profile management endpoints for viewing and updating user info like bio, phone, picture. Separate from User model for clean separation of concerns."

---

### **12. profile_serializers.py** ðŸ“‹
**What:** Profile data validation
**Why:** Validate profile updates, handle nested user data
**How:**
- `ProfileSerializer` - Validates bio, phone, address, picture
- Nested `UserSerializer` for displaying user info
- File upload validation for profile pictures

**Interview Answer:** "Validates profile data including phone format, image uploads, and nested user information display."

---

### **13. profile_urls.py** ðŸ”—
**What:** Profile endpoint routing
**Why:** Organize profile routes
**How:**
- Maps `/me/`, `/me/picture/` to profile views
- Requires authentication

**Interview Answer:** "URL configuration for profile endpoints - view and update profile."

---

### **14. admin_views.py** ðŸ‘¨â€ðŸ’¼
**What:** Admin-only user management endpoints
**Why:** Allow admins to manage users, roles, and account status
**How:**
- List/create/update/delete users
- Change user roles
- Lock/unlock accounts
- View user statistics
- Role-based permission checks

**Interview Answer:** "Admin endpoints for managing users - CRUD operations, role assignments, account locking. Only accessible to admin role users."

---

### **15. admin_serializers.py** ðŸ“Š
**What:** Admin-specific serializers
**Why:** Different validation rules for admin operations
**How:**
- `AdminUserSerializer` - Full user data with security fields
- `UserRoleUpdateSerializer` - Role change validation
- `AccountStatusSerializer` - Lock/unlock validation

**Interview Answer:** "Admin serializers expose additional fields like security settings, failed login attempts, and allow role modifications."

---

### **16. admin_urls.py** ðŸ”—
**What:** Admin endpoint routing
**Why:** Organize admin routes separately
**How:**
- Maps admin user management endpoints
- Includes role and status update routes

**Interview Answer:** "URL configuration for admin-only user management features."

---

### **17. admin.py** ðŸŽ›ï¸
**What:** Django admin panel configuration
**Why:** Provide web UI for staff to manage data
**How:**
- Registers User and Profile models
- Customizes list display, filters, search
- Makes fields editable in admin panel

**Interview Answer:** "Django admin configuration for managing users and profiles through web interface. Customized for better usability."

---

### **18. redis_utils.py** âš¡
**What:** Redis caching and rate limiting utilities
**Why:** Store temporary tokens, implement rate limiting
**How:**
- `VerificationTokenManager` - Stores email verification tokens in Redis
- `EmailResendRateLimiter` - Prevents email spam (1 per minute)
- `PasswordResetTokenManager` - Stores password reset tokens
- Uses Django cache as fallback if Redis unavailable

**Interview Answer:** "Redis utilities for token storage and rate limiting. Verification tokens expire in 6 hours. Email resend limited to once per minute per user."

---

### **19. validators.py** âœ”ï¸
**What:** Reusable validation functions
**Why:** Centralize validation logic, avoid code duplication
**How:**
- `validate_unique_username` - Check username availability
- `validate_unique_email` - Check email availability
- `validate_phone_format` - Phone number format check
- `validate_fingerprint` - Device fingerprint validation
- `get_client_ip` - Extract IP from request

**Interview Answer:** "Centralized validation functions for uniqueness checks, format validation, and request metadata extraction. Reusable across serializers."

---

### **20. signals.py** ðŸ“¡
**What:** Django signals for automatic actions
**Why:** Auto-create related objects, send notifications
**How:**
- `post_save(User)` - Auto-creates Profile when User created
- `post_save(User)` - Sends verification email on registration
- `password_changed` - Custom signal for password change events
- `mfa_status_changed` - Custom signal for MFA toggle events

**Interview Answer:** "Django signals automatically create user profiles on registration and send verification emails. Custom signals trigger notifications for security events."

---

### **21. urls.py** ðŸ—ºï¸
**What:** Main URL configuration for accounts app
**Why:** Central routing for all accounts endpoints
**How:**
- Includes auth URLs (login/logout)
- Includes registration and verification
- Includes password URLs
- Includes profile URLs
- Includes admin URLs

**Interview Answer:** "Main URL router for accounts app, organizing authentication, registration, password, profile, and admin routes."

---

### **22. serializers.py** ðŸ“¦
**What:** Common/shared serializers
**Why:** Reusable serializers used across multiple views
**How:**
- `UserSerializer` - Basic user data serialization
- `RegisterSerializer` - Registration data validation
- Device-related serializers
- Base serializers extended by others

**Interview Answer:** "Base serializers for common use cases like user data display and registration. Extended by specialized serializers in other files."

---

### **23. views.py** ðŸ”„
**What:** Legacy or miscellaneous views
**Why:** Backward compatibility or endpoints not yet categorized
**How:**
- May contain older endpoints
- Gradually migrated to specific view files

**Interview Answer:** "Contains legacy or miscellaneous endpoints. Modern endpoints are organized in specific files like auth_views, profile_views."

---

### **24. apps.py** âš™ï¸
**What:** Django app configuration
**Why:** Register app, configure app settings
**How:**
- Defines app name as 'accounts'
- Imports signals in ready() method

**Interview Answer:** "App configuration file that registers the accounts app and ensures signals are loaded when Django starts."

---

### **25. tests.py** ðŸ§ª
**What:** Unit and integration tests
**Why:** Ensure code correctness, prevent regressions
**How:**
- Tests for registration, login, logout
- Tests for password reset flow
- Tests for profile operations
- Tests for admin endpoints

**Interview Answer:** "Comprehensive test suite covering authentication flows, password management, profile operations, and admin features."

---

## ðŸŽ“ Interview-Ready Summary

**Q: What does the accounts app do?**
A: "Handles user authentication with email-based login, registration with email verification, password management, user profiles, role-based access (admin/manager/user), and admin user management. Includes rate limiting and audit logging."

**Q: How is security implemented?**
A: "Email verification required before login, password strength validation, account lockout after failed attempts, JWT token authentication, device fingerprinting, rate limiting on registration and login, and audit logs for all security events."

**Q: What's the architecture pattern?**
A: "Organized by feature: separate views, serializers, and URLs for auth, registration, password, profile, and admin. Uses signals for cross-cutting concerns, Redis for caching, and Celery for async email sending."

**Q: How does MFA work?**
A: "During login, if device is untrusted, system generates OTP and sends via email. User must verify OTP before receiving access token. Device becomes trusted after successful verification."

---

## ðŸ“š Key Technologies
- **Django REST Framework** - API framework
- **JWT** - Token-based authentication
- **Redis** - Caching and rate limiting
- **Celery** - Async email sending
- **Django Signals** - Event-driven actions
- **Custom Auth Backend** - Email-based login

---

## ðŸ”„ Request Flow Examples

### Registration Flow:
1. POST `/api/auth/register/` â†’ `registration_views.py`
2. Validates data â†’ `serializers.py` (RegisterSerializer)
3. Creates User â†’ `models.py`
4. Signal triggers â†’ `signals.py` (auto-create Profile, send verification email)
5. Returns success response

### Login Flow:
1. POST `/api/auth/login/` â†’ `auth_views.py`
2. Authenticates â†’ `backends.py` (EmailBackend)
3. Checks device trust â†’ `devices` app
4. If untrusted â†’ Sends OTP â†’ `otp` app
5. Returns tokens + user data

### Password Reset Flow:
1. POST `/api/password/forgot/` â†’ `password_views.py`
2. Generates token â†’ `redis_utils.py`
3. Sends email â†’ Celery task
4. User clicks link â†’ POST `/api/password/reset/`
5. Validates token â†’ `password_serializers.py`
6. Updates password â†’ `models.py`

---

**Remember:** This architecture promotes **separation of concerns**, **reusability**, and **maintainability**. Each file has a single responsibility, making it easy to test, debug, and extend.
