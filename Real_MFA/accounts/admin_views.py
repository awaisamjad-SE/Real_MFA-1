"""
Admin Views - Comprehensive user management APIs for admin dashboard
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Count, Q
from django.utils import timezone

from .models import User
from .admin_serializers import AdminUserListSerializer, AdminUserDetailSerializer


class IsAdminOrManager(IsAuthenticated):
    """
    Permission class for admin or manager users
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.role in ['admin', 'manager']


class AdminUserListView(APIView):
    """
    Get all users with summary data
    
    GET /api/admin/users/
    
    Query Parameters:
    - role: Filter by role (admin, manager, user)
    - status: Filter by status (active, inactive, locked, deleted, unverified)
    - mfa: Filter by MFA status (enabled, disabled)
    - search: Search by email or username
    - ordering: Order by field (-created_at, email, last_login_at)
    - page: Page number
    - page_size: Items per page (default 20, max 100)
    
    Response (200):
    {
        "count": 150,
        "total_pages": 8,
        "current_page": 1,
        "page_size": 20,
        "summary": {
            "total_users": 150,
            "active_users": 140,
            "locked_users": 3,
            "mfa_enabled": 50,
            "unverified_emails": 10
        },
        "users": [...]
    }
    """
    permission_classes = [IsAuthenticated]
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'
    
    def get(self, request):
        # Start with all users
        queryset = User.objects.all()
        
        # Filter by role
        role = request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            if status_filter == 'active':
                queryset = queryset.filter(is_active=True, is_deleted=False, email_verified=True)
            elif status_filter == 'inactive':
                queryset = queryset.filter(is_active=False)
            elif status_filter == 'locked':
                queryset = queryset.filter(account_locked_until__gt=timezone.now())
            elif status_filter == 'deleted':
                queryset = queryset.filter(is_deleted=True)
            elif status_filter == 'unverified':
                queryset = queryset.filter(email_verified=False)
        
        # Filter by MFA status
        mfa = request.query_params.get('mfa')
        if mfa:
            if mfa == 'enabled':
                queryset = queryset.filter(mfa_enabled=True)
            elif mfa == 'disabled':
                queryset = queryset.filter(mfa_enabled=False)
        
        # Search
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        # Ordering
        ordering = request.query_params.get('ordering', '-created_at')
        valid_orderings = ['created_at', '-created_at', 'email', '-email', 
                          'last_login_at', '-last_login_at', 'username', '-username']
        if ordering in valid_orderings:
            queryset = queryset.order_by(ordering)
        
        # Get summary stats (before pagination)
        total_users = User.objects.count()
        summary = {
            'total_users': total_users,
            'active_users': User.objects.filter(is_active=True, is_deleted=False).count(),
            'locked_users': User.objects.filter(account_locked_until__gt=timezone.now()).count(),
            'mfa_enabled': User.objects.filter(mfa_enabled=True).count(),
            'unverified_emails': User.objects.filter(email_verified=False).count(),
            'deleted_users': User.objects.filter(is_deleted=True).count(),
        }
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 20)), 100)
        
        total_count = queryset.count()
        total_pages = (total_count + page_size - 1) // page_size
        
        start = (page - 1) * page_size
        end = start + page_size
        users = queryset[start:end]
        
        serializer = AdminUserListSerializer(users, many=True)
        
        return Response({
            'count': total_count,
            'total_pages': total_pages,
            'current_page': page,
            'page_size': page_size,
            'summary': summary,
            'users': serializer.data
        })


class AdminUserDetailView(APIView):
    """
    Get comprehensive details for a single user
    
    GET /api/admin/users/{user_id}/
    
    Response (200):
    {
        "id": "uuid",
        "email": "...",
        "username": "...",
        "profile": {...},
        "devices": [...],
        "sessions": [...],
        "otps": [...],
        "totp_device": {...},
        "backup_codes": [...],
        "email_notifications": [...],
        "sms_notifications": [...],
        "mfa_settings": {...},
        "password_history": [...],
        ...
    }
    """
    permission_classes = [IsAuthenticated]
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'
    
    def get(self, request, user_id):
        # Check permission
        if not self.has_permission(request, None):
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            user = User.objects.select_related(
                'profile', 'totp_device', 'mfa_settings'
            ).prefetch_related(
                'devices', 'sessions', 'otps', 'backup_codes',
                'email_notifications', 'sms_notifications', 'password_history'
            ).get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = AdminUserDetailSerializer(user)
        return Response(serializer.data)


