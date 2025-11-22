from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import AcademicYear, Quarter


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch', 'start_date', 'end_date', 'is_active_badge', 'quarters_count', 'created_at')
    list_filter = ('branch', 'is_active', 'start_date', 'created_at')
    search_fields = ('name', 'branch__name')
    autocomplete_fields = ('branch',)
    readonly_fields = ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
    date_hierarchy = 'start_date'
    list_per_page = 50
    
    fieldsets = (
        (_('Asosiy ma\'lumotlar'), {
            'fields': ('branch', 'name', 'start_date', 'end_date', 'is_active')
        }),
        (_('Tizim ma\'lumotlari'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('quarters')
    
    @admin.display(description=_('Holati'), boolean=False)
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#090;">{}</span>', _('Faol'))
        return format_html('<span style="color:#999;">{}</span>', _('Nofaol'))
    
    @admin.display(description=_('Choraklar soni'))
    def quarters_count(self, obj):
        count = obj.quarters.count()
        return count


@admin.register(Quarter)
class QuarterAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year', 'number', 'start_date', 'end_date', 'is_active_badge', 'created_at')
    list_filter = ('academic_year', 'is_active', 'number', 'start_date')
    search_fields = ('name', 'academic_year__name', 'academic_year__branch__name')
    autocomplete_fields = ('academic_year',)
    readonly_fields = ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
    date_hierarchy = 'start_date'
    list_per_page = 50
    
    fieldsets = (
        (_('Asosiy ma\'lumotlar'), {
            'fields': ('academic_year', 'name', 'number', 'start_date', 'end_date', 'is_active')
        }),
        (_('Tizim ma\'lumotlari'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
        }),
    )
    
    @admin.display(description=_('Holati'), boolean=False)
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#090;">{}</span>', _('Faol'))
        return format_html('<span style="color:#999;">{}</span>', _('Nofaol'))

