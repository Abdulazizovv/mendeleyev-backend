from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Count
from .models import TimetableTemplate, TimetableSlot, LessonInstance, LessonTopic


class TimetableSlotInline(admin.TabularInline):
    """Inline for timetable slots within a template."""
    model = TimetableSlot
    extra = 0
    fields = ('class_obj', 'class_subject', 'day_of_week', 'lesson_number', 'start_time', 'end_time', 'room')
    autocomplete_fields = ('class_obj', 'class_subject', 'room')
    ordering = ('day_of_week', 'lesson_number')


@admin.register(TimetableTemplate)
class TimetableTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'branch', 'academic_year', 'is_active_badge', 
        'effective_from', 'slots_count', 'created_at'
    )
    list_filter = ('branch', 'academic_year', 'is_active', 'effective_from', 'created_at')
    search_fields = ('name', 'branch__name', 'academic_year__name')
    autocomplete_fields = ('branch', 'academic_year')
    readonly_fields = ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
    date_hierarchy = 'effective_from'
    list_per_page = 30
    ordering = ('-effective_from', '-created_at')
    
    fieldsets = (
        (_('Asosiy ma\'lumotlar'), {
            'fields': ('branch', 'academic_year', 'name', 'is_active')
        }),
        (_('Amal qilish muddati'), {
            'fields': ('effective_from', 'effective_until')
        }),
        (_('Qo\'shimcha ma\'lumotlar'), {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        (_('Tizim ma\'lumotlari'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
        }),
    )
    
    inlines = [TimetableSlotInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('branch', 'academic_year').annotate(
            _slots_count=Count('slots', distinct=True)
        )
    
    @admin.display(description=_('Holati'), boolean=True)
    def is_active_badge(self, obj):
        return obj.is_active
    
    @admin.display(description=_('Slotlar soni'))
    def slots_count(self, obj):
        return getattr(obj, '_slots_count', obj.slots.count())


@admin.register(TimetableSlot)
class TimetableSlotAdmin(admin.ModelAdmin):
    list_display = (
        'timetable', 'class_obj', 'day_of_week_display', 'lesson_number', 
        'start_time', 'end_time', 'class_subject', 'room'
    )
    list_filter = ('timetable', 'day_of_week', 'lesson_number', 'class_subject__class_obj')
    search_fields = (
        'timetable__name', 'class_subject__class_obj__name', 
        'class_subject__subject__name', 'room__name'
    )
    autocomplete_fields = ('timetable', 'class_obj', 'class_subject', 'room')
    readonly_fields = ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
    list_per_page = 50
    ordering = ('timetable', 'day_of_week', 'lesson_number')
    
    fieldsets = (
        (_('Jadval ma\'lumotlari'), {
            'fields': ('timetable', 'class_obj', 'class_subject')
        }),
        (_('Vaqt va joy'), {
            'fields': ('day_of_week', 'lesson_number', 'start_time', 'end_time', 'room')
        }),
        (_('Tizim ma\'lumotlari'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'timetable', 'class_subject__class_obj', 
            'class_subject__subject', 'room'
        )
    
    @admin.display(description=_('Hafta kuni'))
    def day_of_week_display(self, obj):
        days = {
            0: 'Dushanba',
            1: 'Seshanba',
            2: 'Chorshanba',
            3: 'Payshanba',
            4: 'Juma',
            5: 'Shanba',
            6: 'Yakshanba'
        }
        return days.get(obj.day_of_week, obj.day_of_week)


@admin.register(LessonInstance)
class LessonInstanceAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'lesson_number', 'class_subject', 'topic', 
        'status_badge', 'is_auto_generated', 'created_at'
    )
    list_filter = (
        'status', 'is_auto_generated', 'date', 'lesson_number', 
        'class_subject__class_obj'
    )
    search_fields = (
        'class_subject__class_obj__name', 'class_subject__subject__name',
        'topic__title', 'teacher_notes', 'homework'
    )
    autocomplete_fields = ('class_subject', 'topic', 'room', 'timetable_slot')
    readonly_fields = (
        'is_auto_generated',
        'created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by'
    )
    date_hierarchy = 'date'
    list_per_page = 50
    ordering = ('-date', 'lesson_number')
    
    fieldsets = (
        (_('Dars ma\'lumotlari'), {
            'fields': ('class_subject', 'date', 'lesson_number', 'topic')
        }),
        (_('Vaqt va joy'), {
            'fields': ('start_time', 'end_time', 'room')
        }),
        (_('Holat'), {
            'fields': ('status',)
        }),
        (_('Avtomatik generatsiya'), {
            'fields': ('is_auto_generated', 'timetable_slot'),
            'classes': ('collapse',)
        }),
        (_('Qo\'shimcha'), {
            'fields': ('homework', 'teacher_notes'),
            'classes': ('collapse',)
        }),
        (_('Tizim ma\'lumotlari'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'class_subject__class_obj', 'class_subject__subject',
            'class_subject__teacher',
            'topic', 'room', 'timetable_slot'
        )
    
    @admin.display(description=_('Holat'))
    def status_badge(self, obj):
        colors = {
            'planned': '#0066cc',
            'completed': '#009900',
            'canceled': '#cc0000'
        }
        labels = {
            'planned': 'Rejalashtirilgan',
            'completed': 'Bajarilgan',
            'canceled': 'Bekor qilingan'
        }
        color = colors.get(obj.status, '#999')
        label = labels.get(obj.status, obj.status)
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>',
            color, label
        )


@admin.register(LessonTopic)
class LessonTopicAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'subject', 'quarter', 'position', 
        'created_at'
    )
    list_filter = ('subject', 'quarter', 'created_at')
    search_fields = ('title', 'description', 'subject__name')
    autocomplete_fields = ('subject', 'quarter')
    readonly_fields = ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
    list_per_page = 50
    ordering = ('subject', 'quarter', 'position')
    
    fieldsets = (
        (_('Mavzu ma\'lumotlari'), {
            'fields': ('subject', 'quarter', 'title', 'description')
        }),
        (_('Tartiblash'), {
            'fields': ('position',)
        }),
        (_('Tizim ma\'lumotlari'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('subject', 'quarter')
