"""
Password URLs - Password management endpoints
"""

from django.urls import path
from .password_views import forgot_password, reset_password

urlpatterns = [
    # Forgot password - request reset
    path('forgot/', forgot_password, name='forgot-password'),
    
    # Reset password - complete reset
    path('reset/', reset_password, name='reset-password'),
]
