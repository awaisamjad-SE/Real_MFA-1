"""
Email Verification Serializers - Token validation and email verification logic
"""

from rest_framework import serializers
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from .models import User
from .redis_utils import VerificationTokenManager, ResendLimiter, CooldownManager
from Real_MFA.celery_tasks import send_verification_email


class EmailVerificationSerializer(serializers.Serializer):
    """Verify email with token and mark user as verified"""
    uid = serializers.CharField()
    token = serializers.CharField()
    
    def validate(self, attrs):
        uid = attrs.get('uid')
        token = attrs.get('token')
        
        try:
            # Decode user ID from base64
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Invalid verification link.")
        
        # Validate token (Django's token generator checks timestamp)
        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError("Verification link expired or invalid.")
        
        attrs['user'] = user
        return attrs
    
    def save(self):
        """Mark user as verified (idempotent - safe to call multiple times)"""
        user = self.validated_data['user']
        
        # Mark as verified
        user.email_verified = True
        user.save(update_fields=['email_verified'])
        
        # Invalidate token
        VerificationTokenManager.invalidate_token(user.id)
        
        return user


class ResendVerificationEmailSerializer(serializers.Serializer):
    """Request resend of verification email with rate limiting"""
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            self.user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        
        # Check if already verified
        if self.user.email_verified:
            raise serializers.ValidationError("Email already verified.")
        
        return value
    
    def save(self):
        user = self.user
        
        # Check cooldown (60 seconds)
        can_resend, message = CooldownManager.can_resend_now(user.id)
        if not can_resend:
            raise serializers.ValidationError(message)
        
        # Check hourly limit (max 4/hour)
        can_resend, message = ResendLimiter.can_resend(user.id)
        if not can_resend:
            raise serializers.ValidationError(message)
        
        # Record this resend attempt
        ResendLimiter.record_resend(user.id)
        CooldownManager.set_cooldown(user.id)
        
        # Invalidate previous tokens
        VerificationTokenManager.invalidate_previous_tokens(user.id)
        
        # Generate new token and store
        from django.contrib.auth.tokens import default_token_generator
        token = default_token_generator.make_token(user)
        VerificationTokenManager.store_token(user.id, token)
        
        # Enqueue new email task
        send_verification_email.delay(str(user.id))
        
        return {"message": "Verification email resent.", "remaining": ResendLimiter.get_remaining_resends(user.id)}
