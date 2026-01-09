"""
OTP Utilities - Generate, hash, and verify OTP codes
"""

import hashlib
import secrets
from django.utils import timezone


def generate_otp_code(length=6):
    """Generate a secure random OTP code"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(length)])


def hash_otp(code):
    """Hash OTP code for storage"""
    return hashlib.sha256(code.encode()).hexdigest()


def verify_otp_hash(code, code_hash):
    """Verify OTP code against stored hash"""
    return hash_otp(code) == code_hash


def get_client_ip(request):
    """Extract client IP address from request"""
    if request is None:
        return '0.0.0.0'
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def create_otp(user, purpose, target=None, ip_address=None, expires_minutes=10):
    """
    Create a new OTP record for a user
    
    Args:
        user: User object
        purpose: OTP purpose (email_verification, device_verification, etc.)
        target: Target email/phone (defaults to user's email)
        ip_address: Client IP address
        expires_minutes: Minutes until OTP expires
    
    Returns:
        tuple: (OTP object, plain_code)
    """
    from .models import OTP
    
    otp_code = generate_otp_code(6)
    expires_at = timezone.now() + timezone.timedelta(minutes=expires_minutes)
    
    otp = OTP.objects.create(
        user=user,
        code_hash=hash_otp(otp_code),
        purpose=purpose,
        target=target or user.email,
        ip_address=ip_address,
        expires_at=expires_at
    )
    
    return otp, otp_code


def invalidate_user_otps(user, purpose):
    """Invalidate all unused OTPs for a user with given purpose"""
    from .models import OTP
    
    OTP.objects.filter(
        user=user,
        purpose=purpose,
        is_used=False
    ).update(is_used=True)
