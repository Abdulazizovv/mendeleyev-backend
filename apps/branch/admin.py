from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    Branch, BranchStatuses, BranchTypes, BranchMembership, Role, SalaryType, 
    BranchSettings, BalanceTransaction, SalaryPayment, EmploymentType
)
from apps.branch.choices import TransactionType, PaymentMethod, PaymentStatus
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
			'fields': (
				'academic_year_start_month', 'academic_year_end_month',
				'working_days', 'holidays', 'daily_lesson_start_time', 
				'daily_lesson_end_time', 'max_lessons_per_day'
			)
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
		'name', 'code', 'slug', 'type', 'status', 'phone_number', 'email', 'created_at', 'updated_at', 'deleted_badge'
	)
	list_filter = (
		'type', 'status', 'created_at', 'updated_at'
	)
	search_fields = ('name', 'code', 'slug', 'address', 'phone_number', 'email')
	ordering = ('-created_at',)
	date_hierarchy = 'created_at'
	list_per_page = 50
	readonly_fields = ('created_at', 'updated_at', 'deleted_at')
	prepopulated_fields = {"slug": ("name",)}
	fieldsets = (
		(_('Asosiy ma\'lumotlar'), {
			'fields': ('name', 'code', 'slug', 'type', 'status')
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
	list_display = ("name", "code", "branch", "salary_range_display", "is_active", "memberships_count", "created_at")
	list_filter = ("is_active", "branch")
	search_fields = ("name", "code", "description", "branch__name")
	autocomplete_fields = ("branch",)
	readonly_fields = ("created_at", "updated_at", "memberships_count")
	
	fieldsets = (
		(_('Asosiy ma\'lumotlar'), {
			'fields': ('name', 'code', 'branch', 'description', 'is_active')
		}),
		(_('Maosh yo\'riqnomasi'), {
			'fields': ('salary_range_min', 'salary_range_max'),
			'description': 'Tavsiya etilgan maosh oralig\'i (optional)'
		}),
		(_('Ruxsatlar'), {
			'fields': ('permissions',)
		}),
		(_('Tizim ma\'lumotlari'), {
			'classes': ('collapse',),
			'fields': ('created_at', 'updated_at', 'memberships_count')
		}),
	)
	
	def get_queryset(self, request):
		return super().get_queryset(request).select_related('branch')
	
	@admin.display(description='Maosh oralig\'i')
	def salary_range_display(self, obj):
		if obj.salary_range_min and obj.salary_range_max:
			return format_html(
				'{} - {} so\'m',
				f"{obj.salary_range_min:_}",
				f"{obj.salary_range_max:_}"
			)
		return '-'
	
	@admin.display(description='Xodimlar soni')
	def memberships_count(self, obj):
		return obj.get_memberships_count()


@admin.register(BranchMembership)
class BranchMembershipAdmin(admin.ModelAdmin):
	list_display = (
		"user_display", "branch", "role_display", "role_ref", "title", 
		"salary_display", "balance_display", "employment_status", "created_at"
	)
	list_filter = ("role", "branch", "salary_type", "employment_type", "hire_date")
	search_fields = ("user__phone_number", "user__first_name", "user__last_name", "branch__name", "title")
	autocomplete_fields = ("user", "branch", "role_ref")
	readonly_fields = ("created_at", "updated_at", "deleted_at", "days_employed", "years_employed", "balance_status")
	
	fieldsets = (
		(_('Asosiy ma\'lumotlar'), {
			'fields': ('user', 'branch', 'role', 'role_ref', 'title')
		}),
		(_('Maosh konfiguratsiyasi'), {
			'fields': ('salary_type', 'monthly_salary', 'hourly_rate', 'per_lesson_rate'),
			'description': 'Maosh turiga qarab tegishli maydonni to\'ldiring.'
		}),
		(_('Moliya'), {
			'fields': ('balance', 'balance_status')
		}),
		(_('Ish ma\'lumotlari'), {
			'fields': ('hire_date', 'termination_date', 'employment_type', 'days_employed', 'years_employed')
		}),
		(_('Shaxsiy ma\'lumotlar'), {
			'fields': ('passport_serial', 'passport_number', 'address', 'emergency_contact'),
			'classes': ('collapse',)
		}),
		(_('Qo\'shimcha'), {
			'fields': ('notes',),
			'classes': ('collapse',)
		}),
		(_('Tizim ma\'lumotlari'), {
			'classes': ('collapse',),
			'fields': ('created_at', 'updated_at', 'deleted_at')
		}),
	)
	inlines = [AdminProfileInline]
	
	actions = ['soft_delete_selected', 'restore_soft_deleted', 'hard_delete_selected']
	
	def get_queryset(self, request):
		# Include soft-deleted in admin list, so staff can restore
		qs = super().get_queryset(request)
		return qs
	
	@admin.display(description='Xodim')
	def user_display(self, obj):
		name = obj.user.get_full_name() or obj.user.phone_number
		status = ''
		if obj.deleted_at:
			status = ' <span style="background:#d9534f;color:white;padding:2px 5px;border-radius:3px;font-size:10px;">O\'CHIRILGAN</span>'
		return format_html('<strong>{}</strong><br/><small>{}</small>{}', name, obj.user.phone_number, status)
	
	@admin.display(description='Rol')
	def role_display(self, obj):
		role_name = obj.get_role_display()
		if obj.role_ref:
			return format_html('{} <br/><small style="color:#666;">→ {}</small>', role_name, obj.role_ref.name)
		return role_name
	
	@admin.display(description='Maosh')
	def salary_display(self, obj):
		if obj.salary_type == 'monthly':
			return format_html('{} so\'m/oy', f"{obj.monthly_salary:_}")
		elif obj.salary_type == 'hourly':
			return format_html('{} so\'m/soat', f"{obj.hourly_rate or 0:_}")
		elif obj.salary_type == 'per_lesson':
			return format_html('{} so\'m/dars', f"{obj.per_lesson_rate or 0:_}")
		return '-'
	
	@admin.display(description='Balans')
	def balance_display(self, obj):
		color = '#090' if obj.balance >= 0 else '#d9534f'
		return format_html(
			'<span style="color:{};font-weight:bold;">{} so\'m</span>',
			color,
			f"{obj.balance:_}"
		)
	
	@admin.display(description='Ish holati')
	def employment_status(self, obj):
		if not obj.hire_date:
			return format_html('<span style="color:#999;">Ma\'lumot yo\'q</span>')
		
		if obj.deleted_at:
			return format_html(
				'<span style="color:#d9534f;font-weight:bold;">O\'chirilgan</span><br/>'
				'<small>Chiqish: {}</small>',
				obj.termination_date.strftime('%Y-%m-%d') if obj.termination_date else 'N/A'
			)
		
		if obj.termination_date:
			return format_html('<span style="color:#d9534f;">Ishdan chiqqan</span>')
		
		return format_html('<span style="color:#090;">Ishlamoqda</span>')
	
	# Actions
	@admin.action(description=_('Tanlanganlarni soft delete qilish (ishdan chiqarish)'))
	def soft_delete_selected(self, request, queryset):
		count = 0
		for obj in queryset.filter(deleted_at__isnull=True):
			obj.soft_delete(user=request.user)
			count += 1
		self.message_user(request, _(f"{count} ta xodim ishdan chiqarildi (soft delete)"))
	
	@admin.action(description=_('Tanlanganlarni tiklash (qayta ishga olish)'))
	def restore_soft_deleted(self, request, queryset):
		restored = 0
		for obj in queryset.filter(deleted_at__isnull=False):
			obj.restore()
			restored += 1
		self.message_user(request, _(f"{restored} ta xodim qayta ishga olindi"))
	
	@admin.action(description=_('Tanlanganlarni butunlay o\'chirish (hard delete)'))
	def hard_delete_selected(self, request, queryset):
		count = 0
		for obj in queryset:
			obj.hard_delete()
			count += 1
		self.message_user(request, _(f"{count} ta xodim butunlay o\'chirildi (hard delete)"))


@admin.register(BalanceTransaction)
class BalanceTransactionAdmin(admin.ModelAdmin):
	list_display = (
		"staff_display", "transaction_type_display", "amount_display", 
		"balance_change", "reference", "deleted_badge", "created_at"
	)
	list_filter = ("transaction_type", "created_at", "membership__branch")
	actions = ['restore_soft_deleted', 'hard_delete_selected']
	search_fields = (
		"membership__user__phone_number", "membership__user__first_name", 
		"membership__user__last_name", "reference", "description"
	)
	autocomplete_fields = ("membership", "salary_payment", "processed_by")
	readonly_fields = ("created_at", "updated_at", "previous_balance", "new_balance")
	date_hierarchy = "created_at"
	
	fieldsets = (
		(_('Asosiy ma\'lumotlar'), {
			'fields': ('membership', 'transaction_type', 'amount', 'description')
		}),
		(_('Balans ma\'lumotlari'), {
			'fields': ('previous_balance', 'new_balance')
		}),
		(_('Qo\'shimcha'), {
			'fields': ('reference', 'salary_payment', 'processed_by')
		}),
		(_('Tizim ma\'lumotlari'), {
			'classes': ('collapse',),
			'fields': ('created_at', 'updated_at')
		}),
	)
	
	def get_queryset(self, request):
		return super().get_queryset(request).select_related(
			'membership', 'membership__user', 'membership__branch', 'processed_by'
		)
	
	@admin.display(description='Xodim')
	def staff_display(self, obj):
		name = obj.membership.user.get_full_name() or obj.membership.user.phone_number
		return format_html('<strong>{}</strong><br/><small>{}</small>', name, obj.membership.branch.name)
	
	@admin.display(description='Holat', boolean=False)
	def deleted_badge(self, obj):
		if obj.deleted_at:
			return format_html('<span style="background:#d9534f;color:white;padding:2px 5px;border-radius:3px;">O\'CHIRILGAN</span>')
		return format_html('<span style="color:#090;">✓ Faol</span>')
	
	@admin.display(description='Tur')
	def transaction_type_display(self, obj):
		colors = {
			'salary': '#090',
			'bonus': '#0a0',
			'advance': '#fa0',
			'deduction': '#d00',
			'fine': '#c00',
			'adjustment': '#66f',
			'other': '#999'
		}
		color = colors.get(obj.transaction_type, '#000')
		return format_html(
			'<span style="color:{};">{}</span>',
			color,
			obj.get_transaction_type_display()
		)
	
	@admin.display(description='Summa')
	def amount_display(self, obj):
		return f"{obj.amount:_} so'm"
	
	@admin.display(description='Balans o\'zgarishi')
	def balance_change(self, obj):
		change = obj.new_balance - obj.previous_balance
		color = '#090' if change >= 0 else '#d9534f'
		sign = '+' if change >= 0 else ''
		return format_html(
			'<span style="color:{};">{}{}</span>',
			color,
			sign,
			f"{change:_}"
		)
	
	@admin.action(description=_('Tanlanganlarni tiklash'))
	def restore_soft_deleted(self, request, queryset):
		restored = 0
		for obj in queryset.filter(deleted_at__isnull=False):
			obj.restore()
			restored += 1
		self.message_user(request, _(f"{restored} ta tranzaksiya tiklandi"))
	
	@admin.action(description=_('Tanlanganlarni butunlay o\'chirish'))
	def hard_delete_selected(self, request, queryset):
		count = queryset.count()
		for obj in queryset:
			obj.hard_delete()
		self.message_user(request, _(f"{count} ta tranzaksiya butunlay o\'chirildi"))


@admin.register(SalaryPayment)
class SalaryPaymentAdmin(admin.ModelAdmin):
	list_display = (
		"staff_display", "month", "amount_display", "payment_date", 
		"payment_method_display", "status_badge", "deleted_badge", "created_at"
	)
	list_filter = ("status", "payment_method", "payment_date", "membership__branch")
	actions = ['restore_soft_deleted', 'hard_delete_selected']
	search_fields = (
		"membership__user__phone_number", "membership__user__first_name",
		"membership__user__last_name", "reference_number", "notes"
	)
	autocomplete_fields = ("membership", "processed_by")
	readonly_fields = ("created_at", "updated_at")
	date_hierarchy = "payment_date"
	
	fieldsets = (
		(_('Asosiy ma\'lumotlar'), {
			'fields': ('membership', 'month', 'amount', 'payment_date')
		}),
		(_('To\'lov ma\'lumotlari'), {
			'fields': ('payment_method', 'status', 'reference_number')
		}),
		(_('Qo\'shimcha'), {
			'fields': ('notes', 'processed_by')
		}),
		(_('Tizim ma\'lumotlari'), {
			'classes': ('collapse',),
			'fields': ('created_at', 'updated_at')
		}),
	)
	
	def get_queryset(self, request):
		return super().get_queryset(request).select_related(
			'membership', 'membership__user', 'membership__branch', 'processed_by'
		)
	
	@admin.display(description='Xodim')
	def staff_display(self, obj):
		name = obj.membership.user.get_full_name() or obj.membership.user.phone_number
		return format_html('<strong>{}</strong><br/><small>{}</small>', name, obj.membership.branch.name)
	
	@admin.display(description='Summa')
	def amount_display(self, obj):
		return f"{obj.amount:_} so'm"
	
	@admin.display(description='To\'lov usuli')
	def payment_method_display(self, obj):
		return obj.get_payment_method_display()
	
	@admin.display(description='Holat')
	def status_badge(self, obj):
		colors = {
			'pending': '#fa0',
			'paid': '#090',
			'cancelled': '#999',
			'failed': '#d00'
		}
		color = colors.get(obj.status, '#000')
		return format_html(
			'<span style="padding:3px 8px;background:{};color:#fff;border-radius:3px;font-size:11px;">{}</span>',
			color,
			obj.get_status_display()
		)
	
	@admin.display(description='Deleted', boolean=False)
	def deleted_badge(self, obj):
		if obj.deleted_at:
			return format_html('<span style="background:#d9534f;color:white;padding:2px 5px;border-radius:3px;">O\'CHIRILGAN</span>')
		return format_html('<span style="color:#090;">✓ Faol</span>')
	
	@admin.action(description=_('Tanlanganlarni tiklash'))
	def restore_soft_deleted(self, request, queryset):
		restored = 0
		for obj in queryset.filter(deleted_at__isnull=False):
			obj.restore()
			restored += 1
		self.message_user(request, _(f"{restored} ta to'lov tiklandi"))
	
	@admin.action(description=_('Tanlanganlarni butunlay o\'chirish'))
	def hard_delete_selected(self, request, queryset):
		count = queryset.count()
		for obj in queryset:
			obj.hard_delete()
		self.message_user(request, _(f"{count} ta to'lov butunlay o\'chirildi"))


