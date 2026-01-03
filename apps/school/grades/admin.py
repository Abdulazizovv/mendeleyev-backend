from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Avg
from .models import AssessmentType, Assessment, Grade, QuarterGrade


class GradeInline(admin.TabularInline):
    """Inline for grades within an assessment."""
    model = Grade
    extra = 0
    fields = ('student', 'score', 'calculated_score', 'final_score', 'override_reason', 'graded_at')
    readonly_fields = ('calculated_score', 'graded_at')
    autocomplete_fields = ('student',)


@admin.register(AssessmentType)
class AssessmentTypeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'code', 'branch', 'default_weight', 
        'is_active_badge', 'assessments_count', 'created_at'
    )
    list_filter = ('branch', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'branch__name', 'description')
    autocomplete_fields = ('branch',)
    readonly_fields = ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
    list_per_page = 50
    ordering = ('branch', 'code')
    
    fieldsets = (
        (_('Asosiy ma\'lumotlar'), {
            'fields': ('branch', 'name', 'code', 'default_max_score', 'default_weight', 'color', 'is_active')
        }),
        (_('Tavsif'), {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        (_('Tizim ma\'lumotlari'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('branch').annotate(
            _assessments_count=Count('assessments', distinct=True)
        )
    
    @admin.display(description=_('Faol'), boolean=True)
    def is_active_badge(self, obj):
        return obj.is_active
    
    @admin.display(description=_('Nazorat ishlari soni'))
    def assessments_count(self, obj):
        return getattr(obj, '_assessments_count', 0)


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'assessment_type', 'class_subject', 'date',
        'max_score', 'is_locked_badge', 'grades_count', 'average_score', 'created_at'
    )
    list_filter = (
        'assessment_type', 'is_locked', 'date', 
        'class_subject__class_obj', 'quarter', 'created_at'
    )
    search_fields = (
        'title', 'description', 
        'class_subject__class_obj__name',
        'class_subject__subject__name'
    )
    autocomplete_fields = ('class_subject', 'assessment_type', 'quarter', 'lesson')
    readonly_fields = (
        'is_locked', 'locked_at',
        'created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by'
    )
    date_hierarchy = 'date'
    list_per_page = 50
    ordering = ('-date', 'class_subject')
    
    fieldsets = (
        (_('Nazorat ishi ma\'lumotlari'), {
            'fields': (
                'class_subject', 'assessment_type', 'quarter',
                'title', 'description', 'date'
            )
        }),
        (_('Baholash'), {
            'fields': ('max_score', 'weight', 'lesson')
        }),
        (_('Qulflash'), {
            'fields': ('is_locked', 'locked_at'),
            'classes': ('collapse',)
        }),
        (_('Tizim ma\'lumotlari'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
        }),
    )
    
    inlines = [GradeInline]
    
    actions = ['lock_assessment', 'unlock_assessment']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'class_subject__class_obj',
            'class_subject__subject',
            'class_subject__teacher',
            'assessment_type',
            'quarter',
            'lesson'
        ).annotate(
            _grades_count=Count('grades', distinct=True),
            _avg_score=Avg('grades__final_score')
        )
    
    @admin.display(description=_('Qulflangan'), boolean=True)
    def is_locked_badge(self, obj):
        return obj.is_locked
    
    @admin.display(description=_('Baholar soni'))
    def grades_count(self, obj):
        return getattr(obj, '_grades_count', 0)
    
    @admin.display(description=_('O\'rtacha ball'))
    def average_score(self, obj):
        avg = getattr(obj, '_avg_score', None)
        if avg is not None:
            return f"{avg:.2f}"
        return "-"
    
    @admin.action(description=_('Tanlangan nazoratlarni qulflash'))
    def lock_assessment(self, request, queryset):
        count = 0
        for assessment in queryset.filter(is_locked=False):
            assessment.lock(locked_by=request.user)
            count += 1
        self.message_user(request, _(f'{count} ta nazorat qulflandi'))
    
    @admin.action(description=_('Tanlangan nazoratlarni ochish'))
    def unlock_assessment(self, request, queryset):
        count = 0
        for assessment in queryset.filter(is_locked=True):
            assessment.unlock()
            count += 1
        self.message_user(request, _(f'{count} ta nazorat ochildi'))


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = (
        'student_name', 'assessment', 'score', 'calculated_score',
        'final_score_display', 'has_override', 'graded_at'
    )
    list_filter = (
        'assessment__assessment_type', 'assessment__date',
        'assessment__class_subject__class_obj', 'graded_at'
    )
    search_fields = (
        'student__user_branch__user__first_name',
        'student__user_branch__user__last_name',
        'assessment__title',
        'assessment__class_subject__subject__name'
    )
    autocomplete_fields = ('assessment', 'student')
    readonly_fields = (
        'calculated_score', 'graded_at',
        'created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by'
    )
    list_per_page = 100
    ordering = ('-graded_at', 'assessment')
    date_hierarchy = 'graded_at'
    
    fieldsets = (
        (_('Baho ma\'lumotlari'), {
            'fields': ('assessment', 'student', 'score')
        }),
        (_('Hisoblangan va final baholar'), {
            'fields': ('calculated_score', 'final_score', 'override_reason')
        }),
        (_('Qo\'shimcha'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        (_('Tizim ma\'lumotlari'), {
            'classes': ('collapse',),
            'fields': ('graded_at', 'created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'assessment__class_subject__class_obj',
            'assessment__class_subject__subject',
            'assessment__assessment_type',
            'student__user_branch__user'
        )
    
    @admin.display(description=_('O\'quvchi'))
    def student_name(self, obj):
        return obj.get_student_name()
    
    @admin.display(description=_('Final ball'))
    def final_score_display(self, obj):
        if obj.final_score is not None and obj.final_score != obj.calculated_score:
            return format_html(
                '<span style="color:#cc6600; font-weight:bold;">{}</span> (o\'zgartirilgan)',
                obj.final_score
            )
        return obj.calculated_score or "-"
    
    @admin.display(description=_('Qo\'lda o\'zgartirilgan'), boolean=True)
    def has_override(self, obj):
        return obj.final_score is not None and obj.final_score != obj.calculated_score


@admin.register(QuarterGrade)
class QuarterGradeAdmin(admin.ModelAdmin):
    list_display = (
        'student_name', 'class_subject', 'quarter',
        'calculated_grade', 'final_grade', 'is_locked',
        'last_calculated'
    )
    list_filter = (
        'quarter', 'class_subject__class_obj',
        'class_subject__subject', 'is_locked', 'last_calculated'
    )
    search_fields = (
        'student__user_branch__user__first_name',
        'student__user_branch__user__last_name',
        'class_subject__class_obj__name',
        'class_subject__subject__name'
    )
    autocomplete_fields = ('student', 'class_subject', 'quarter')
    readonly_fields = (
        'calculated_grade', 'last_calculated', 'is_locked', 'locked_at',
        'created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by'
    )
    list_per_page = 100
    ordering = ('-last_calculated', 'class_subject', 'student')
    date_hierarchy = 'last_calculated'
    
    fieldsets = (
        (_('Chorak baho ma\'lumotlari'), {
            'fields': ('student', 'class_subject', 'quarter')
        }),
        (_('Hisoblangan ko\'rsatkichlar'), {
            'fields': (
                'calculated_grade', 'last_calculated'
            )
        }),
        (_('Final baho'), {
            'fields': ('final_grade', 'override_reason')
        }),
        (_('Qulflash'), {
            'fields': ('is_locked', 'locked_at'),
            'classes': ('collapse',)
        }),
        (_('Tizim ma\'lumotlari'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
        }),
    )
    
    actions = ['recalculate_grades']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'student__user_branch__user',
            'class_subject__class_obj',
            'class_subject__subject',
            'quarter'
        )
    
    @admin.display(description=_('O\'quvchi'))
    def student_name(self, obj):
        if obj.student and obj.student.user_branch:
            user = obj.student.user_branch.user
            return f"{user.first_name} {user.last_name}"
        return "Unknown"
    
    @admin.action(description=_('Tanlangan chorak baholarini qayta hisoblash'))
    def recalculate_grades(self, request, queryset):
        count = 0
        for quarter_grade in queryset:
            quarter_grade.calculate()
            count += 1
        self.message_user(request, _(f'{count} ta chorak baho qayta hisoblandi'))
