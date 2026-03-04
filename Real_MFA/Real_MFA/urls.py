"""
URL configuration for Real_MFA project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.db import connections
from django.core.cache import cache
from otp.urls import totp_urlpatterns


def health_check(request):
    checks = {
        'database': 'ok',
        'cache': 'ok',
    }
    status_code = 200

    try:
        with connections['default'].cursor() as cursor:
            cursor.execute('SELECT 1')
    except Exception:
        checks['database'] = 'error'
        status_code = 503

    try:
        cache.set('healthcheck', 'ok', timeout=10)
        if cache.get('healthcheck') != 'ok':
            raise RuntimeError('Cache validation failed')
    except Exception:
        checks['cache'] = 'error'
        status_code = 503

    return JsonResponse(
        {
            'status': 'ok' if status_code == 200 else 'degraded',
            'checks': checks,
        },
        status=status_code,
    )

urlpatterns = [
    path('healthz/', health_check),
    path('admin/', admin.site.urls),
    
    # Accounts: Login, Logout, Registration
    path('api/', include('accounts.urls')),
    
    # Profile: User profile and account management
    path('api/profile/', include('accounts.profile_urls')),
    
    # Password: Forgot/Reset password
    path('api/password/', include('accounts.password_urls')),
    
    # Devices: Device verification and management
    path('api/devices/', include('devices.urls')),
    
    # OTP: OTP resend
    path('api/otp/', include('otp.urls')),
    
    # TOTP/MFA: TOTP setup, verify, disable, backup codes
    path('api/totp/', include(totp_urlpatterns)),
    
    # Notifications: Email verification
    path('api/notifications/', include('notification.urls')),
    
    # Admin: Admin dashboard APIs
    path('api/admin-dashboard/', include('accounts.admin_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
