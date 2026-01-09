"""
Password Serializers - Password reset and forgot password
"""

import secrets
from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from hashlib import sha256
from accounts.models import User, PasswordHistory
from accounts.redis_utils import redis_client
from otp.utils import generate_otp_code, hash_otp, create_otp


class ForgotPasswordSerializer(serializers.Serializer):
    """
    Request password reset - sends OTP to email
    
    Redis Keys:
    - password_reset:{user_id} -> OTP ID (TTL: 15 minutes)
    - password_reset_token:{token} -> user_id (TTL: 15 minutes)
    
    Rate Limiting:
    - 3 requests per hour per email
    """
    email = serializers.EmailField()
    
    def validate_email(self, value):
        # Normalize email
        email = value.lower().strip()
        
        # Check rate limit (100 per hour for development)
        rate_key = f"password_reset_rate:{sha256(email.encode()).hexdigest()}"
        current_count = redis_client.get(rate_key)
        
        if current_count and int(current_count) >= 100:
            raise serializers.ValidationError(
                "Too many password reset requests. Please try again later."
            )
        
        return email
    
    def save(self):
        email = self.validated_data['email']
        
        # Check if user exists
        try:
            user = User.objects.get(email=email, is_active=True, is_deleted=False)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                "email": "No account found with this email address."
            })
        
        # Increment rate limit
        rate_key = f"password_reset_rate:{sha256(email.encode()).hexdigest()}"
        pipe = redis_client.pipeline()
        pipe.incr(rate_key)
        pipe.expire(rate_key, 60)  # 1 minute
        pipe.execute()
        
        # Invalidate existing password reset OTPs
        from otp.models import OTP
        OTP.objects.filter(
            user=user,
            purpose='password_reset',
            is_used=False
        ).update(is_used=True)
        
        # Create new OTP
        otp, otp_code = create_otp(
            user=user,
            purpose='password_reset',
            target=email,
            expires_minutes=15
        )
        
        # Generate a secure reset token (for use in reset link)
        reset_token = secrets.token_urlsafe(32)
        
        # Store mapping: token -> user_id and otp_id
        redis_client.setex(
            f"password_reset_token:{reset_token}",
            900,  # 15 minutes
            f"{user.id}:{otp.id}"
        )
        
        # Store pending reset
        redis_client.setex(
            f"password_reset:{user.id}",
            900,
            str(otp.id)
        )
        
        # Send OTP via email (async Celery task)
        from Real_MFA.celery_tasks import send_password_reset_otp
        send_password_reset_otp.delay(str(user.id), otp_code)
        
        # Return response
        return {
            'status': 'success',
            'message': 'Password reset code sent to your email.',
            'expires_in': 900,
            'reset_token': reset_token,
            'user_id': str(user.id)
        }