class AdminUserStatsView(APIView):
    """
    Get overall system statistics
    
    GET /api/admin/stats/
    
    Response (200):
    {
        "users": {
            "total": 150,
            "active": 140,
            "by_role": {"admin": 5, "manager": 10, "user": 135}
        },
        "security": {
            "mfa_enabled": 50,
            "locked_accounts": 3,
            "compromised_devices": 1
        },
        "activity": {
            "active_sessions": 80,
            "logins_today": 45,
            "registrations_today": 5
        }
    }
    """
    permission_classes = [IsAuthenticated]
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'
    
    def get(self, request):
        # Check permission
        if not self.has_permission(request, None):
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from devices.models import Device, Session
        
        today = timezone.now().date()
        
        stats = {
            'users': {
                'total': User.objects.count(),
                'active': User.objects.filter(is_active=True, is_deleted=False).count(),
                'inactive': User.objects.filter(is_active=False).count(),
                'deleted': User.objects.filter(is_deleted=True).count(),
                'unverified': User.objects.filter(email_verified=False).count(),
                'by_role': {
                    'admin': User.objects.filter(role='admin').count(),
                    'manager': User.objects.filter(role='manager').count(),
                    'user': User.objects.filter(role='user').count(),
                }
            },
            'security': {
                'mfa_enabled': User.objects.filter(mfa_enabled=True).count(),
                'mfa_disabled': User.objects.filter(mfa_enabled=False).count(),
                'locked_accounts': User.objects.filter(
                    account_locked_until__gt=timezone.now()
                ).count(),
                'compromised_devices': Device.objects.filter(is_compromised=True).count(),
            },
            'devices': {
                'total': Device.objects.filter(is_deleted=False).count(),
                'verified': Device.objects.filter(is_verified=True, is_deleted=False).count(),
                'trusted': Device.objects.filter(is_trusted=True, is_deleted=False).count(),
            },
            'sessions': {
                'active': Session.objects.filter(is_active=True).count(),
                'revoked_today': Session.objects.filter(
                    revoked_at__date=today
                ).count(),
            },
            'activity': {
                'logins_today': Session.objects.filter(
                    created_at__date=today
                ).count(),
                'registrations_today': User.objects.filter(
                    created_at__date=today
                ).count(),
                'active_today': User.objects.filter(
                    last_activity__date=today
                ).count(),
            }
        }
        
        return Response(stats)


