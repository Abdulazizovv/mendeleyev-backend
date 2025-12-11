from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Building, Room


class SoftDeleteStatusFilter(admin.SimpleListFilter):
    title = _('O\'chirish holati')
    parameter_name = 'deleted_state'

    def lookups(self, request, model_admin):
        return (
            ('active', _('Faol (o\'chirilmagan)')),
            ('deleted', _('O\'chirilgan')),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'active':
            return queryset.filter(deleted_at__isnull=True)
        if value == 'deleted':
            return queryset.filter(deleted_at__isnull=False)
        return queryset


def restore_selected(modeladmin, request, queryset):
    restored = 0
    for obj in queryset:
        if getattr(obj, 'deleted_at', None):
            obj.restore()
            restored += 1
    if restored:
        modeladmin.message_user(
            request,
            _('%(count)d ta obyekt qayta tiklandi.') % {'count': restored},
            messages.SUCCESS,
        )
    else:
        modeladmin.message_user(
            request,
            _('Tanlangan obyektlar orasida o\'chirilganlari yo\'q.'),
            messages.INFO,
        )


restore_selected.short_description = _('Tanlangan obyektlarni tiklash')


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch', 'floors', 'rooms_count', 'state_badge', 'deleted_at', 'created_at')
    list_filter = ('branch', 'is_active', SoftDeleteStatusFilter, 'created_at')
    search_fields = ('name', 'branch__name', 'address')
    autocomplete_fields = ('branch',)
    readonly_fields = ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
    list_per_page = 50
    actions = ['delete_selected', restore_selected]
    
    fieldsets = (
        (_('Asosiy ma\'lumotlar'), {
            'fields': ('branch', 'name', 'address', 'floors', 'description', 'is_active')
        }),
        (_('Tizim ma\'lumotlari'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('rooms')
    
    @admin.display(description=_('Xonalar soni'))
    def rooms_count(self, obj):
        return obj.rooms.filter(deleted_at__isnull=True).count()
    
    @admin.display(description=_('Holati'), boolean=False)
    def state_badge(self, obj):
        if obj.deleted_at:
            return format_html('<span style="color:#d9534f;">{}</span>', _('O\'chirilgan'))
        if obj.is_active:
            return format_html('<span style="color:#090;">{}</span>', _('Faol'))
        return format_html('<span style="color:#999;">{}</span>', _('Nofaol'))


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'building', 'room_type', 'floor', 'capacity', 'state_badge', 'deleted_at', 'created_at')
    list_filter = ('branch', 'building', 'room_type', 'is_active', SoftDeleteStatusFilter, 'floor', 'created_at')
    search_fields = ('name', 'building__name', 'branch__name')
    autocomplete_fields = ('branch', 'building')
    readonly_fields = ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
    list_per_page = 50
    actions = ['delete_selected', restore_selected]
    
    fieldsets = (
        (_('Asosiy ma\'lumotlar'), {
            'fields': ('branch', 'building', 'name', 'room_type', 'floor', 'capacity', 'equipment', 'is_active')
        }),
        (_('Tizim ma\'lumotlari'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('building', 'branch')
    
    @admin.display(description=_('Holati'), boolean=False)
    def state_badge(self, obj):
        if obj.deleted_at:
            return format_html('<span style="color:#d9534f;">{}</span>', _('O\'chirilgan'))
        if obj.is_active:
            return format_html('<span style="color:#090;">{}</span>', _('Faol'))
        return format_html('<span style="color:#999;">{}</span>', _('Nofaol'))

