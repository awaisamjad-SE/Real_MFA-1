"""
Admin URLs - User management endpoints for admin dashboard
"""

from django.urls import path
from . import admin_views

urlpatterns = [
    # =========================================================================
    # Admin User Management
    # =========================================================================
    
    # Get all users (with filters, search, pagination)
    path('users/', admin_views.AdminUserListView.as_view(), name='admin-users-list'),
    
    # Get single user with all details
    path('users/<uuid:user_id>/', admin_views.AdminUserDetailView.as_view(), name='admin-user-detail'),
    
    # Get system statistics
    path('stats/', admin_views.AdminUserStatsView.as_view(), name='admin-stats'),
    
    # Delete user (soft delete)
    path('users/<uuid:user_id>/delete/', admin_views.AdminUserDeleteView.as_view(), name='admin-user-delete'),
    
    # Permanently remove user (hard delete)
    path('users/<uuid:user_id>/remove/', admin_views.AdminUserRemoveView.as_view(), name='admin-user-remove'),
    
    # Restore soft-deleted user
    path('users/<uuid:user_id>/restore/', admin_views.AdminUserRestoreView.as_view(), name='admin-user-restore'),
    
    # =========================================================================
    # Search
    # =========================================================================
    path('search/', admin_views.AdminSearchView.as_view(), name='admin-search'),
    
    # =========================================================================
    # MFA Management
    # =========================================================================
    
    # View user's MFA details
    path('users/<uuid:user_id>/mfa/', admin_views.AdminUserMFADetailView.as_view(), name='admin-user-mfa-detail'),
    
    # Reset user's MFA (disable and clear all MFA data)
    path('users/<uuid:user_id>/mfa/reset/', admin_views.AdminResetUserMFAView.as_view(), name='admin-reset-mfa'),
    
    # Force enable MFA for user
    path('users/<uuid:user_id>/mfa/force-enable/', admin_views.AdminForceEnableMFAView.as_view(), name='admin-force-enable-mfa'),
    
    # Force disable MFA for user
    path('users/<uuid:user_id>/mfa/force-disable/', admin_views.AdminForceDisableMFAView.as_view(), name='admin-force-disable-mfa'),
    
    # Generate emergency backup codes
    path('users/<uuid:user_id>/mfa/emergency-codes/', admin_views.AdminGenerateEmergencyCodesView.as_view(), name='admin-emergency-codes'),
    
    # Revoke all trusted devices
    path('users/<uuid:user_id>/mfa/revoke-devices/', admin_views.AdminRevokeTrustedDevicesView.as_view(), name='admin-revoke-devices'),
    
    # MFA audit history for user
    path('users/<uuid:user_id>/mfa/audit-history/', admin_views.AdminMFAAuditHistoryView.as_view(), name='admin-mfa-audit'),
    
    # MFA emergency bypass
    path('users/<uuid:user_id>/mfa/emergency-bypass/', admin_views.AdminMFAEmergencyBypassView.as_view(), name='admin-mfa-bypass'),
    
    # MFA compliance report
    path('mfa/compliance-report/', admin_views.AdminMFAComplianceReportView.as_view(), name='admin-mfa-compliance'),
    
    # Bulk MFA operations
    path('mfa/bulk-enable/', admin_views.AdminBulkEnableMFAView.as_view(), name='admin-bulk-enable-mfa'),
    path('mfa/bulk-disable/', admin_views.AdminBulkDisableMFAView.as_view(), name='admin-bulk-disable-mfa'),
    
    # MFA policy settings
    path('mfa/policy/', admin_views.AdminMFAPolicyView.as_view(), name='admin-mfa-policy'),
]
