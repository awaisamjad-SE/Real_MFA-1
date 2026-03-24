# Audit Logs App - File by File Tutorial

## 1) What this app does
Stores security timeline for incident response and compliance.

## 2) models.py
Core fields in AuditLog:
- actor (nullable user)
- event_type
- severity
- ip_address
- user_agent
- metadata JSON
- created_at

Index suggestions:
- event_type + created_at
- actor + created_at

## 3) admin.py
Read-only list configuration with fast filters.

## 4) views.py (optional)
Admin-only page for filtered search.

## 5) where to call audit logging
- accounts views (register/login)
- otp verify views
- device trust/revoke actions
- password reset actions

## 6) log format advice
Use stable event names:
- auth.register.success
- auth.login.failed
- mfa.otp.verify.failed
- device.trust.added

## 7) mini exercise
1. create AuditLog model
2. write helper function log_event
3. call helper in register and login views
4. verify records in admin
