from django.contrib import admin
from .models import (
    EmailNotification, SMSNotification, NotificationPreference, 
    DetailedNotificationPreference, QuietHours, NotificationBlocklist,
    NotificationConsent, NotificationLog, MFANotification
)


@admin.register(EmailNotification)
class EmailNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'to_email', 'subject', 'email_type', 'status', 'sent_at')
    list_filter = ('email_type', 'status', 'created_at')
    search_fields = ('user__email', 'user__username', 'to_email', 'subject')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Email Info', {
            'fields': ('id', 'user', 'to_email', 'subject', 'email_type', 'template_name')
        }),
        ('Content', {
            'fields': ('body',)
        }),
        ('Status', {
            'fields': ('status', 'sent_at')
        }),
        ('Tracking', {
            'fields': ('opened_at', 'clicked_at', 'click_url')
        }),
        ('Error Handling', {
            'fields': ('error_message', 'retry_count', 'max_retries')
        }),
        ('Provider', {
            'fields': ('provider', 'provider_message_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['mark_as_sent', 'retry_failed']
    
    def mark_as_sent(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='sent', sent_at=timezone.now())
        self.message_user(request, f'{updated} notification(s) marked as sent.')
    mark_as_sent.short_description = 'Mark selected as sent'
    
    def retry_failed(self, request, queryset):
        updated = queryset.filter(status='failed').update(status='pending', error_message='')
        self.message_user(request, f'{updated} notification(s) queued for retry.')
    retry_failed.short_description = 'Retry failed notifications'


@admin.register(SMSNotification)
class SMSNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'sms_type', 'status', 'sent_at')
    list_filter = ('sms_type', 'status', 'created_at')
    search_fields = ('user__email', 'user__username', 'phone_number')
    readonly_fields = ('id', 'provider_message_id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('SMS Info', {
            'fields': ('id', 'user', 'phone_number', 'sms_type')
        }),
        ('Content', {
            'fields': ('message',)
        }),
        ('Status', {
            'fields': ('status', 'sent_at', 'delivered_at')
        }),
        ('Provider', {
            'fields': ('provider', 'provider_message_id', 'cost')
        }),
        ('Error Handling', {
            'fields': ('error_message', 'error_code', 'retry_count', 'max_retries')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_otp', 'email_alerts', 'sms_otp', 'sms_alerts', 'push_enabled')
    list_filter = ('email_otp', 'email_alerts', 'sms_otp', 'sms_alerts', 'push_enabled')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('User', {
            'fields': ('id', 'user')
        }),
        ('Email Preferences', {
            'fields': ('email_otp', 'email_alerts', 'email_marketing')
        }),
        ('SMS Preferences', {
            'fields': ('sms_otp', 'sms_alerts')
        }),
        ('Other Channels', {
            'fields': ('push_enabled',)
        }),
        ('Quiet Hours', {
            'fields': ('quiet_hours_enabled', 'quiet_start', 'quiet_end')
        }),
        ('Frequency', {
            'fields': ('digest_frequency',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(DetailedNotificationPreference)
class DetailedNotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'email_enabled', 'sms_enabled', 'push_enabled', 'in_app_enabled')
    list_filter = ('notification_type', 'email_enabled', 'sms_enabled', 'push_enabled', 'in_app_enabled', 'created_at')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('User & Type', {
            'fields': ('id', 'user', 'notification_type')
        }),
        ('Channel Preferences', {
            'fields': ('email_enabled', 'sms_enabled', 'in_app_enabled', 'push_enabled')
        }),
        ('Priority & Timing', {
            'fields': ('priority', 'respect_quiet_hours', 'delay_minutes')
        }),
        ('Frequency Cap', {
            'fields': ('max_per_day',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(QuietHours)
class QuietHoursAdmin(admin.ModelAdmin):
    list_display = ('user', 'day_of_week', 'start_time', 'end_time', 'is_enabled', 'allow_critical_only')
    list_filter = ('is_enabled', 'allow_critical_only', 'day_of_week')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Schedule Info', {
            'fields': ('id', 'user', 'day_of_week', 'description')
        }),
        ('Time Range', {
            'fields': ('start_time', 'end_time', 'timezone')
        }),
        ('Configuration', {
            'fields': ('is_enabled', 'allow_critical_only')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(NotificationBlocklist)
class NotificationBlocklistAdmin(admin.ModelAdmin):
    list_display = ('user', 'block_type', 'blocked_value', 'is_active', 'blocked_at')
    list_filter = ('block_type', 'is_active', 'created_at')
    search_fields = ('user__email', 'user__username', 'blocked_value', 'reason')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-blocked_at',)
    date_hierarchy = 'blocked_at'
    
    fieldsets = (
        ('Block Info', {
            'fields': ('id', 'user', 'block_type', 'blocked_value', 'reason')
        }),
        ('Status', {
            'fields': ('is_active', 'blocked_at', 'unblocked_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(NotificationConsent)
class NotificationConsentAdmin(admin.ModelAdmin):
    list_display = ('user', 'consent_type', 'is_consented', 'consented_at', 'withdrawn_at', 'source')
    list_filter = ('consent_type', 'is_consented', 'source', 'created_at')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Consent Info', {
            'fields': ('id', 'user', 'consent_type', 'source')
        }),
        ('Consent Status', {
            'fields': ('is_consented', 'consented_at', 'withdrawn_at')
        }),
        ('Tracking', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'channel', 'subject', 'delivered', 'created_at')
    list_filter = ('channel', 'delivered', 'created_at')
    search_fields = ('user__email', 'user__username', 'recipient', 'subject')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Log Info', {
            'fields': ('id', 'user', 'channel', 'recipient')
        }),
        ('Content', {
            'fields': ('subject', 'message')
        }),
        ('Status', {
            'fields': ('delivered',)
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


@admin.register(MFANotification)
class MFANotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'mfa_type', 'delivery_method', 'is_sent', 'is_verified', 'created_at')
    list_filter = ('mfa_type', 'delivery_method', 'is_sent', 'is_verified')
    search_fields = ('user__email', 'user__username', 'recipient')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Notification Info', {
            'fields': ('id', 'user', 'mfa_type', 'delivery_method')
        }),
        ('Recipient', {
            'fields': ('recipient',)
        }),
        ('Message', {
            'fields': ('subject', 'message')
        }),
        ('OTP Details', {
            'fields': ('otp_code_hash', 'code_length', 'expires_at')
        }),
        ('Delivery Status', {
            'fields': ('is_sent', 'sent_at', 'is_delivered', 'delivered_at')
        }),
        ('Verification', {
            'fields': ('is_verified', 'verified_at', 'verification_attempts', 'max_attempts')
        }),
        ('Error & Provider', {
            'fields': ('error_message', 'retry_count', 'provider', 'provider_message_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_add_permission(self, request):
        return False
