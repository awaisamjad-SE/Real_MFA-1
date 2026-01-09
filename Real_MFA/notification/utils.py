"""
Notification Utilities
Send security alerts and notifications to users
"""

from django.utils import timezone
from django.template.loader import render_to_string
from .models import EmailNotification, NotificationLog, NotificationPreference
import logging

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Extract client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_device_info(request):
    """Extract device information from request"""
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    return {
        'user_agent': user_agent,
        'ip_address': get_client_ip(request),
    }


def send_security_alert(user, alert_type, context, request=None):
    """
    Send security alert to user
    
    Args:
        user: User instance
        alert_type: Type of alert (new_device_login, mfa_enabled, mfa_disabled, password_changed, profile_changed)
        context: Dict with alert-specific context data
        request: HttpRequest object (optional)
    """
    # Check if user wants to receive security alerts
    try:
        prefs = NotificationPreference.objects.get(user=user)
        if not prefs.email_alerts:
            logger.info(f"User {user.email} has email alerts disabled")
            return
    except NotificationPreference.DoesNotExist:
        # Default to sending alerts if no preference set
        pass
    
    # Add device info if request provided
    if request:
        device_info = get_device_info(request)
        context.update(device_info)
    
    # Map alert types to email details
    alert_templates = {
        'new_device_login': {
            'subject': '🔐 New Device Login Detected',
            'template': 'notification/email/new_device_login.html',
            'email_type': 'security_alert'
        },
        'mfa_enabled': {
            'subject': '✅ Two-Factor Authentication Enabled',
            'template': 'notification/email/mfa_enabled.html',
            'email_type': 'security_alert'
        },
        'mfa_disabled': {
            'subject': '⚠️ Two-Factor Authentication Disabled',
            'template': 'notification/email/mfa_disabled.html',
            'email_type': 'security_alert'
        },
        'password_changed': {
            'subject': '🔑 Password Changed Successfully',
            'template': 'notification/email/password_changed.html',
            'email_type': 'security_alert'
        },
        'profile_changed': {
            'subject': '👤 Profile Information Updated',
            'template': 'notification/email/profile_changed.html',
            'email_type': 'account_alert'
        },
        'suspicious_login': {
            'subject': '🚨 Suspicious Login Attempt',
            'template': 'notification/email/suspicious_login.html',
            'email_type': 'security_alert'
        },
        'device_verified': {
            'subject': '✓ New Device Verified',
            'template': 'notification/email/device_verified.html',
            'email_type': 'security_alert'
        }
    }
    
    if alert_type not in alert_templates:
        logger.error(f"Unknown alert type: {alert_type}")
        return
    
    alert_config = alert_templates[alert_type]
    
    # Add common context
    context.update({
        'user': user,
        'timestamp': timezone.now(),
        'site_name': 'Real MFA',
    })
    
    # Render email body
    try:
        body = render_to_string(alert_config['template'], context)
    except Exception as e:
        logger.error(f"Failed to render template {alert_config['template']}: {e}")
        # Fallback to simple text
        body = f"{alert_config['subject']}\n\n"
        for key, value in context.items():
            if key not in ['user', 'site_name']:
                body += f"{key}: {value}\n"
    
    # Create email notification
    email_notification = EmailNotification.objects.create(
        user=user,
        to_email=user.email,
        subject=alert_config['subject'],
        email_type=alert_config['email_type'],
        template_name=alert_config['template'],
        body=body,
        status='pending'
    )
    
    # Create notification log
    NotificationLog.objects.create(
        user=user,
        channel='email',
        subject=alert_config['subject'],
        message=body,
        recipient=user.email,
        delivered=False,
        metadata={'alert_type': alert_type, **context}
    )
    
    # TODO: Trigger async email sending via Celery
    # send_email_task.delay(email_notification.id)
    
    logger.info(f"Security alert '{alert_type}' queued for user {user.email}")
    
    return email_notification


def notify_new_device_login(user, device, request=None):
    """Notify user about new device login"""
    context = {
        'device_name': device.device_name or 'Unknown Device',
        'device_type': device.get_device_type_display(),
        'browser': device.browser,
        'os': device.os,
        'location': f"{device.city}, {device.country}" if device.city and device.country else 'Unknown',
        'ip_address': device.ip_address,
        'login_time': device.created_at,
    }
    return send_security_alert(user, 'new_device_login', context, request)


def notify_mfa_enabled(user, mfa_method, request=None):
    """Notify user that MFA was enabled"""
    context = {
        'mfa_method': mfa_method,
        'enabled_at': timezone.now(),
    }
    return send_security_alert(user, 'mfa_enabled', context, request)


def notify_mfa_disabled(user, mfa_method, request=None):
    """Notify user that MFA was disabled"""
    context = {
        'mfa_method': mfa_method,
        'disabled_at': timezone.now(),
    }
    return send_security_alert(user, 'mfa_disabled', context, request)


def notify_password_changed(user, request=None):
    """Notify user that password was changed"""
    context = {
        'changed_at': timezone.now(),
    }
    return send_security_alert(user, 'password_changed', context, request)


def notify_profile_changed(user, changed_fields, request=None):
    """Notify user that profile was changed"""
    context = {
        'changed_fields': changed_fields,
        'changed_at': timezone.now(),
    }
    return send_security_alert(user, 'profile_changed', context, request)


def notify_device_verified(user, device, request=None):
    """Notify user that device was verified"""
    context = {
        'device_name': device.device_name or 'Unknown Device',
        'device_type': device.get_device_type_display(),
        'verified_at': device.verified_at,
    }
    return send_security_alert(user, 'device_verified', context, request)


def notify_suspicious_login(user, reason, request=None):
    """Notify user about suspicious login attempt"""
    context = {
        'reason': reason,
        'attempt_time': timezone.now(),
    }
    return send_security_alert(user, 'suspicious_login', context, request)