class ResetPasswordSerializer(serializers.Serializer):
    """
    Reset password with token/OTP
    Supports two methods:
    1. Token + OTP code (from email)
    2. User ID + OTP code (direct verification)
    """
    # Method 1: Token-based
    reset_token = serializers.CharField(required=False)
    
    # Method 2: User ID-based
    user_id = serializers.UUIDField(required=False)
    
    # OTP code (required for both methods)
    otp_code = serializers.CharField(min_length=6, max_length=6)
    
    # New password
    new_password = serializers.CharField(min_length=8, max_length=128)
    new_password2 = serializers.CharField(min_length=8, max_length=128)
    
    def validate(self, attrs):
        reset_token = attrs.get('reset_token')
        user_id = attrs.get('user_id')
        otp_code = attrs.get('otp_code')
        new_password = attrs.get('new_password')
        new_password2 = attrs.get('new_password2')
        
        # Must provide either reset_token or user_id
        if not reset_token and not user_id:
            raise serializers.ValidationError({
                "error": "Please provide either reset_token or user_id."
            })
        
        # Validate passwords match
        if new_password != new_password2:
            raise serializers.ValidationError({
                "new_password2": "Passwords do not match."
            })
        
        # Get user and OTP ID
        if reset_token:
            # Token-based method
            token_data = redis_client.get(f"password_reset_token:{reset_token}")
            if not token_data:
                raise serializers.ValidationError({
                    "reset_token": "Invalid or expired reset token."
                })
            
            user_id_str, otp_id_str = token_data.split(':')
            try:
                user = User.objects.get(id=user_id_str, is_active=True, is_deleted=False)
            except User.DoesNotExist:
                raise serializers.ValidationError({
                    "error": "User not found."
                })
            
            attrs['otp_id'] = otp_id_str
        else:
            # User ID-based method
            try:
                user = User.objects.get(id=user_id, is_active=True, is_deleted=False)
            except User.DoesNotExist:
                raise serializers.ValidationError({
                    "user_id": "Invalid user."
                })
            
            # Get pending OTP ID
            otp_id = redis_client.get(f"password_reset:{user_id}")
            if not otp_id:
                raise serializers.ValidationError({
                    "error": "No pending password reset. Request a new one."
                })
            
            attrs['otp_id'] = otp_id
        
        # Verify OTP
        from otp.models import OTP
        try:
            otp = OTP.objects.get(
                id=attrs['otp_id'],
                user=user,
                purpose='password_reset',
                is_used=False
            )
        except OTP.DoesNotExist:
            raise serializers.ValidationError({
                "error": "Invalid or expired reset code."
            })
        
        # Check OTP validity
        if not otp.is_valid():
            if otp.attempts >= otp.max_attempts:
                raise serializers.ValidationError({
                    "error": "Too many failed attempts. Request a new reset code."
                })
            if timezone.now() >= otp.expires_at:
                raise serializers.ValidationError({
                    "error": "Reset code expired. Request a new one."
                })
        
        # Verify OTP code
        if otp.code_hash != hash_otp(otp_code):
            otp.increment_attempts()
            remaining = otp.max_attempts - otp.attempts
            raise serializers.ValidationError({
                "otp_code": f"Invalid code. {remaining} attempts remaining."
            })
        
        # Validate password strength
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            raise serializers.ValidationError({
                "new_password": list(e.messages)
            })
        
        # Check password history (last 5 passwords)
        from django.contrib.auth.hashers import check_password
        
        password_history = PasswordHistory.objects.filter(
            user=user
        ).order_by('-created_at')[:5]
        
        for ph in password_history:
            if check_password(new_password, ph.password_hash):
                raise serializers.ValidationError({
                    "new_password": "Cannot reuse your last 5 passwords."
                })
        
        # Also check current password
        if user.check_password(new_password):
            raise serializers.ValidationError({
                "new_password": "New password cannot be the same as your current password."
            })
        
        attrs['user'] = user
        attrs['otp'] = otp
        attrs['reset_token'] = reset_token
        return attrs
    
    def save(self):
        user = self.validated_data['user']
        otp = self.validated_data['otp']
        reset_token = self.validated_data.get('reset_token')
        new_password = self.validated_data['new_password']
        
        # Save current password to history
        PasswordHistory.objects.create(
            user=user,
            password_hash=user.password,
            changed_from_ip=self.context.get('request').META.get('REMOTE_ADDR')
        )
        
        # Set new password
        user.set_password(new_password)
        user.password_changed_at = timezone.now()
        user.require_password_change = False
        user.save(update_fields=['password', 'password_changed_at', 'require_password_change'])
        
        # Mark OTP as used
        otp.mark_used()
        
        # Clean up Redis keys
        redis_client.delete(f"password_reset:{user.id}")
        if reset_token:
            redis_client.delete(f"password_reset_token:{reset_token}")
        
        # Revoke all sessions for security
        from devices.models import Session
        revoked_count = Session.revoke_all_for_user(user=user, reason='password_reset')
        
        return {
            'status': 'success',
            'message': 'Password reset successfully. Please login with your new password.',
            'sessions_revoked': revoked_count
        }
