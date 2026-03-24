# Notification App - File by File Tutorial

## 1) What this app does
Sends and tracks security notifications.

## 2) models.py
Main entities:
- EmailNotification
- NotificationLog
- NotificationPreference

Important design:
- provider_message_id should be unique and always generated if provider does not return one.
- metadata JSON must be JSON serializable.

## 3) services.py or utils.py
Responsibilities:
- compose subject/body
- choose template
- send via backend
- record status and errors

Pattern:
1. prepare payload
2. create notification record
3. send email
4. update status sent/failed

## 4) templates/notification/email/
Files by event type:
- email_verification.html
- otp_login.html
- password_changed.html
- new_device_login.html

## 5) admin.py
Expose filters:
- status
- email_type
- provider
- created_at

## 6) failure strategy
- if notification fails, business flow should continue where non-critical
- always log concise error
- retries via celery task if needed

## 7) mini exercise
1. implement send_security_alert helper
2. add template rendering fallback
3. add unique provider id generation
4. add test for duplicate protection
