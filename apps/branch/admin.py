from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Branch, BranchStatuses, BranchTypes, BranchMembership, Role, SalaryType, BranchSettings
# Lazy import to avoid circular dependency
# AdminProfile will be imported inside methods if needed


class BranchSettingsInline(admin.StackedInline):
	"""Inline to display/edit BranchSettings on a branch page."""
	
	model = BranchSettings
	extra = 0
	can_delete = False
	fk_name = "branch"
	fieldsets = (
		(_('Dars jadvali sozlamalari'), {
			'fields': ('lesson_duration_minutes', 'break_duration_minutes', 'school_start_time', 'school_end_time')
		}),
		(_('Akademik sozlamalar'), {
			'fields': ('academic_year_start_month', 'academic_year_end_month')
		}),
		(_('Moliya sozlamalari'), {
			'fields': ('currency', 'currency_symbol')
		}),
		(_('Qo\'shimcha sozlamalar'), {
			'fields': ('additional_settings',),
			'classes': ('collapse',)
		}),
	)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
	list_display = (
		'name', 'slug', 'type', 'status', 'phone_number', 'email', 'created_at', 'updated_at', 'deleted_badge'
	)
	list_filter = (
		'type', 'status', 'created_at', 'updated_at'
	)
	search_fields = ('name', 'slug', 'address', 'phone_number', 'email')
	ordering = ('-created_at',)
	date_hierarchy = 'created_at'
	list_per_page = 50
	readonly_fields = ('created_at', 'updated_at', 'deleted_at')
	prepopulated_fields = {"slug": ("name",)}
	fieldsets = (
		(_('Asosiy ma\'lumotlar'), {
			'fields': ('name', 'slug', 'type', 'status')
		}),
		(_('Kontakt va manzil'), {
			'fields': ('address', 'phone_number', 'email')
		}),
		(_('Tizim ma\'lumotlari'), {
			'classes': ('collapse',),
			'fields': ('created_at', 'updated_at', 'deleted_at')
		}),
	)
	inlines = [BranchSettingsInline]

	actions = ('make_active', 'make_inactive', 'archive', 'restore_soft_deleted', 'hard_delete_selected')

	def get_queryset(self, request):
		# Include soft-deleted in admin list, so staff can restore
		qs = super().get_queryset(request)
		return qs

	@admin.display(description=_('Holati'), boolean=False)
	def deleted_badge(self, obj: Branch):
		if obj.deleted_at:
			return format_html('<span style="color:#d00;">{}</span>', _('O\'chirilgan'))
		return format_html('<span style="color:#090;">{}</span>', _('Faol (soft-delete emas)'))

	# Actions
	@admin.action(description=_('Tanlangan filiallarni FAOL qilish'))
	def make_active(self, request, queryset):
		updated = queryset.update(status=BranchStatuses.ACTIVE)
		self.message_user(request, _(f"{updated} ta filial FAOL qilindi"))

	@admin.action(description=_('Tanlangan filiallarni NOFAOL qilish'))
	def make_inactive(self, request, queryset):
		updated = queryset.update(status=BranchStatuses.INACTIVE)
		self.message_user(request, _(f"{updated} ta filial NOFAOL qilindi"))

	@admin.action(description=_('Tanlangan filiallarni ARXIVlash'))
	def archive(self, request, queryset):
		updated = queryset.update(status=BranchStatuses.ARCHIVED)
		self.message_user(request, _(f"{updated} ta filial ARXIVlandi"))

	@admin.action(description=_('Tanlanganlarini tiklash (soft-delete)'))
	def restore_soft_deleted(self, request, queryset):
		restored = 0
		for obj in queryset:
			if obj.deleted_at:
				obj.restore()
				restored += 1
		self.message_user(request, _(f"{restored} ta filial tiklandi"))

	@admin.action(description=_('Tanlanganlarini butunlay o\'chirish (hard delete)'))
	def hard_delete_selected(self, request, queryset):
		count = 0
		for obj in queryset:
			obj.hard_delete()
			count += 1
		self.message_user(request, _(f"{count} ta filial butunlay o\'chirildi"))


@admin.register(BranchSettings)
class BranchSettingsAdmin(admin.ModelAdmin):
	list_display = ('branch', 'lesson_duration_minutes', 'break_duration_minutes', 'school_start_time', 'school_end_time', 'currency', 'created_at')
	list_filter = ('currency', 'academic_year_start_month', 'academic_year_end_month')
	search_fields = ('branch__name', 'currency')
	autocomplete_fields = ('branch',)
	readonly_fields = ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
	
	fieldsets = (
		(_('Asosiy ma\'lumotlar'), {
			'fields': ('branch',)
		}),
		(_('Dars jadvali sozlamalari'), {
			'fields': ('lesson_duration_minutes', 'break_duration_minutes', 'school_start_time', 'school_end_time')
		}),
		(_('Akademik sozlamalar'), {
			'fields': ('academic_year_start_month', 'academic_year_end_month')
		}),
		(_('Moliya sozlamalari'), {
			'fields': ('currency', 'currency_symbol')
		}),
		(_('Qo\'shimcha sozlamalar'), {
			'fields': ('additional_settings',),
			'classes': ('collapse',)
		}),
		(_('Tizim ma\'lumotlari'), {
			'classes': ('collapse',),
			'fields': ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
		}),
	)


def get_admin_profile_inline():
	"""Factory function to create AdminProfileInline with lazy import.
	
	This avoids circular import issues between apps.branch and auth.profiles.
	"""
	from auth.profiles.models import AdminProfile
	
	class AdminProfileInline(admin.StackedInline):
		"""Inline to display/edit AdminProfile on a membership page.

		AdminProfile links to BranchMembership via OneToOneField.
		"""
		model = AdminProfile
		extra = 0
		can_delete = True
		fk_name = "user_branch"
		fields = ("is_super_admin", "managed_branches", "title", "notes")
		filter_horizontal = ("managed_branches",)
	
	return AdminProfileInline

# Create the inline class with lazy import
AdminProfileInline = get_admin_profile_inline()


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
	list_display = ("name", "branch", "is_active", "created_at")
	list_filter = ("is_active", "branch")
	search_fields = ("name", "description", "branch__name")
	autocomplete_fields = ("branch",)
	fieldsets = (
		(_('Asosiy ma\'lumotlar'), {
			'fields': ('name', 'branch', 'description', 'is_active')
		}),
		(_('Ruxsatlar'), {
			'fields': ('permissions',)
		}),
	)


@admin.register(BranchMembership)
class BranchMembershipAdmin(admin.ModelAdmin):
	list_display = ("user", "branch", "role", "role_ref", "title", "salary_type", "get_salary_display", "balance", "created_at")
	list_filter = ("role", "branch", "salary_type")
	search_fields = ("user__phone_number", "branch__name", "title")
	autocomplete_fields = ("user", "branch", "role_ref")
	fieldsets = (
		(_('Asosiy ma\'lumotlar'), {
			'fields': ('user', 'branch', 'role', 'role_ref', 'title')
		}),
		(_('Maosh konfiguratsiyasi'), {
			'fields': ('salary_type', 'monthly_salary', 'hourly_rate', 'per_lesson_rate'),
			'description': 'Maosh turiga qarab tegishli maydonni to\'ldiring.'
		}),
		(_('Moliya'), {
			'fields': ('balance',)
		}),
	)
	inlines = [AdminProfileInline]
	
	@admin.display(description='Maosh')
	def get_salary_display(self, obj):
		return obj.get_salary_display()

