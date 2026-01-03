from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Count
from .models import Homework, HomeworkSubmission


class HomeworkSubmissionInline(admin.TabularInline):
    """Inline for homework submissions."""
    model = HomeworkSubmission
    extra = 0
    fields = ('student', 'status', 'is_late', 'score', 'submitted_at', 'graded_at')
    readonly_fields = ('submitted_at', 'graded_at', 'is_late')
    autocomplete_fields = ('student',)


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'class_subject', 'assigned_date', 'due_date',
        'status_badge', 'submissions_count', 'completion_rate_display', 'created_at'
    )
    list_filter = (
        'status', 'assigned_date', 'due_date',
        'class_subject__class_obj', 'allow_late_submission'
    )
    search_fields = (
        'title', 'description',
        'class_subject__class_obj__name',
        'class_subject__subject__name'
    )
    autocomplete_fields = ('class_subject', 'lesson', 'assessment')
    readonly_fields = (
        'created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by'
    )
    date_hierarchy = 'due_date'
    list_per_page = 50
    ordering = ('-due_date', '-assigned_date')
    
    fieldsets = (
        (_('Vazifa ma\'lumotlari'), {
            'fields': (
                'class_subject', 'title', 'description',
                'assigned_date', 'due_date', 'allow_late_submission'
            )
        }),
        (_('Bog\'liq ma\'lumotlar'), {
            'fields': ('lesson', 'assessment', 'max_score'),
            'classes': ('collapse',)
        }),
        (_('Fayllar va holat'), {
            'fields': ('attachments', 'status')
        }),
        (_('Qo\'shimcha'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        (_('Tizim ma\'lumotlari'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
        }),
    )
    
    inlines = [HomeworkSubmissionInline]
    
    actions = ['close_homework', 'reopen_homework']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'class_subject__class_obj',
            'class_subject__subject',
            'lesson',
            'assessment'
        ).annotate(
            _submissions_count=Count('submissions', distinct=True)
        )
    
    @admin.display(description=_('Holat'))
    def status_badge(self, obj):
        colors = {
            'active': '#009900',
            'closed': '#cc6600',
            'archived': '#999999'
        }
        labels = {
            'active': 'Faol',
            'closed': 'Yopilgan',
            'archived': 'Arxivlangan'
        }
        color = colors.get(obj.status, '#999')
        label = labels.get(obj.status, obj.status)
        return format_html(
            '<span style="background-color:{}; color:white; padding:2px 8px; border-radius:3px;">{}</span>',
            color, label
        )
    
    @admin.display(description=_('Topshiriqlar'))
    def submissions_count(self, obj):
        count = getattr(obj, '_submissions_count', 0)
        graded = obj.get_graded_count()
        return f"{count} ({graded} baholangan)"
    
    @admin.display(description=_('Bajarilish %'))
    def completion_rate_display(self, obj):
        rate = obj.get_completion_rate()
        color = '#009900' if rate >= 80 else '#ff9900' if rate >= 50 else '#cc0000'
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}%</span>',
            color, rate
        )
    
    @admin.action(description=_('Tanlangan vazifalarni yopish'))
    def close_homework(self, request, queryset):
        from .models import HomeworkStatus
        updated = queryset.update(status=HomeworkStatus.CLOSED)
        self.message_user(request, _(f'{updated} ta vazifa yopildi'))
    
    @admin.action(description=_('Tanlangan vazifalarni qayta ochish'))
    def reopen_homework(self, request, queryset):
        from .models import HomeworkStatus
        updated = queryset.update(status=HomeworkStatus.ACTIVE)
        self.message_user(request, _(f'{updated} ta vazifa qayta ochildi'))


@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        'student_name', 'homework_title', 'submitted_at',
        'status_badge', 'is_late_badge', 'score', 'graded_at'
    )
    list_filter = (
        'status', 'is_late', 'submitted_at', 'graded_at',
        'homework__class_subject__class_obj'
    )
    search_fields = (
        'student__user_branch__user__first_name',
        'student__user_branch__user__last_name',
        'homework__title',
        'submission_text'
    )
    autocomplete_fields = ('homework', 'student')
    readonly_fields = (
        'submitted_at', 'graded_at', 'is_late',
        'created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by'
    )
    date_hierarchy = 'submitted_at'
    list_per_page = 100
    ordering = ('-submitted_at',)
    
    fieldsets = (
        (_('Topshiriq ma\'lumotlari'), {
            'fields': ('homework', 'student', 'status', 'is_late')
        }),
        (_('Topshirilgan javob'), {
            'fields': ('submission_text', 'attachments', 'submitted_at')
        }),
        (_('Baholash'), {
            'fields': ('score', 'teacher_feedback', 'graded_at')
        }),
        (_('Tizim ma\'lumotlari'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'homework__class_subject__class_obj',
            'homework__class_subject__subject',
            'student__user_branch__user'
        )
    
    @admin.display(description=_('O\'quvchi'))
    def student_name(self, obj):
        return obj.get_student_name()
    
    @admin.display(description=_('Vazifa'))
    def homework_title(self, obj):
        return obj.homework.title
    
    @admin.display(description=_('Holat'))
    def status_badge(self, obj):
        colors = {
            'not_submitted': '#999999',
            'submitted': '#0066cc',
            'late': '#ff9900',
            'graded': '#009900',
            'returned': '#cc0000'
        }
        labels = {
            'not_submitted': 'Topshirilmagan',
            'submitted': 'Topshirilgan',
            'late': 'Kechikkan',
            'graded': 'Baholangan',
            'returned': 'Qaytarilgan'
        }
        color = colors.get(obj.status, '#999')
        label = labels.get(obj.status, obj.status)
        return format_html(
            '<span style="background-color:{}; color:white; padding:2px 8px; border-radius:3px;">{}</span>',
            color, label
        )
    
    @admin.display(description=_('Kechikkan'), boolean=True)
    def is_late_badge(self, obj):
        return obj.is_late
