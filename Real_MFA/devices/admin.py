from django.contrib import admin
from .models import Device, TrustedDevice, Session


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_name', 'device_type', 'browser', 'ip_address', 'is_verified', 'is_trusted', 'last_used_at')
    list_filter = ('device_type', 'is_verified', 'is_trusted', 'is_compromised', 'created_at')
    search_fields = ('user__email', 'user__username', 'device_name', 'ip_address', 'fingerprint_hash')
    readonly_fields = ('id', 'fingerprint_hash', 'created_at', 'updated_at', 'verified_at', 'first_used_at', 'last_used_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Device Info', {
            'fields': ('id', 'user', 'device_name', 'device_type', 'fingerprint_hash')
        }),
        ('Browser & OS', {
            'fields': ('browser', 'browser_version', 'os', 'os_version')
        }),
        ('Network & Location', {
            'fields': ('ip_address', 'last_ip', 'country', 'city', 'latitude', 'longitude')
        }),
        ('Trust & Verification', {
            'fields': ('is_verified', 'is_trusted', 'verified_at', 'trust_expires_at')
        }),
        ('Activity', {
            'fields': ('last_used_at', 'first_used_at', 'total_logins')
        }),
        ('Security', {
            'fields': ('is_compromised', 'risk_score', 'last_risk_assessment', 'can_skip_mfa', 'mfa_skip_until', 'security_notes')
        }),
        ('Soft Delete', {
            'fields': ('is_deleted', 'deleted_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['revoke_trust']
    
    def revoke_trust(self, request, queryset):
        for device in queryset:
            device.revoke_trust()
        self.message_user(request, f'{queryset.count()} device(s) trust revoked.')
    revoke_trust.short_description = 'Revoke trust for selected devices'
    
    def has_add_permission(self, request):
        return False


@admin.register(TrustedDevice)
class TrustedDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'device', 'device_name', 'trusted_at', 'is_trusted', 'expires_at')
    list_filter = ('is_trusted', 'created_at')
    search_fields = ('user__email', 'user__username', 'device__device_name', 'device_name')
    readonly_fields = ('id', 'created_at', 'updated_at', 'trusted_at', 'revoked_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Trust Info', {
            'fields': ('id', 'user', 'device', 'device_name', 'trust_days')
        }),
        ('Status', {
            'fields': ('is_trusted', 'trusted_at', 'expires_at')
        }),
        ('Activity', {
            'fields': ('last_verified_at', 'times_skipped_mfa')
        }),
        ('Revocation', {
            'fields': ('revoked_at', 'revocation_reason')
        }),
        ('Soft Delete', {
            'fields': ('is_deleted', 'deleted_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_add_permission(self, request):
        return False


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_name', 'ip_address', 'is_active', 'created_at', 'expires_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__email', 'user__username', 'ip_address', 'token_jti')
    readonly_fields = ('id', 'token_jti', 'fingerprint_hash', 'created_at', 'updated_at', 'last_activity')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Session Info', {
            'fields': ('id', 'user', 'token_jti', 'fingerprint_hash')
        }),
        ('Device Info', {
            'fields': ('device_name', 'device_type', 'browser', 'os')
        }),
        ('Network & Location', {
            'fields': ('ip_address', 'country', 'city', 'user_agent')
        }),
        ('Status', {
            'fields': ('is_active', 'expires_at', 'last_activity')
        }),
        ('Revocation', {
            'fields': ('revoked_at', 'revoked_reason')
        }),
        ('Soft Delete', {
            'fields': ('is_deleted', 'deleted_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['revoke_sessions']
    
    def revoke_sessions(self, request, queryset):
        for session in queryset:
            session.revoke(reason='admin_revoked')
        self.message_user(request, f'{queryset.count()} session(s) revoked.')
    revoke_sessions.short_description = 'Revoke selected sessions'
    
    def has_add_permission(self, request):
        return False
