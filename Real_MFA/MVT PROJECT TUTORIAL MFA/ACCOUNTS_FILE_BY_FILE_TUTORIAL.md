# Accounts App - File by File Tutorial

## 1) What this app does
Accounts is the identity entry point:
- Register user
- Login password phase
- Profile management
- Password change/reset start
- Hand-off to MFA step

## 2) models.py - how to think
Create only fields required by features:
- user identity
- verification flags
- security counters
- timestamps

Suggested entities:
- User (custom) or UserProfile (if extending default User)
- Profile
- PasswordHistory

Checklist while writing models:
1. What must be unique? email/username
2. What can be null? optional profile fields
3. What needs index? login/security fields
4. What behavior belongs to model methods? lock/unlock, increment_failed_login

## 3) forms.py - validation layer
Main forms:
- RegisterForm
- LoginForm
- ProfileUpdateForm
- PasswordChangeForm

Why this file matters:
- avoids view bloat
- keeps reusable validation in one place
- gives clean template errors

RegisterForm validation should include:
- email uniqueness
- username uniqueness
- password match
- password complexity

## 4) views.py - request orchestration
Use small views that call form + service helpers.

Core views:
- register_view
- login_view
- logout_view
- dashboard_view
- profile_view

Login pattern:
1. Validate credentials
2. Check lockout and email verification
3. If MFA enabled -> set pending session and redirect OTP page
4. Else do login and redirect dashboard

Keep side effects wrapped safely:
- email send failures should not crash whole request
- write audit logs for success/failure

## 5) urls.py - route map
Recommended names:
- auth/register/
- auth/login/
- auth/logout/
- dashboard/
- profile/

Use app_name for namespacing:
- app_name = "accounts"

Then use reverse names in templates:
- accounts:login
- accounts:register

## 6) templates/accounts/
Minimum files:
- register.html
- login.html
- dashboard.html
- profile.html

Template rules:
- always include csrf token
- show field and non-field errors
- disable submit button on post

## 7) signals.py
Use only for light, predictable work:
- create profile on user create
- optional account notification flags

Do not put heavy business logic here.

## 8) admin.py
Expose security support fields in admin list:
- email_verified
- mfa_enabled
- failed_login_attempts
- account_locked_until

## 9) mini exercise
Build this in order:
1. register form + view + template
2. login form + view + template
3. profile page
4. lockout rule and tests
