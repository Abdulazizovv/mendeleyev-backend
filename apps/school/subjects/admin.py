from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Subject, ClassSubject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'branch', 'is_active_badge', 'created_at')
    list_filter = ('branch', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'branch__name')
    autocomplete_fields = ('branch',)
    readonly_fields = ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
    list_per_page = 50
    
    fieldsets = (
        (_('Asosiy ma\'lumotlar'), {
            'fields': ('branch', 'name', 'code', 'description', 'is_active')
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


@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = ('class_obj', 'subject', 'teacher_display', 'hours_per_week', 'quarter', 'is_active_badge', 'created_at')
    list_filter = ('class_obj', 'subject', 'is_active', 'quarter', 'created_at')
    search_fields = ('class_obj__name', 'subject__name', 'teacher__user__phone_number', 'teacher__user__first_name')
    autocomplete_fields = ('class_obj', 'subject', 'teacher', 'quarter')
    readonly_fields = ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
    list_per_page = 50
    
    fieldsets = (
        (_('Asosiy ma\'lumotlar'), {
            'fields': ('class_obj', 'subject', 'teacher', 'hours_per_week', 'quarter', 'is_active')
        }),
        (_('Tizim ma\'lumotlari'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('class_obj', 'subject', 'teacher', 'teacher__user', 'quarter')
    
    @admin.display(description=_('O\'qituvchi'))
    def teacher_display(self, obj):
        if obj.teacher:
            user = obj.teacher.user
            return user.get_full_name() or user.phone_number
        return '-'
    
    @admin.display(description=_('Holati'), boolean=False)
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#090;">{}</span>', _('Faol'))
        return format_html('<span style="color:#999;">{}</span>', _('Nofaol'))

