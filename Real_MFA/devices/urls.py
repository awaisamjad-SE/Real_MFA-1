"""
Device URLs - Device and Session management endpoints
"""

from django.urls import path
from . import views

urlpatterns = [
    # Device list
    path('', views.DeviceListView.as_view(), name='device-list'),
    
    # Device verification
    path('verify/', views.verify_device, name='verify-device'),
    
    # Device revoke
    path('<uuid:device_id>/revoke/', views.DeviceRevokeView.as_view(), name='device-revoke'),
    
    # Session management
    path('sessions/', views.SessionListView.as_view(), name='session-list'),
    path('sessions/<uuid:session_id>/revoke/', views.SessionRevokeView.as_view(), name='session-revoke'),
    path('sessions/revoke-all/', views.RevokeAllSessionsView.as_view(), name='session-revoke-all'),
]