from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Class, ClassStudent


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch', 'academic_year', 'grade_level', 'section', 'class_teacher_display', 'students_count', 'max_students', 'is_active_badge', 'created_at')
    list_filter = ('branch', 'academic_year', 'grade_level', 'is_active', 'created_at')
    search_fields = ('name', 'branch__name', 'academic_year__name', 'section')
    autocomplete_fields = ('branch', 'academic_year', 'class_teacher')
    readonly_fields = ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by', 'current_students_count_display')
    list_per_page = 50
    
    fieldsets = (
        (_('Asosiy ma\'lumotlar'), {
            'fields': ('branch', 'academic_year', 'name', 'grade_level', 'section', 'class_teacher', 'max_students', 'is_active')
        }),
        (_('Statistika'), {
            'fields': ('current_students_count_display',)
        }),
        (_('Tizim ma\'lumotlari'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('branch', 'academic_year', 'class_teacher', 'class_teacher__user').prefetch_related('class_students')
    
    @admin.display(description=_('O\'qituvchi'))
    def class_teacher_display(self, obj):
        if obj.class_teacher:
            user = obj.class_teacher.user
            return user.get_full_name() or user.phone_number
        return '-'
    
    @admin.display(description=_('O\'quvchilar'))
    def students_count(self, obj):
        count = obj.current_students_count
        max_count = obj.max_students
        color = '#090' if count < max_count else '#f00'
        return format_html(
            '<span style="color:{};">{}/{}</span>',
            color,
            count,
            max_count
        )
    
    @admin.display(description=_('Holati'), boolean=False)
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#090;">{}</span>', _('Faol'))
        return format_html('<span style="color:#999;">{}</span>', _('Nofaol'))
    
    @admin.display(description=_('Joriy o\'quvchilar soni'))
    def current_students_count_display(self, obj):
        return f"{obj.current_students_count} / {obj.max_students}"


@admin.register(ClassStudent)
class ClassStudentAdmin(admin.ModelAdmin):
    list_display = ('student_display', 'class_obj', 'enrollment_date', 'is_active_badge', 'created_at')
    list_filter = ('class_obj', 'is_active', 'enrollment_date', 'created_at')
    search_fields = ('membership__user__phone_number', 'membership__user__first_name', 'membership__user__last_name', 'class_obj__name')
    autocomplete_fields = ('class_obj', 'membership')
    readonly_fields = ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by', 'enrollment_date')
    date_hierarchy = 'enrollment_date'
    list_per_page = 50
    
    fieldsets = (
        (_('Asosiy ma\'lumotlar'), {
            'fields': ('class_obj', 'membership', 'enrollment_date', 'is_active', 'notes')
        }),
        (_('Tizim ma\'lumotlari'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('class_obj', 'membership', 'membership__user')
    
    @admin.display(description=_('O\'quvchi'))
    def student_display(self, obj):
        user = obj.membership.user
        return user.get_full_name() or user.phone_number
    
    @admin.display(description=_('Holati'), boolean=False)
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#090;">{}</span>', _('Faol'))
        return format_html('<span style="color:#999;">{}</span>', _('Nofaol'))

