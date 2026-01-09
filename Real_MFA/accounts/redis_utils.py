"""
Redis Utilities - Rate limiting for email resend and token management
"""

import json
import time
from django.conf import settings
from django.core.cache import cache
from datetime import datetime, timedelta

try:
    import redis
except Exception:  # pragma: no cover
    redis = None


class _CacheKV:
    """Small Redis-like KV wrapper backed by Django cache.

    This keeps the rest of the codebase unchanged while allowing local/dev usage
    without requiring a running Redis server.
    """

    _EXP_SUFFIX = ":__exp"
    _DEFAULT_INCR_TIMEOUT = 3600

    def _exp_key(self, key: str) -> str:
        return f"{key}{self._EXP_SUFFIX}"

    def get(self, key):
        return cache.get(key)

    def set(self, key, value):
        cache.set(key, value, timeout=None)

    def setex(self, key, ttl_seconds, value):
        ttl_seconds = int(ttl_seconds)
        cache.set(key, value, timeout=ttl_seconds)
        cache.set(self._exp_key(key), time.time() + ttl_seconds, timeout=ttl_seconds)

    def delete(self, key):
        cache.delete(key)
        cache.delete(self._exp_key(key))

    def exists(self, key):
        return cache.get(key) is not None

    def ttl(self, key):
        expires_at = cache.get(self._exp_key(key))
        if not expires_at:
            return -1
        remaining = int(expires_at - time.time())
        return max(0, remaining)

    def expire(self, key, ttl_seconds):
        value = cache.get(key)
        if value is None:
            return False
        self.setex(key, ttl_seconds, value)
        return True

    def incr(self, key):
        current = cache.get(key)
        try:
            current_int = int(current) if current is not None else 0
        except (TypeError, ValueError):
            current_int = 0
        new_value = current_int + 1

        # Preserve existing TTL if present; otherwise use a safe default.
        remaining_ttl = self.ttl(key)
        if remaining_ttl > 0:
            self.setex(key, remaining_ttl, new_value)
        else:
            cache.set(key, new_value, timeout=self._DEFAULT_INCR_TIMEOUT)
            cache.set(self._exp_key(key), time.time() + self._DEFAULT_INCR_TIMEOUT, timeout=self._DEFAULT_INCR_TIMEOUT)

        return new_value


def _get_kv_client():
    """Return a Redis client if available/reachable, else a cache-backed KV."""

    if redis is None:
        return _CacheKV()

    try:
        client = redis.StrictRedis(
            host=getattr(settings, 'REDIS_HOST', 'localhost'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            db=getattr(settings, 'REDIS_DB', 0),
            decode_responses=True,
            socket_connect_timeout=0.2,
            socket_timeout=0.5,
        )
        client.ping()
        return client
    except Exception:
        return _CacheKV()

# KV connection (Redis if available, otherwise cache-backed)
redis_client = _get_kv_client()


class ResendLimiter:
    """Rate limit email resend attempts (max 4/hour, 60sec cooldown)"""
    
    @staticmethod
    def can_resend(user_id):
        """Check if user can resend verification email"""
        key = f"resend_limit:{user_id}"
        current_count = redis_client.get(key)
        
        if current_count is None:
            return True, "Can resend"
        
        count = int(current_count)
        if count >= 4:
            ttl = redis_client.ttl(key)
            return False, f"Max resends reached. Try again in {ttl} seconds."
        
        return True, "Can resend"
    
    @staticmethod
    def record_resend(user_id):
        """Record resend attempt and set rate limit"""
        key = f"resend_limit:{user_id}"
        
        # Increment counter
        count = redis_client.incr(key)
        
        # Set expiry to 1 hour on first attempt
        if count == 1:
            redis_client.expire(key, 3600)
    
    @staticmethod
    def get_remaining_resends(user_id):
        """Get remaining resend attempts for user"""
        key = f"resend_limit:{user_id}"
        current_count = redis_client.get(key)
        
        if current_count is None:
            return 4
        
        return max(0, 4 - int(current_count))


class VerificationTokenManager:
    """Manage verification tokens and invalidation"""
    
    @staticmethod
    def invalidate_previous_tokens(user_id):
        """Invalidate all previous verification tokens for user"""
        key = f"verification_token:{user_id}"
        redis_client.delete(key)
    
    @staticmethod
    def store_token(user_id, token, expires_in=86400):
        """Store verification token (24 hours default)"""
        key = f"verification_token:{user_id}"
        redis_client.setex(key, expires_in, token)
    
    @staticmethod
    def verify_token(user_id, token):
        """Check if token is valid (not invalidated)"""
        key = f"verification_token:{user_id}"
        stored_token = redis_client.get(key)
        return stored_token == token if stored_token else False
    
    @staticmethod
    def invalidate_token(user_id):
        """Invalidate token after verification"""
        key = f"verification_token:{user_id}"
        redis_client.delete(key)


class CooldownManager:
    """Manage cooldown between resend attempts (60 seconds)"""
    
    @staticmethod
    def can_resend_now(user_id):
        """Check if 60 second cooldown has passed"""
        key = f"resend_cooldown:{user_id}"
        if redis_client.exists(key):
            ttl = redis_client.ttl(key)
            return False, f"Please wait {ttl} seconds before resending"
        
        return True, "Can resend"
    
    @staticmethod
    def set_cooldown(user_id):
        """Set 60 second cooldown after resend"""
        key = f"resend_cooldown:{user_id}"
        redis_client.setex(key, 60, "1")
