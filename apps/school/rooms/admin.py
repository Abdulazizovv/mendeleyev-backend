from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Building, Room


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch', 'floors', 'rooms_count', 'is_active_badge', 'created_at')
    list_filter = ('branch', 'is_active', 'created_at')
    search_fields = ('name', 'branch__name', 'address')
    autocomplete_fields = ('branch',)
    readonly_fields = ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
    list_per_page = 50
    
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
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#090;">{}</span>', _('Faol'))
        return format_html('<span style="color:#999;">{}</span>', _('Nofaol'))


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'building', 'room_type', 'floor', 'capacity', 'is_active_badge', 'created_at')
    list_filter = ('branch', 'building', 'room_type', 'is_active', 'floor', 'created_at')
    search_fields = ('name', 'building__name', 'branch__name')
    autocomplete_fields = ('branch', 'building')
    readonly_fields = ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
    list_per_page = 50
    
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
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#090;">{}</span>', _('Faol'))
        return format_html('<span style="color:#999;">{}</span>', _('Nofaol'))

