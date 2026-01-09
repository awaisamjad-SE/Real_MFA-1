"""
Accounts URLs - Authentication and Registration endpoints

Email verification moved to: /api/notifications/
Device verification moved to: /api/devices/
OTP resend moved to: /api/otp/
"""

from django.urls import path
from . import views
from . import auth_views

urlpatterns = [
    # =========================================================================
    # Authentication endpoints
    # =========================================================================
    path('auth/login/', auth_views.login, name='login'),
    path('auth/logout/', auth_views.logout, name='logout'),
    path('auth/verify-mfa/', auth_views.verify_mfa_login, name='verify-mfa-login'),
    
    # =========================================================================
    # Registration endpoints
    # =========================================================================
    path('auth/register/', views.register, name='register'),
    
    # =========================================================================
    # Demo APIs with caching
    # =========================================================================
    path('demo/pakistani-names/', views.demo_pakistani_names, name='demo-pakistani-names'),
    path('demo/heavy-data/', views.demo_heavy_data, name='demo-heavy-data'),
]