class AdminUserDeleteView(APIView):
    """
    Soft delete a user (marks as deleted, keeps data)
    Only admins can access this endpoint
    
    DELETE /api/admin/users/{user_id}/delete/
    
    Response (200):
    {
        "status": "success",
        "message": "User soft deleted successfully",
        "user_id": "uuid",
        "email": "user@example.com",
        "deleted_at": "2026-01-09T10:30:00Z"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def has_permission(self, request, view):
        # Only admins can delete users
        return request.user.is_authenticated and request.user.role == 'admin'
    
    def delete(self, request, user_id):
        # Check permission
        if not self.has_permission(request, None):
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Prevent self-deletion
        if str(request.user.id) == str(user_id):
            return Response(
                {'error': 'Cannot delete your own account'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if already deleted
        if user.is_deleted:
            return Response(
                {'error': 'User is already deleted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Soft delete the user
        user.soft_delete()
        
        # Deactivate account
        user.is_active = False
        user.save(update_fields=['is_active'])
        
        # Revoke all sessions
        from devices.models import Session
        Session.objects.filter(user=user, is_active=True).update(
            is_active=False,
            revoked_at=timezone.now(),
            revoked_reason='User deleted by admin'
        )
        
        # Log the action in audit logs
        from audits_logs.models import AuditLog
        AuditLog.objects.create(
            user=user,
            event_type='user_deleted',
            action='soft_delete',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={
                'deleted_by': str(request.user.id),
                'deleted_by_email': request.user.email,
                'reason': 'Admin action'
            }
        )
        
        return Response({
            'status': 'success',
            'message': 'User soft deleted successfully',
            'user_id': str(user.id),
            'email': user.email,
            'deleted_at': user.deleted_at.isoformat()
        })


class AdminUserRemoveView(APIView):
    """
    Permanently remove a user (hard delete - cannot be undone)
    Only admins can access this endpoint
    CAUTION: This permanently deletes all user data
    
    DELETE /api/admin/users/{user_id}/remove/
    
    Response (200):
    {
        "status": "success",
        "message": "User permanently removed",
        "user_id": "uuid",
        "email": "user@example.com"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def has_permission(self, request, view):
        # Only admins can permanently remove users
        return request.user.is_authenticated and request.user.role == 'admin'
    
    def delete(self, request, user_id):
        # Check permission
        if not self.has_permission(request, None):
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Prevent self-removal
        if str(request.user.id) == str(user_id):
            return Response(
                {'error': 'Cannot remove your own account'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Store info before deletion
        user_email = user.email
        user_id_str = str(user.id)
        
        # Log the action BEFORE deletion
        from audits_logs.models import AuditLog
        AuditLog.objects.create(
            user=None,  # User will be deleted
            event_type='user_permanently_removed',
            action='hard_delete',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={
                'removed_user_id': user_id_str,
                'removed_user_email': user_email,
                'removed_by': str(request.user.id),
                'removed_by_email': request.user.email,
                'reason': 'Admin action - permanent removal'
            }
        )
        
        # Permanently delete the user (CASCADE will delete related objects)
        user.delete()
        
        return Response({
            'status': 'success',
            'message': 'User permanently removed',
            'user_id': user_id_str,
            'email': user_email
        })


class AdminUserRestoreView(APIView):
    """
    Restore a soft-deleted user
    Only admins can access this endpoint
    
    POST /api/admin/users/{user_id}/restore/
    
    Response (200):
    {
        "status": "success",
        "message": "User restored successfully",
        "user_id": "uuid",
        "email": "user@example.com"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def has_permission(self, request, view):
        # Only admins can restore users
        return request.user.is_authenticated and request.user.role == 'admin'
    
    def post(self, request, user_id):
        # Check permission
        if not self.has_permission(request, None):
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user is deleted
        if not user.is_deleted:
            return Response(
                {'error': 'User is not deleted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Restore the user
        user.restore()
        
        # Reactivate account
        user.is_active = True
        user.save(update_fields=['is_active'])
        
        # Log the action
        from audits_logs.models import AuditLog
        AuditLog.objects.create(
            user=user,
            event_type='user_restored',
            action='restore',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={
                'restored_by': str(request.user.id),
                'restored_by_email': request.user.email,
                'reason': 'Admin action'
            }
        )
        
        return Response({
            'status': 'success',
            'message': 'User restored successfully',
            'user_id': str(user.id),
            'email': user.email
        })


# ============================================================================
# SEARCH API
# ============================================================================

class AdminSearchView(APIView):
    """
    Global search for users, devices, sessions, etc.
    
    GET /api/admin/search/?q=john&type=users
    
    Query Parameters:
    - q: Search query (required)
    - type: Filter by type (users, devices, sessions, all) - default: all
    - limit: Max results per type (default: 10)
    
    Response (200):
    {
        "query": "john",
        "results": {
            "users": [...],
            "devices": [...],
            "sessions": [...]
        },
        "total_count": 15
    }
    """
    permission_classes = [IsAuthenticated]
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'
    
    def get(self, request):
        # Check permission
        if not self.has_permission(request, None):
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        query = request.query_params.get('q', '').strip()
        search_type = request.query_params.get('type', 'all')
        limit = min(int(request.query_params.get('limit', 10)), 50)
        
        if not query:
            return Response(
                {'error': 'Search query required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = {}
        total_count = 0
        
        # Search users
        if search_type in ['all', 'users']:
            users = User.objects.filter(
                Q(email__icontains=query) |
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )[:limit]
            
            results['users'] = [{
                'id': str(user.id),
                'email': user.email,
                'username': user.username,
                'role': user.role,
                'is_active': user.is_active,
                'mfa_enabled': user.mfa_enabled
            } for user in users]
            total_count += len(results['users'])
        
        # Search devices
        if search_type in ['all', 'devices']:
            from devices.models import Device
            devices = Device.objects.filter(
                Q(device_name__icontains=query) |
                Q(ip_address__icontains=query) |
                Q(browser__icontains=query) |
                Q(os__icontains=query)
            ).select_related('user')[:limit]
            
            results['devices'] = [{
                'id': str(device.id),
                'device_name': device.device_name,
                'user_email': device.user.email,
                'ip_address': device.ip_address,
                'is_trusted': device.is_trusted
            } for device in devices]
            total_count += len(results['devices'])
        
        # Search sessions
        if search_type in ['all', 'sessions']:
            from devices.models import Session
            sessions = Session.objects.filter(
                Q(ip_address__icontains=query) |
                Q(device_name__icontains=query) |
                Q(user_agent__icontains=query)
            ).select_related('user')[:limit]
            
            results['sessions'] = [{
                'id': str(session.id),
                'user_email': session.user.email,
                'device_name': session.device_name,
                'ip_address': session.ip_address,
                'is_active': session.is_active
            } for session in sessions]
            total_count += len(results['sessions'])
        
        return Response({
            'query': query,
            'results': results,
            'total_count': total_count
        })


# ============================================================================
# MFA MANAGEMENT
# ============================================================================

class AdminUserMFADetailView(APIView):
    """
    Get comprehensive MFA details for a user
    
    GET /api/admin/users/{user_id}/mfa/
    
    Response (200):
    {
        "user_id": "uuid",
        "email": "user@example.com",
        "mfa_enabled": true,
        "mfa_method": "totp",
        "totp_device": {
            "id": "uuid",
            "name": "My Authenticator",
            "created_at": "2026-01-01T10:00:00Z",
            "last_used": "2026-01-09T08:30:00Z"
        },
        "backup_codes": {
            "total": 10,
            "used": 3,
            "remaining": 7
        },
        "trusted_devices": 5,
        "last_mfa_verification": "2026-01-09T08:30:00Z",
        "recovery_methods": ["email", "phone"]
    }
    """
    permission_classes = [IsAdminOrManager]
    
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        from otp.models import TOTPDevice, BackupCode
        from devices.models import Device
        
        # Get TOTP device
        totp_device = None
        try:
            totp = TOTPDevice.objects.get(user=user, is_verified=True)
            totp_device = {
                'id': str(totp.id),
                'name': totp.name,
                'created_at': totp.created_at.isoformat(),
                'last_used': totp.last_used_at.isoformat() if totp.last_used_at else None,
                'confirmed': totp.confirmed
            }
        except TOTPDevice.DoesNotExist:
            pass
        
        # Get backup codes stats
        backup_codes = BackupCode.objects.filter(user=user)
        backup_codes_used = backup_codes.filter(is_used=True).count()
        backup_codes_total = backup_codes.count()
        
        # Get trusted devices count
        trusted_devices = Device.objects.filter(
            user=user,
            is_trusted=True,
            is_deleted=False
        ).count()
        
        # Get last MFA verification
        from otp.models import MFAChallenge
        last_challenge = MFAChallenge.objects.filter(
            user=user,
            status='verified'
        ).order_by('-verified_at').first()
        
        return Response({
            'user_id': str(user.id),
            'email': user.email,
            'username': user.username,
            'mfa_enabled': user.mfa_enabled,
            'mfa_method': user.mfa_method if user.mfa_enabled else None,
            'totp_device': totp_device,
            'backup_codes': {
                'total': backup_codes_total,
                'used': backup_codes_used,
                'remaining': backup_codes_total - backup_codes_used
            },
            'trusted_devices': trusted_devices,
            'last_mfa_verification': last_challenge.verified_at.isoformat() if last_challenge else None
        })


class AdminResetUserMFAView(APIView):
    """
    Reset user's MFA completely (disable and clear all MFA data)
    
    POST /api/admin/users/{user_id}/mfa/reset/
    
    Body (optional):
    {
        "reason": "User lost authenticator app",
        "notify_user": true
    }
    
    Response (200):
    {
        "status": "success",
        "message": "MFA reset successfully",
        "user_id": "uuid",
        "actions_taken": [
            "Disabled MFA",
            "Deleted TOTP device",
            "Invalidated 7 backup codes",
            "Revoked 3 trusted devices"
        ]
    }
    """
    permission_classes = [IsAuthenticated]
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'
    
    def post(self, request, user_id):
        if not self.has_permission(request, None):
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        reason = request.data.get('reason', 'Admin reset')
        notify_user = request.data.get('notify_user', True)
        actions_taken = []
        
        # Disable MFA
        if user.mfa_enabled:
            user.mfa_enabled = False
            user.mfa_method = None
            user.save(update_fields=['mfa_enabled', 'mfa_method'])
            actions_taken.append('Disabled MFA')
        
        # Delete TOTP device
        from otp.models import TOTPDevice, BackupCode
        totp_deleted = TOTPDevice.objects.filter(user=user).delete()
        if totp_deleted[0] > 0:
            actions_taken.append(f'Deleted {totp_deleted[0]} TOTP device(s)')
        
        # Invalidate backup codes
        backup_codes = BackupCode.objects.filter(user=user, is_used=False)
        backup_count = backup_codes.count()
        if backup_count > 0:
            backup_codes.update(is_used=True)
            actions_taken.append(f'Invalidated {backup_count} backup codes')
        
        # Revoke trusted devices
        from devices.models import Device
        trusted_devices = Device.objects.filter(user=user, is_trusted=True)
        trusted_count = trusted_devices.count()
        if trusted_count > 0:
            trusted_devices.update(
                is_trusted=False,
                can_skip_mfa=False,
                trust_expires_at=None,
                mfa_skip_until=None
            )
            actions_taken.append(f'Revoked {trusted_count} trusted devices')
        
        # Log the action
        from audits_logs.models import AuditLog
        AuditLog.objects.create(
            user=user,
            event_type='mfa_reset_by_admin',
            action='mfa_reset',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={
                'reset_by': str(request.user.id),
                'reset_by_email': request.user.email,
                'reason': reason,
                'actions_taken': actions_taken
            }
        )
        
        # Send notification to user
        if notify_user:
            from notification.utils import send_security_alert
            send_security_alert(
                user,
                'mfa_disabled',
                {'reason': 'Reset by administrator', 'admin_email': request.user.email},
                request
            )
        
        return Response({
            'status': 'success',
            'message': 'MFA reset successfully',
            'user_id': str(user.id),
            'actions_taken': actions_taken
        })


class AdminForceEnableMFAView(APIView):
    """
    Force enable MFA for a user
    
    POST /api/admin/users/{user_id}/mfa/force-enable/
    
    Body:
    {
        "method": "totp",
        "reason": "Security policy requirement"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'
    
    def post(self, request, user_id):
        if not self.has_permission(request, None):
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        method = request.data.get('method', 'totp')
        reason = request.data.get('reason', 'Admin enforcement')
        
        if user.mfa_enabled:
            return Response(
                {'error': 'MFA is already enabled for this user'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Enable MFA
        user.mfa_enabled = True
        user.mfa_method = method
        user.require_password_change = True  # Force setup
        user.save(update_fields=['mfa_enabled', 'mfa_method', 'require_password_change'])
        
        # Log action
        from audits_logs.models import AuditLog
        AuditLog.objects.create(
            user=user,
            event_type='mfa_forced_enabled',
            action='mfa_force_enable',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={
                'enabled_by': str(request.user.id),
                'enabled_by_email': request.user.email,
                'method': method,
                'reason': reason
            }
        )
        
        return Response({
            'status': 'success',
            'message': 'MFA enabled successfully',
            'user_id': str(user.id),
            'method': method
        })


class AdminForceDisableMFAView(APIView):
    """
    Force disable MFA for a user
    
    POST /api/admin/users/{user_id}/mfa/force-disable/
    """
    permission_classes = [IsAuthenticated]
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'
    
    def post(self, request, user_id):
        if not self.has_permission(request, None):
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        reason = request.data.get('reason', 'Admin action')
        
        if not user.mfa_enabled:
            return Response(
                {'error': 'MFA is not enabled for this user'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Disable MFA
        user.mfa_enabled = False
        user.save(update_fields=['mfa_enabled'])
        
        # Log action
        from audits_logs.models import AuditLog
        AuditLog.objects.create(
            user=user,
            event_type='mfa_forced_disabled',
            action='mfa_force_disable',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={
                'disabled_by': str(request.user.id),
                'disabled_by_email': request.user.email,
                'reason': reason
            }
        )
        
        return Response({
            'status': 'success',
            'message': 'MFA disabled successfully',
            'user_id': str(user.id)
        })


class AdminGenerateEmergencyCodesView(APIView):
    """
    Generate emergency backup codes for a user
    
    POST /api/admin/users/{user_id}/mfa/emergency-codes/
    
    Response (200):
    {
        "status": "success",
        "user_id": "uuid",
        "codes": ["ABC123", "DEF456", ...],
        "message": "10 emergency codes generated"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'
    
    def post(self, request, user_id):
        if not self.has_permission(request, None):
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        from otp.models import BackupCode
        from otp.utils import generate_backup_code
        
        # Invalidate old codes
        BackupCode.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Generate new codes
        codes = []
        for _ in range(10):
            code = generate_backup_code()
            BackupCode.objects.create(user=user, code=code)
            codes.append(code)
        
        # Log action
        from audits_logs.models import AuditLog
        AuditLog.objects.create(
            user=user,
            event_type='emergency_codes_generated',
            action='generate_emergency_codes',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={
                'generated_by': str(request.user.id),
                'generated_by_email': request.user.email,
                'codes_count': len(codes)
            }
        )
        
        return Response({
            'status': 'success',
            'user_id': str(user.id),
            'codes': codes,
            'message': f'{len(codes)} emergency codes generated'
        })


class AdminRevokeTrustedDevicesView(APIView):
    """
    Revoke all trusted devices for a user
    
    POST /api/admin/users/{user_id}/mfa/revoke-devices/
    
    Response (200):
    {
        "status": "success",
        "devices_revoked": 5,
        "message": "All trusted devices revoked"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'
    
    def post(self, request, user_id):
        if not self.has_permission(request, None):
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        from devices.models import Device
        
        # Revoke all trusted devices
        devices = Device.objects.filter(user=user, is_trusted=True, is_deleted=False)
        count = devices.count()
        
        devices.update(
            is_trusted=False,
            can_skip_mfa=False,
            trust_expires_at=None,
            mfa_skip_until=None
        )
        
        # Log action
        from audits_logs.models import AuditLog
        AuditLog.objects.create(
            user=user,
            event_type='trusted_devices_revoked',
            action='revoke_trusted_devices',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={
                'revoked_by': str(request.user.id),
                'revoked_by_email': request.user.email,
                'devices_count': count
            }
        )
        
        return Response({
            'status': 'success',
            'devices_revoked': count,
            'message': f'{count} trusted device(s) revoked'
        })


class AdminMFAAuditHistoryView(APIView):
    """
    Get MFA audit history for a user
    
    GET /api/admin/users/{user_id}/mfa/audit-history/
    
    Response (200):
    {
        "user_id": "uuid",
        "events": [
            {
                "timestamp": "2026-01-09T10:00:00Z",
                "event_type": "mfa_enabled",
                "action": "User enabled MFA",
                "ip_address": "192.168.1.1",
                "details": {...}
            }
        ]
    }
    """
    permission_classes = [IsAuthenticated]
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'
    
    def get(self, request, user_id):
        # Check permission
        if not self.has_permission(request, None):
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        from audits_logs.models import AuditLog
        
        # Get MFA-related audit logs
        logs = AuditLog.objects.filter(
            user=user,
            event_type__in=[
                'mfa_enabled', 'mfa_disabled', 'mfa_reset_by_admin',
                'mfa_forced_enabled', 'mfa_forced_disabled',
                'emergency_codes_generated', 'trusted_devices_revoked',
                'mfa_challenge_failed', 'mfa_challenge_success'
            ]
        ).order_by('-timestamp')[:50]
        
        events = [{
            'id': str(log.id),
            'timestamp': log.timestamp.isoformat(),
            'event_type': log.event_type,
            'action': log.action,
            'ip_address': log.ip_address,
            'user_agent': log.user_agent,
            'metadata': log.metadata
        } for log in logs]
        
        return Response({
            'user_id': str(user.id),
            'total_events': len(events),
            'events': events
        })


class AdminMFAEmergencyBypassView(APIView):
    """
    Create temporary MFA bypass for emergency access
    
    POST /api/admin/users/{user_id}/mfa/emergency-bypass/
    
    Body:
    {
        "duration_hours": 24,
        "reason": "Emergency system access"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'
    
    def post(self, request, user_id):
        if not self.has_permission(request, None):
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        duration_hours = request.data.get('duration_hours', 24)
        reason = request.data.get('reason', 'Emergency bypass')
        
        # Create bypass by temporarily marking primary device as trusted
        from devices.models import Device
        bypass_until = timezone.now() + timezone.timedelta(hours=duration_hours)
        
        device = Device.objects.filter(user=user, is_deleted=False).first()
        if device:
            device.can_skip_mfa = True
            device.mfa_skip_until = bypass_until
            device.save(update_fields=['can_skip_mfa', 'mfa_skip_until'])
        
        # Log action
        from audits_logs.models import AuditLog
        AuditLog.objects.create(
            user=user,
            event_type='mfa_emergency_bypass',
            action='emergency_bypass',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={
                'bypass_by': str(request.user.id),
                'bypass_by_email': request.user.email,
                'duration_hours': duration_hours,
                'bypass_until': bypass_until.isoformat(),
                'reason': reason
            }
        )
        
        return Response({
            'status': 'success',
            'message': f'MFA bypass created for {duration_hours} hours',
            'user_id': str(user.id),
            'bypass_until': bypass_until.isoformat()
        })


class AdminMFAComplianceReportView(APIView):
    """
    Get MFA compliance report
    
    GET /api/admin/mfa/compliance-report/
    
    Query Parameters:
    - role: Filter by role
    - min_risk: Minimum risk level (high, medium, low)
    """
    permission_classes = [IsAuthenticated]
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'
    
    def get(self, request):
        # Check permission
        if not self.has_permission(request, None):
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        role_filter = request.query_params.get('role')
        
        queryset = User.objects.filter(is_active=True, is_deleted=False)
        if role_filter:
            queryset = queryset.filter(role=role_filter)
        
        total_users = queryset.count()
        mfa_enabled_count = queryset.filter(mfa_enabled=True).count()
        mfa_disabled_count = total_users - mfa_enabled_count
        
        compliance_rate = (mfa_enabled_count / total_users * 100) if total_users > 0 else 0
        
        # Identify high-risk users (admins/managers without MFA)
        high_risk_users = queryset.filter(
            role__in=['admin', 'manager'],
            mfa_enabled=False
        ).values('id', 'email', 'role', 'last_login_at')
        
        return Response({
            'total_users': total_users,
            'mfa_enabled': mfa_enabled_count,
            'mfa_disabled': mfa_disabled_count,
            'compliance_rate': f'{compliance_rate:.1f}%',
            'high_risk_users': list(high_risk_users),
            'by_role': {
                'admin': {
                    'total': queryset.filter(role='admin').count(),
                    'mfa_enabled': queryset.filter(role='admin', mfa_enabled=True).count()
                },
                'manager': {
                    'total': queryset.filter(role='manager').count(),
                    'mfa_enabled': queryset.filter(role='manager', mfa_enabled=True).count()
                },
                'user': {
                    'total': queryset.filter(role='user').count(),
                    'mfa_enabled': queryset.filter(role='user', mfa_enabled=True).count()
                }
            }
        })


class AdminBulkEnableMFAView(APIView):
    """
    Bulk enable MFA for multiple users
    
    POST /api/admin/mfa/bulk-enable/
    
    Body:
    {
        "user_ids": ["uuid1", "uuid2"],
        "method": "totp",
        "reason": "Security policy"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'
    
    def post(self, request):
        if not self.has_permission(request, None):
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_ids = request.data.get('user_ids', [])
        method = request.data.get('method', 'totp')
        reason = request.data.get('reason', 'Bulk enable by admin')
        
        if not user_ids:
            return Response(
                {'error': 'user_ids required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        users = User.objects.filter(id__in=user_ids, mfa_enabled=False)
        count = users.update(mfa_enabled=True, mfa_method=method)
        
        # Log action
        from audits_logs.models import AuditLog
        for user in users:
            AuditLog.objects.create(
                user=user,
                event_type='mfa_bulk_enabled',
                action='bulk_enable_mfa',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata={
                    'enabled_by': str(request.user.id),
                    'enabled_by_email': request.user.email,
                    'method': method,
                    'reason': reason
                }
            )
        
        return Response({
            'status': 'success',
            'users_updated': count,
            'message': f'MFA enabled for {count} users'
        })


class AdminBulkDisableMFAView(APIView):
    """
    Bulk disable MFA for multiple users
    
    POST /api/admin/mfa/bulk-disable/
    
    Body:
    {
        "user_ids": ["uuid1", "uuid2"],
        "reason": "Temporary disable"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'
    
    def post(self, request):
        if not self.has_permission(request, None):
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_ids = request.data.get('user_ids', [])
        reason = request.data.get('reason', 'Bulk disable by admin')
        
        if not user_ids:
            return Response(
                {'error': 'user_ids required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        users = User.objects.filter(id__in=user_ids, mfa_enabled=True)
        count = users.update(mfa_enabled=False)
        
        # Log action
        from audits_logs.models import AuditLog
        for user in users:
            AuditLog.objects.create(
                user=user,
                event_type='mfa_bulk_disabled',
                action='bulk_disable_mfa',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata={
                    'disabled_by': str(request.user.id),
                    'disabled_by_email': request.user.email,
                    'reason': reason
                }
            )
        
        return Response({
            'status': 'success',
            'users_updated': count,
            'message': f'MFA disabled for {count} users'
        })


class AdminMFAPolicyView(APIView):
    """
    Get or set MFA policy settings (stored in Django settings or database)
    
    GET /api/admin/mfa/policy/
    POST /api/admin/mfa/policy/
    
    Body (POST):
    {
        "require_for_roles": ["admin", "manager"],
        "allow_methods": ["totp", "email"],
        "backup_codes_required": true,
        "trusted_device_expiry_days": 30
    }
    """
    permission_classes = [IsAuthenticated]
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'
    
    def get(self, request):
        if not self.has_permission(request, None):
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Return current policy (could be from Django settings or database)
        policy = {
            'require_for_roles': ['admin', 'manager'],
            'allow_methods': ['totp', 'email', 'sms'],
            'backup_codes_required': True,
            'trusted_device_expiry_days': 30,
            'mfa_timeout_minutes': 15
        }
        
        return Response(policy)
    
    def post(self, request):
        if not self.has_permission(request, None):
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # In a real implementation, this would save to database
        # For now, just return the received policy
        policy = request.data
        
        # Log action
        from audits_logs.models import AuditLog
        AuditLog.objects.create(
            user=request.user,
            event_type='mfa_policy_updated',
            action='update_mfa_policy',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={
                'updated_by': str(request.user.id),
                'updated_by_email': request.user.email,
                'policy': policy
            }
        )
        
        return Response({
            'status': 'success',
            'message': 'MFA policy updated',
            'policy': policy
        })
