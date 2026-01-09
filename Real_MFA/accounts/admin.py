from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, Profile, PasswordHistory


class ProfileInline(admin.StackedInline):
	model = Profile
	can_delete = False
	fk_name = 'user'
	extra = 0


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
	inlines = [ProfileInline]

	list_display = (
		'email',
		'username',
		'role',
		'email_verified',
		'mfa_enabled',
		'is_active',
		'is_staff',
		'is_deleted',
		'created_at',
	)
	list_filter = (
		'role',
		'email_verified',
		'mfa_enabled',
		'is_active',
		'is_staff',
		'is_superuser',
		'is_deleted',
		'created_at',
	)
	search_fields = ('email', 'username', 'first_name', 'last_name')
	ordering = ('email',)
	readonly_fields = ('id', 'created_at', 'updated_at', 'last_login', 'date_joined')

	fieldsets = (
		(None, {'fields': ('id', 'email', 'username', 'password')}),
		(_('Role & Status'), {'fields': ('role', 'is_active', 'is_deleted')}),
		(_('Verification & MFA'), {'fields': ('email_verified', 'email_verified_at', 'mfa_enabled', 'mfa_method')}),
		(_('Security'), {'fields': (
			'last_login_ip',
			'last_login_at',
			'failed_login_attempts',
			'account_locked_until',
			'password_changed_at',
			'require_password_change',
			'last_activity',
		)}),
		(_('Permissions'), {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
		(_('Personal info'), {'fields': ('first_name', 'last_name')}),
		(_('Important dates'), {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
	)

	add_fieldsets = (
		(None, {
			'classes': ('wide',),
			'fields': ('email', 'username', 'role', 'password1', 'password2'),
		}),
	)

	filter_horizontal = ('groups', 'user_permissions')

	def has_change_permission(self, request, obj=None):
		"""Prevent editing of admin role users (except themselves)"""
		if obj is not None and obj.role == 'admin':
			# Allow admin to edit their own account
			if request.user == obj:
				return True
			return False
		return super().has_change_permission(request, obj)

	def has_delete_permission(self, request, obj=None):
		"""Prevent deletion of admin role users"""
		if obj is not None and obj.role == 'admin':
			return False
		return super().has_delete_permission(request, obj)

	def delete_model(self, request, obj):
		"""Block single admin deletion"""
		if obj.role == 'admin':
			messages.error(request, f"Cannot delete admin user: {obj.email}")
			return
		super().delete_model(request, obj)

	def delete_queryset(self, request, queryset):
		"""Block bulk deletion of admin users"""
		admin_users = queryset.filter(role='admin')
		if admin_users.exists():
			admin_emails = ', '.join(admin_users.values_list('email', flat=True))
			messages.error(request, f"Cannot delete admin users: {admin_emails}")
			queryset = queryset.exclude(role='admin')
		super().delete_queryset(request, queryset)


@admin.register(PasswordHistory)
class PasswordHistoryAdmin(admin.ModelAdmin):
	list_display = ('user', 'created_at', 'changed_from_ip')
	list_filter = ('created_at',)
	search_fields = ('user__email', 'user__username')
	readonly_fields = ('user', 'password_hash', 'changed_from_ip', 'created_at', 'updated_at')

	def has_add_permission(self, request):
		return False

