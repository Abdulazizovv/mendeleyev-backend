from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Count
from .models import LessonAttendance, StudentAttendanceRecord, AttendanceStatistics


class StudentAttendanceRecordInline(admin.TabularInline):
    """Inline for individual student attendance records."""
    model = StudentAttendanceRecord
    extra = 0
    fields = ('student', 'status', 'notes', 'marked_at')
    readonly_fields = ('marked_at',)
    autocomplete_fields = ('student',)


@admin.register(LessonAttendance)
class LessonAttendanceAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'lesson_number', 'class_subject', 'lesson',
        'is_locked_badge', 'records_count', 'present_count', 'created_at'
    )
    list_filter = (
        'is_locked', 'date', 'lesson_number', 
        'class_subject__class_obj', 'created_at'
    )
    search_fields = (
        'class_subject__class_obj__name', 
        'class_subject__subject__name',
        'notes'
    )
    autocomplete_fields = ('class_subject', 'lesson', 'locked_by')
    readonly_fields = (
        'is_locked', 'locked_at', 'locked_by',
        'created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by'
    )
    date_hierarchy = 'date'
    list_per_page = 50
    ordering = ('-date', 'lesson_number')
    
    fieldsets = (
        (_('Dars ma\'lumotlari'), {
            'fields': ('class_subject', 'lesson', 'date', 'lesson_number')
        }),
        (_('Qulflash'), {
            'fields': ('is_locked', 'locked_at', 'locked_by'),
            'classes': ('collapse',)
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
    
    inlines = [StudentAttendanceRecordInline]
    
    actions = ['lock_attendance', 'unlock_attendance']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'class_subject__class_obj', 
            'class_subject__subject',
            'lesson', 'locked_by'
        ).annotate(
            _records_count=Count('records', distinct=True)
        )
    
    @admin.display(description=_('Qulflangan'), boolean=True)
    def is_locked_badge(self, obj):
        return obj.is_locked
    
    @admin.display(description=_('Yozuvlar soni'))
    def records_count(self, obj):
        return getattr(obj, '_records_count', obj.records.count())
    
    @admin.display(description=_('Ishtirok etganlar'))
    def present_count(self, obj):
        return obj.get_present_count()
    
    @admin.action(description=_('Tanlangan davomat yozuvlarini qulflash'))
    def lock_attendance(self, request, queryset):
        count = 0
        for attendance in queryset.filter(is_locked=False):
            attendance.lock(locked_by=request.user)
            count += 1
        self.message_user(request, _(f'{count} ta davomat yozuvi qulflandi'))
    
    @admin.action(description=_('Tanlangan davomat yozuvlarini ochish'))
    def unlock_attendance(self, request, queryset):
        count = 0
        for attendance in queryset.filter(is_locked=True):
            attendance.unlock()
            count += 1
        self.message_user(request, _(f'{count} ta davomat yozuvi ochildi'))


@admin.register(StudentAttendanceRecord)
class StudentAttendanceRecordAdmin(admin.ModelAdmin):
    list_display = (
        'student_name', 'attendance', 'status_badge', 'marked_at'
    )
    list_filter = (
        'status', 'marked_at', 'attendance__date',
        'attendance__class_subject__class_obj'
    )
    search_fields = (
        'student__user_branch__user__first_name',
        'student__user_branch__user__last_name',
        'attendance__class_subject__class_obj__name',
        'notes'
    )
    autocomplete_fields = ('attendance', 'student')
    readonly_fields = ('marked_at', 'created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
    list_per_page = 100
    ordering = ('-marked_at',)
    date_hierarchy = 'marked_at'
    
    fieldsets = (
        (_('Davomat ma\'lumotlari'), {
            'fields': ('attendance', 'student', 'status')
        }),
        (_('Qo\'shimcha'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        (_('Tizim ma\'lumotlari'), {
            'classes': ('collapse',),
            'fields': ('marked_at', 'created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'attendance__class_subject__class_obj',
            'student__user_branch__user'
        )
    
    @admin.display(description=_('O\'quvchi'))
    def student_name(self, obj):
        return obj.get_student_name()
    
    @admin.display(description=_('Holat'))
    def status_badge(self, obj):
        colors = {
            'present': '#009900',
            'absent': '#cc0000',
            'late': '#ff9900',
            'excused': '#0066cc',
            'sick': '#9933cc'
        }
        labels = {
            'present': 'Bor',
            'absent': 'Yo\'q',
            'late': 'Kech qolgan',
            'excused': 'Sababli',
            'sick': 'Kasal'
        }
        color = colors.get(obj.status, '#999')
        label = labels.get(obj.status, obj.status)
        return format_html(
            '<span style="background-color:{}; color:white; padding:2px 8px; border-radius:3px;">{}</span>',
            color, label
        )


@admin.register(AttendanceStatistics)
class AttendanceStatisticsAdmin(admin.ModelAdmin):
    list_display = (
        'student_name', 'class_subject', 'start_date', 'end_date',
        'total_lessons', 'present_count', 'absent_count', 'attendance_rate', 'last_calculated'
    )
    list_filter = (
        'start_date', 'end_date', 'class_subject__class_obj',
        'last_calculated'
    )
    search_fields = (
        'student__user_branch__user__first_name',
        'student__user_branch__user__last_name',
        'class_subject__class_obj__name',
        'class_subject__subject__name'
    )
    autocomplete_fields = ('student', 'class_subject')
    readonly_fields = (
        'total_lessons', 'present_count', 'absent_count', 'late_count', 'excused_count',
        'attendance_rate', 'last_calculated',
        'created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by'
    )
    list_per_page = 50
    ordering = ('-last_calculated',)
    date_hierarchy = 'start_date'
    
    fieldsets = (
        (_('Statistika ma\'lumotlari'), {
            'fields': ('student', 'class_subject', 'start_date', 'end_date')
        }),
        (_('Davomat ko\'rsatkichlari'), {
            'fields': (
                'total_lessons', 'present_count', 'absent_count', 'late_count', 
                'excused_count', 'attendance_rate'
            )
        }),
        (_('Tizim ma\'lumotlari'), {
            'classes': ('collapse',),
            'fields': ('last_calculated', 'created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'student__user_branch__user',
            'class_subject__class_obj',
            'class_subject__subject'
        )
    
    @admin.display(description=_('O\'quvchi'))
    def student_name(self, obj):
        if obj.student and obj.student.user_branch:
            user = obj.student.user_branch.user
            return f"{user.first_name} {user.last_name}"
        return "Unknown"
