"""
Accounts Views - Registration with rate limiting (2-3/min per IP/device)
"""

import random
import time
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import BaseThrottle
from django.core.cache import cache
from .serializers import RegisterSerializer
from .verification_serializers import EmailVerificationSerializer, ResendVerificationEmailSerializer


# Pakistani names for demo API
PAKISTANI_FIRST_NAMES = [
    "Ahmed", "Ali", "Hassan", "Hussain", "Muhammad", "Usman", "Bilal", "Imran",
    "Kamran", "Faisal", "Saad", "Zain", "Hamza", "Omar", "Asad", "Tariq",
    "Shahid", "Khalid", "Rashid", "Waseem", "Nadeem", "Saleem", "Kareem",
    "Amir", "Fahad", "Rizwan", "Adnan", "Arslan", "Atif", "Waqas",
    "Ayesha", "Fatima", "Khadija", "Zainab", "Maryam", "Aisha", "Sana",
    "Hira", "Maham", "Noor", "Sara", "Amna", "Bushra", "Rabia", "Samina",
    "Nadia", "Farah", "Uzma", "Asma", "Sadia", "Huma", "Mehwish", "Sidra",
    "Arooj", "Iqra", "Kinza", "Nimra", "Aliya", "Sobia", "Rubina"
]

PAKISTANI_LAST_NAMES = [
    "Khan", "Ahmed", "Ali", "Malik", "Sheikh", "Butt", "Chaudhry", "Qureshi",
    "Hashmi", "Syed", "Mirza", "Rana", "Bhatti", "Gill", "Mughal", "Durrani",
    "Afridi", "Yousafzai", "Shah", "Baloch", "Abbasi", "Raza", "Iqbal", "Hussain",
    "Javed", "Aslam", "Akram", "Saleem", "Rehman", "Farooq"
]


def generate_pakistani_people(count=100):
    """Generate list of Pakistani names with ages"""
    people = []
    for i in range(1, count + 1):
        first_name = random.choice(PAKISTANI_FIRST_NAMES)
        last_name = random.choice(PAKISTANI_LAST_NAMES)
        age = random.randint(18, 65)
        people.append({
            "id": i,
            "name": f"{first_name} {last_name}",
            "age": age
        })
    return people


