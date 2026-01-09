"""
Celery Tasks - Async email sending with rate limiting
Email verification and notification delivery
"""

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from accounts.models import User
from notification.models import EmailNotification
import uuid
import smtplib
import logging

logger = logging.getLogger(__name__)


def _short_exc(exc: Exception) -> str:
    msg = str(exc)
    msg = " ".join(msg.split())
    if len(msg) > 180:
        return msg[:177] + "..."
    return msg


@shared_task(bind=True, rate_limit='2/s', max_retries=3)
def send_verification_email(self, user_id):
    """
    Send email verification link to user
    Rate limited to 2 emails/second to avoid Gmail throttling
    Retries with exponential backoff on failure
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Generate verification token (secure, time-limited, single-use)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Create verification link
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        verification_link = f"{frontend_url}/verify-email/{uid}/{token}/"

        # Dev helper: print link in terminal for quick testing.
        # Avoid leaking tokens in production logs.
        if getattr(settings, 'DEBUG', False) or str(getattr(settings, 'PRINT_VERIFICATION_LINK', False)).lower() == 'true':
            logger.info("Verification link for %s: %s", user.email, verification_link)
        
        # Email content
        subject = "Verify Your Email - Real MFA"
        html_message = f"""
        <h2>Welcome to Real MFA!</h2>
        <p>Thank you for registering. Please verify your email by clicking the link below:</p>
        <a href="{verification_link}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            Verify Email
        </a>
        <p>This link expires in 24 hours.</p>
        <p>If you didn't register, please ignore this email.</p>
        """
        
        # If using SMTP in development but you don't want to configure credentials,
        # skip sending and just rely on the printed link for manual verification.
        if (
            settings.EMAIL_BACKEND.endswith('smtp.EmailBackend')
            and not getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        ):
            logger.warning(
                "SMTP is configured but EMAIL_HOST_PASSWORD is empty; skipping email send for %s",
                user.email,
            )
        else:
            # Send email via SMTP
            send_mail(
                subject=subject,
                message="Please verify your email by clicking the link above.",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False
            )
        
        # Log email notification
        EmailNotification.objects.create(
            user=user,
            to_email=user.email,
            subject=subject,
            email_type='email_verification',
            template_name='email_verification.html',
            body=html_message,
            status='sent',
            sent_at=timezone.now(),
            provider='smtp',
            # Unique constraint: blank string will collide on every insert.
            provider_message_id=f"smtp-{uuid.uuid4()}"
        )
        
        logger.info(f"Verification email sent to {user.email}")
        return {'status': 'success', 'user_id': str(user_id)}
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for verification email")
        return {'status': 'failed', 'reason': 'User not found'}
        
    except smtplib.SMTPAuthenticationError as exc:
        # In dev, don't spam tracebacks or retry on auth failures.
        logger.error("Email auth failed (SMTP 535). %s", _short_exc(exc))
        if getattr(settings, 'DEBUG', False):
            return {'status': 'failed', 'reason': 'smtp_auth_failed', 'user_id': str(user_id)}
        raise self.retry(exc=exc, countdown=5 ** self.request.retries)

    except Exception as exc:
        # In dev, keep logs concise and don't retry unless explicitly desired.
        logger.error("Error sending verification email: %s", _short_exc(exc))
        if getattr(settings, 'DEBUG', False):
            return {'status': 'failed', 'reason': 'send_failed', 'user_id': str(user_id)}
        # Retry with exponential backoff (5s, 25s, 125s)
        raise self.retry(exc=exc, countdown=5 ** self.request.retries)


@shared_task(bind=True, rate_limit='2/s', max_retries=3)
def send_password_reset_otp(self, user_id, otp_code):
    """
    Send password reset OTP to user's email
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Dev helper: print OTP in terminal for quick testing
        if getattr(settings, 'DEBUG', False):
            logger.info("Password Reset OTP for %s: %s", user.email, otp_code)
        
        subject = "Password Reset Code - Real MFA"
        html_message = f"""
        <h2>Password Reset Request</h2>
        <p>You requested to reset your password. Use the code below:</p>
        <div style="background-color: #f4f4f4; padding: 20px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 5px; margin: 20px 0;">
            {otp_code}
        </div>
        <p>This code expires in <strong>15 minutes</strong>.</p>
        <p>If you didn't request this, please ignore this email or contact support if you're concerned.</p>
        """
        
        # Send email
        send_mail(
            subject=subject,
            message=f"Your password reset code is: {otp_code}. This code expires in 15 minutes.",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
        
        # Log notification
        EmailNotification.objects.create(
            user=user,
            to_email=user.email,
            subject=subject,
            email_type='password_reset',
            template_name='password_reset_otp.html',
            body=html_message,
            status='sent',
            sent_at=timezone.now(),
            provider='smtp',
            provider_message_id=f"smtp-{uuid.uuid4()}"
        )
        
        logger.info(f"Password reset OTP sent to {user.email}")
        return {'status': 'success', 'user_id': str(user_id)}
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for password reset OTP")
        return {'status': 'failed', 'reason': 'User not found'}
        
    except Exception as exc:
        logger.error("Error sending password reset OTP: %s", _short_exc(exc))
        if getattr(settings, 'DEBUG', False):
            return {'status': 'failed', 'reason': 'send_failed'}
        raise self.retry(exc=exc, countdown=5 ** self.request.retries)


@shared_task(bind=True, rate_limit='2/s', max_retries=3)
def send_device_verification_otp(self, user_id, otp_code):
    """
    Send device verification OTP to user's email
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Dev helper: print OTP in terminal for quick testing
        if getattr(settings, 'DEBUG', False):
            logger.info("Device Verification OTP for %s: %s", user.email, otp_code)
        
        subject = "Device Verification Code - Real MFA"
        html_message = f"""
        <h2>New Device Login Attempt</h2>
        <p>A login attempt was made from a new device. Use the code below to verify:</p>
        <div style="background-color: #f4f4f4; padding: 20px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 5px; margin: 20px 0;">
            {otp_code}
        </div>
        <p>This code expires in <strong>10 minutes</strong>.</p>
        <p>If this wasn't you, please change your password immediately.</p>
        """
        
        # Send email
        send_mail(
            subject=subject,
            message=f"Your device verification code is: {otp_code}. This code expires in 10 minutes.",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
        
        # Log notification
        EmailNotification.objects.create(
            user=user,
            to_email=user.email,
            subject=subject,
            email_type='device_verification',
            template_name='device_verification_otp.html',
            body=html_message,
            status='sent',
            sent_at=timezone.now(),
            provider='smtp',
            provider_message_id=f"smtp-{uuid.uuid4()}"
        )
        
        logger.info(f"Device verification OTP sent to {user.email}")
        return {'status': 'success', 'user_id': str(user_id)}
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for device verification OTP")
        return {'status': 'failed', 'reason': 'User not found'}
        
    except Exception as exc:
        logger.error("Error sending device verification OTP: %s", _short_exc(exc))
        if getattr(settings, 'DEBUG', False):
            return {'status': 'failed', 'reason': 'send_failed'}
        raise self.retry(exc=exc, countdown=5 ** self.request.retries)
