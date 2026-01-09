"""
Accounts Validators - Reusable validation functions
"""

import re
import os
import requests
from django.core.exceptions import ValidationError

IPINFO_TOKEN = os.getenv('IPINFO_TOKEN', '7d863e1849ce97')


def validate_unique_username(value):
    """Check if username already exists"""
    from .models import User
    if User.objects.filter(username=value).exists():
        raise ValidationError("Username already taken.")
    return value


def validate_unique_email(value):
    """Check if email already exists"""
    from .models import User
    if User.objects.filter(email=value).exists():
        raise ValidationError("Email already registered.")
    return value


def validate_phone_format(value):
    """Validate phone number format"""
    if value and not re.match(r'^\+?1?\d{9,15}$', value):
        raise ValidationError("Phone must be 9-15 digits, optionally with + prefix.")
    return value


def validate_fingerprint(value):
    """Validate fingerprint hash"""
    if not value or len(value) < 10:
        raise ValidationError("Invalid device fingerprint hash.")
    return value


def get_ip_from_ipinfo():
    """Get client IP from ipinfo.io API"""
    try:
        response = requests.get(f'https://ipinfo.io?token={IPINFO_TOKEN}', timeout=5)
        if response.status_code == 200:
            return response.json().get('ip', '127.0.0.1')
    except Exception:
        pass
    return '127.0.0.1'


def get_location_from_ip(ip_address=None):
    """
    Get location data from IP address using ipinfo.io API
    
    Args:
        ip_address: IP address to lookup (if None, uses current request IP)
    
    Returns:
        dict: {
            'ip': '192.168.1.1',
            'country': 'US',
            'city': 'New York',
            'region': 'New York',
            'latitude': 40.7128,
            'longitude': -74.0060,
            'timezone': 'America/New_York',
            'org': 'ISP Name'
        }
    """
    try:
        if ip_address and ip_address not in ['127.0.0.1', 'localhost', '0.0.0.0', 'unknown']:
            url = f'https://ipinfo.io/{ip_address}?token={IPINFO_TOKEN}'
        else:
            url = f'https://ipinfo.io?token={IPINFO_TOKEN}'
        
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # Parse latitude and longitude from 'loc' field (format: "lat,lng")
            latitude = None
            longitude = None
            loc = data.get('loc', '')
            if loc and ',' in loc:
                try:
                    lat_str, lng_str = loc.split(',')
                    latitude = float(lat_str)
                    longitude = float(lng_str)
                except (ValueError, TypeError):
                    pass
            
            return {
                'ip': data.get('ip', ip_address or '127.0.0.1'),
                'country': data.get('country', ''),
                'city': data.get('city', ''),
                'region': data.get('region', ''),
                'latitude': latitude,
                'longitude': longitude,
                'timezone': data.get('timezone', ''),
                'org': data.get('org', '')
            }
    except Exception:
        pass
    
    # Return defaults if API fails
    return {
        'ip': ip_address or '127.0.0.1',
        'country': '',
        'city': '',
        'region': '',
        'latitude': None,
        'longitude': None,
        'timezone': '',
        'org': ''
    }
