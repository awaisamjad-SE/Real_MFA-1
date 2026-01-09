from django.contrib import admin
from .models import (
    SessionAuditLog, DeviceAuditLog, SessionDeviceLinkAuditLog,
    MFAAuditLog, AuditLog, MFAChangeLog, AuditLogSummary
)


@admin.register(SessionAuditLog)
class SessionAuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'status', 'ip_address', 'created_at')
    list_filter = ('action', 'status', 'created_at')
    search_fields = ('user__email', 'user__username', 'ip_address', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Log Info', {
            'fields': ('id', 'user', 'changed_by', 'action', 'status')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Request Context', {
            'fields': ('ip_address', 'user_agent', 'referer')
        }),
        ('Metadata', {
            'fields': ('metadata',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DeviceAuditLog)
class DeviceAuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'status', 'ip_address', 'created_at')
    list_filter = ('action', 'status', 'created_at')
    search_fields = ('user__email', 'user__username', 'ip_address', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Log Info', {
            'fields': ('id', 'user', 'changed_by', 'action', 'status')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Request Context', {
            'fields': ('ip_address', 'user_agent', 'referer')
        }),
        ('Metadata', {
            'fields': ('metadata',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SessionDeviceLinkAuditLog)
class SessionDeviceLinkAuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'status', 'ip_address', 'created_at')
    list_filter = ('action', 'status', 'created_at')
    search_fields = ('user__email', 'user__username', 'ip_address', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Log Info', {
            'fields': ('id', 'user', 'changed_by', 'action', 'status')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Request Context', {
            'fields': ('ip_address', 'user_agent', 'referer')
        }),
        ('Metadata', {
            'fields': ('metadata',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(MFAAuditLog)
class MFAAuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'status', 'ip_address', 'created_at')
    list_filter = ('action', 'status', 'created_at')
    search_fields = ('user__email', 'user__username', 'ip_address', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Log Info', {
            'fields': ('id', 'user', 'changed_by', 'action', 'status')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Request Context', {
            'fields': ('ip_address', 'user_agent', 'referer')
        }),
        ('Metadata', {
            'fields': ('metadata',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'event_type', 'severity', 'ip_address', 'is_resolved', 'created_at')
    list_filter = ('event_type', 'severity', 'is_resolved', 'created_at')
    search_fields = ('user__email', 'user__username', 'description', 'ip_address')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Event Info', {
            'fields': ('id', 'user', 'event_type', 'severity')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Context', {
            'fields': ('ip_address', 'user_agent', 'device')
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolved_at', 'resolved_by')
        }),
        ('Metadata', {
            'fields': ('metadata',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['mark_resolved']
    
    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(is_resolved=False).update(
            is_resolved=True,
            resolved_at=timezone.now(),
            resolved_by=request.user
        )
        self.message_user(request, f'{updated} audit log(s) marked as resolved.')
    mark_resolved.short_description = 'Mark selected as resolved'
    
    def has_add_permission(self, request):
        return False


@admin.register(MFAChangeLog)
class MFAChangeLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'change_type', 'method', 'created_at')
    list_filter = ('change_type', 'method', 'created_at')
    search_fields = ('user__email', 'user__username', 'changed_by__email', 'ip_address')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Change Info', {
            'fields': ('id', 'user', 'change_type', 'method', 'description')
        }),
        ('Changed By', {
            'fields': ('changed_by',)
        }),
        ('Context', {
            'fields': ('ip_address', 'user_agent', 'reason')
        }),
        ('Old and New Values', {
            'fields': ('old_value', 'new_value')
        }),
        ('Approval', {
            'fields': ('requires_approval', 'is_approved')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AuditLogSummary)
class AuditLogSummaryAdmin(admin.ModelAdmin):
    list_display = ('user', 'summary_date', 'total_sessions_created', 'total_devices_registered', 'failed_mfa_attempts')
    list_filter = ('summary_date', 'created_at')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-summary_date',)
    date_hierarchy = 'summary_date'
    
    fieldsets = (
        ('Summary Info', {
            'fields': ('id', 'user', 'summary_date')
        }),
        ('Session Statistics', {
            'fields': ('total_sessions_created', 'total_sessions_terminated', 'total_sessions_revoked', 'concurrent_sessions_max')
        }),
        ('Device Statistics', {
            'fields': ('total_devices_registered', 'total_devices_verified', 'total_devices_trusted', 'total_devices_removed')
        }),
        ('Security Events', {
            'fields': ('failed_mfa_attempts', 'successful_mfa_verifications', 'suspicious_activities_detected', 'anomalous_devices_detected')
        }),
        ('Risk Statistics', {
            'fields': ('high_risk_events', 'critical_risk_events')
        }),
        ('Geographic Statistics', {
            'fields': ('unique_locations', 'unique_countries')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

