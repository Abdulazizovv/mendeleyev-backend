from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Branch, BranchStatuses, BranchTypes


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
	list_display = (
		'name', 'type', 'status', 'phone_number', 'email', 'created_at', 'updated_at', 'deleted_badge'
	)
	list_filter = (
		'type', 'status', 'created_at', 'updated_at'
	)
	search_fields = ('name', 'address', 'phone_number', 'email')
	ordering = ('-created_at',)
	date_hierarchy = 'created_at'
	list_per_page = 50
	readonly_fields = ('created_at', 'updated_at', 'deleted_at')
	fieldsets = (
		(_('Asosiy ma\'lumotlar'), {
			'fields': ('name', 'type', 'status')
		}),
		(_('Kontakt va manzil'), {
			'fields': ('address', 'phone_number', 'email')
		}),
		(_('Tizim ma\'lumotlari'), {
			'classes': ('collapse',),
			'fields': ('created_at', 'updated_at', 'deleted_at')
		}),
	)

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