class RegistrationRateThrottle(BaseThrottle):
    """Rate limit: 3 registrations per minute per IP AND per device"""
    
    RATE_LIMIT = 3  # max registrations
    WINDOW = 60     # 1 minute in seconds
    
    def get_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
    
    def get_device_fingerprint(self, request):
        """Extract device fingerprint from request data"""
        try:
            device_data = request.data.get('device', {})
            return device_data.get('fingerprint_hash', None)
        except Exception:
            return None
    
    def get_ttl(self, key):
        """Get TTL for cache key (Redis-compatible)"""
        try:
            redis_client = cache._cache.get_client(None, write=False)
            cache_key = cache.make_key(key)
            ttl = redis_client.ttl(cache_key)
            return ttl if ttl and ttl > 0 else 0
        except Exception:
            return 0
    
    def allow_request(self, request, view):
        """Allow max 3 registrations per minute per IP and per device"""
        ip = self.get_ip(request)
        fingerprint = self.get_device_fingerprint(request)
        
        # Check IP rate limit
        ip_key = f'reg_throttle:ip:{ip}'
        ip_count = cache.get(ip_key, 0)
        
        if ip_count >= self.RATE_LIMIT:
            self.wait_time = self.get_ttl(ip_key)
            self.blocked_by = 'ip'
            return False
        
        # Check device rate limit (if fingerprint provided)
        if fingerprint:
            device_key = f'reg_throttle:device:{fingerprint}'
            device_count = cache.get(device_key, 0)
            
            if device_count >= self.RATE_LIMIT:
                self.wait_time = self.get_ttl(device_key)
                self.blocked_by = 'device'
                return False
        
        # Passed both checks - increment counters
        cache.set(ip_key, ip_count + 1, self.WINDOW)
        if fingerprint:
            device_key = f'reg_throttle:device:{fingerprint}'
            device_count = cache.get(device_key, 0)
            cache.set(device_key, device_count + 1, self.WINDOW)
        
        return True


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register new user with device fingerprinting
    Rate limited: 3 registrations per minute per IP and per device
    
    POST /api/auth/register/
    {
      "username": "john",
      "email": "john@example.com",
      "password": "SecurePass123!",
      "password2": "SecurePass123!",
      "phone_number": "+1234567890",
      "device": {
        "fingerprint_hash": "abc123...",
        "device_type": "mobile",
        "browser": "Safari",
        "os": "iOS"
      }
    }
    
    Response (201):
    {
      "id": "uuid",
      "email": "john@example.com",
      "username": "john",
      "message": "Registration successful. Check your email to verify.",
      "device_id": "uuid"
    }
    """
    # Check rate limit (3 per minute per IP and per device)
    throttle = RegistrationRateThrottle()
    if not throttle.allow_request(request, None):
        blocked_by = getattr(throttle, 'blocked_by', 'ip')
        wait_time = getattr(throttle, 'wait_time', 60)
        return Response(
            {
                "error": f"Too many registration attempts from this {blocked_by}. Try again in {wait_time}s.",
                "blocked_by": blocked_by,
                "retry_after": wait_time
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    # Validate and create user
    serializer = RegisterSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "message": "Registration successful. Check your email to verify.",
                "device_id": str(user.devices.first().id) if user.devices.exists() else None
            },
            status=status.HTTP_201_CREATED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """
    Verify email with token from link
    
    POST /api/auth/verify-email/
    {
      "uid": "base64_user_id",
      "token": "token_string"
    }
    
    Response (200):
    {"message": "Email verified successfully. You can now login."}
    """
    serializer = EmailVerificationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "Email verified successfully. You can now login."},
            status=status.HTTP_200_OK
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification_email(request):
    """
    Resend verification email with rate limiting
    Rate limits: 4 resends per hour, 60 second cooldown between resends
    
    POST /api/auth/resend-verification-email/
    {
      "email": "john@example.com"
    }
    
    Response (200):
    {
      "message": "Verification email resent.",
      "remaining": 3
    }
    """
    serializer = ResendVerificationEmailSerializer(data=request.data)
    if serializer.is_valid():
        try:
            result = serializer.save()
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
# DEMO API - Pakistani Names with Caching (5 minutes)
# =============================================================================

CACHE_KEY = "demo_pakistani_people"
CACHE_TIMEOUT = 100  # 5 minutes in seconds


@api_view(['GET'])
@permission_classes([AllowAny])
def demo_pakistani_names(request):
    """
    Demo API: Returns 100 Pakistani names with ages.
    Data is cached for 5 minutes.
    
    GET /api/demo/pakistani-names/
    
    Response (200):
    {
      "cached": true/false,
      "cache_expires_in": 285,
      "generated_at": "2026-01-07T16:30:00Z",
      "count": 100,
      "data": [
        {"id": 1, "name": "Ahmed Khan", "age": 32},
        {"id": 2, "name": "Fatima Ali", "age": 28},
        ...
      ]
    }
    """
    start_time = time.time()
    
    # Try to get from cache
    cached_data = cache.get(CACHE_KEY)
    
    if cached_data:
        # Data found in cache - get TTL from Redis
        elapsed = time.time() - start_time
        ttl = None
        try:
            # Access underlying Redis client for TTL
            redis_client = cache._cache.get_client(None, write=False)
            cache_key_versioned = cache.make_key(CACHE_KEY)
            ttl = redis_client.ttl(cache_key_versioned)
            if ttl and ttl < 0:
                ttl = None  # Key doesn't exist or no TTL
        except Exception:
            pass  # Fallback if Redis client not accessible
        
        return Response({
            "cached": True,
            "cache_expires_in": ttl,
            "response_time_ms": round(elapsed * 1000, 2),
            "generated_at": cached_data["generated_at"],
            "count": len(cached_data["data"]),
            "data": cached_data["data"]
        })
    
    # Generate fresh data
    from django.utils import timezone
    people = generate_pakistani_people(100)
    generated_at = timezone.now().isoformat()
    
    # Store in cache for 5 minutes
    cache.set(CACHE_KEY, {
        "generated_at": generated_at,
        "data": people
    }, CACHE_TIMEOUT)
    
    elapsed = time.time() - start_time
    return Response({
        "cached": False,
        "cache_expires_in": CACHE_TIMEOUT,
        "response_time_ms": round(elapsed * 1000, 2),
        "generated_at": generated_at,
        "count": len(people),
        "data": people
    })


# =============================================================================
# HEAVY DEMO API - 10,000 entries for cache testing (simulates slow DB/API)
# =============================================================================

HEAVY_CACHE_KEY = "demo_heavy_data"
HEAVY_CACHE_TIMEOUT = 300  # 5 minutes


def generate_heavy_data(count=10000):
    """
    Generate large dataset with simulated processing delay.
    Simulates expensive database query or external API call.
    """
    # Simulate slow processing (1 second delay)
    time.sleep(1)
    
    cities = ["Karachi", "Lahore", "Islamabad", "Faisalabad", "Rawalpindi", 
              "Multan", "Peshawar", "Quetta", "Sialkot", "Gujranwala"]
    departments = ["IT", "HR", "Finance", "Marketing", "Operations", 
                   "Sales", "Engineering", "Support", "Legal", "Admin"]
    
    data = []
    for i in range(1, count + 1):
        first_name = random.choice(PAKISTANI_FIRST_NAMES)
        last_name = random.choice(PAKISTANI_LAST_NAMES)
        data.append({
            "id": i,
            "name": f"{first_name} {last_name}",
            "age": random.randint(18, 65),
            "email": f"{first_name.lower()}.{last_name.lower()}{i}@example.com",
            "city": random.choice(cities),
            "department": random.choice(departments),
            "salary": random.randint(30000, 500000),
            "is_active": random.choice([True, True, True, False]),  # 75% active
        })
    return data


@api_view(['GET'])
@permission_classes([AllowAny])
def demo_heavy_data(request):
    """
    Heavy Demo API: Returns 10,000 records with simulated 1-second delay.
    Perfect for testing cache performance.
    
    First request: ~1000-1200ms (slow - generating data)
    Cached requests: ~1-5ms (fast - from Redis)
    
    GET /api/demo/heavy-data/
    
    Response (200):
    {
      "cached": true/false,
      "cache_expires_in": 285,
      "response_time_ms": 1.23,
      "generated_at": "2026-01-07T16:30:00Z",
      "count": 10000,
      "data": [...]
    }
    """
    start_time = time.time()
    
    # Try to get from cache
    cached_data = cache.get(HEAVY_CACHE_KEY)
    
    if cached_data:
        # Data found in cache - super fast!
        elapsed = time.time() - start_time
        ttl = None
        try:
            redis_client = cache._cache.get_client(None, write=False)
            cache_key_versioned = cache.make_key(HEAVY_CACHE_KEY)
            ttl = redis_client.ttl(cache_key_versioned)
            if ttl and ttl < 0:
                ttl = None
        except Exception:
            pass
        
        return Response({
            "cached": True,
            "cache_expires_in": ttl,
            "response_time_ms": round(elapsed * 1000, 2),
            "generated_at": cached_data["generated_at"],
            "count": len(cached_data["data"]),
            "message": "Data served from cache (fast!)",
            "data": cached_data["data"]
        })
    
    # Generate fresh data (slow - 1 second + processing)
    from django.utils import timezone
    data = generate_heavy_data(10000)
    generated_at = timezone.now().isoformat()
    
    # Store in cache for 5 minutes
    cache.set(HEAVY_CACHE_KEY, {
        "generated_at": generated_at,
        "data": data
    }, HEAVY_CACHE_TIMEOUT)
    
    elapsed = time.time() - start_time
    return Response({
        "cached": False,
        "cache_expires_in": HEAVY_CACHE_TIMEOUT,
        "response_time_ms": round(elapsed * 1000, 2),
        "generated_at": generated_at,
        "count": len(data),
        "message": "Data freshly generated (slow - 1s delay simulated)",
        "data": data
    })
