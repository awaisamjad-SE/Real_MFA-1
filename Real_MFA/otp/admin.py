from django.contrib import admin
from .models import OTP, TOTPDevice, BackupCode, MFAChallenge, EmailMFAMethod, SMSMFAMethod, MFARecovery


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'purpose', 'target', 'is_used', 'attempts', 'max_attempts', 'expires_at', 'created_at')
    list_filter = ('purpose', 'is_used', 'created_at', 'expires_at')
    search_fields = ('user__email', 'user__username', 'target', 'ip_address')
    readonly_fields = ('id', 'code_hash', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('OTP Info', {
            'fields': ('id', 'user', 'purpose', 'target', 'code_hash')
        }),
        ('Status', {
            'fields': ('is_used', 'used_at', 'attempts', 'max_attempts')
        }),
        ('Security', {
            'fields': ('expires_at', 'ip_address')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_add_permission(self, request):
        return False


@admin.register(TOTPDevice)
class TOTPDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_verified', 'verified_at', 'last_used_at', 'total_verifications', 'failed_attempts', 'created_at')
    list_filter = ('is_verified', 'verified_at', 'created_at')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('id', 'secret', 'backup_codes_generated_at', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('TOTP Info', {
            'fields': ('id', 'user', 'secret')
        }),
        ('Status', {
            'fields': ('is_verified', 'verified_at')
        }),
        ('Backup Codes', {
            'fields': ('backup_codes_generated_at',)
        }),
        ('Usage Stats', {
            'fields': ('last_used_at', 'total_verifications', 'failed_attempts')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_add_permission(self, request):
        return False


@admin.register(BackupCode)
class BackupCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_used', 'used_at', 'used_from_ip', 'created_at')
    list_filter = ('is_used', 'used_at', 'created_at')
    search_fields = ('user__email', 'user__username', 'used_from_ip')
    readonly_fields = ('id', 'code_hash', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Backup Code Info', {
            'fields': ('id', 'user', 'code_hash')
        }),
        ('Usage', {
            'fields': ('is_used', 'used_at', 'used_from_ip')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_add_permission(self, request):
        return False


@admin.register(MFAChallenge)
class MFAChallengeAdmin(admin.ModelAdmin):
    list_display = ('user', 'challenge_type', 'status', 'attempts', 'expires_at', 'created_at')
    list_filter = ('challenge_type', 'status', 'created_at')
    search_fields = ('user__email', 'user__username', 'session_id')
    readonly_fields = ('id', 'created_at', 'updated_at', 'verified_at', 'verified_device')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Challenge Info', {
            'fields': ('id', 'user', 'challenge_type', 'status')
        }),
        ('Session Context', {
            'fields': ('session_id', 'ip_address', 'user_agent')
        }),
        ('Verification', {
            'fields': ('attempts', 'max_attempts', 'verified_at', 'verified_device')
        }),
        ('Timing', {
            'fields': ('expires_at',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_add_permission(self, request):
        return False


@admin.register(EmailMFAMethod)
class EmailMFAMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'is_verified', 'is_enabled', 'last_used_at')
    list_filter = ('is_verified', 'is_enabled', 'created_at')
    search_fields = ('user__email', 'user__username', 'email')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Method Info', {
            'fields': ('id', 'user', 'email')
        }),
        ('Status', {
            'fields': ('is_verified', 'verified_at', 'is_enabled')
        }),
        ('Usage Stats', {
            'fields': ('last_used_at', 'total_verifications', 'failed_attempts')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(SMSMFAMethod)
class SMSMFAMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'is_verified', 'is_enabled', 'last_used_at')
    list_filter = ('is_verified', 'is_enabled', 'created_at')
    search_fields = ('user__email', 'user__username', 'phone_number')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Method Info', {
            'fields': ('id', 'user', 'phone_number')
        }),
        ('Status', {
            'fields': ('is_verified', 'verified_at', 'is_enabled')
        }),
        ('Usage Stats', {
            'fields': ('last_used_at', 'total_verifications', 'failed_attempts')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(MFARecovery)
class MFARecoveryAdmin(admin.ModelAdmin):
    list_display = ('user', 'recovery_type', 'is_successful', 'verified_at', 'created_at')
    list_filter = ('recovery_type', 'is_successful', 'created_at')
    search_fields = ('user__email', 'user__username', 'ip_address')
    readonly_fields = ('id', 'created_at', 'updated_at', 'verified_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Recovery Info', {
            'fields': ('id', 'user', 'recovery_type')
        }),
        ('Status', {
            'fields': ('is_successful', 'verified_at')
        }),
        ('Context', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_add_permission(self, request):
        return False

