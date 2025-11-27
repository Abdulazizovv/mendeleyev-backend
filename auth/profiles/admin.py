from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import (
    Profile,
    UserBranchProfile,
    TeacherProfile,
    StudentProfile,
    ParentProfile,
    AdminProfile,
    StudentRelative,
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "gender", "language", "timezone", "created_at")
    search_fields = ("user__phone_number", "user__first_name", "user__last_name")
    list_filter = ("gender",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(UserBranchProfile)
class UserBranchProfileAdmin(admin.ModelAdmin):
    list_display = ("user_branch", "title", "created_at")
    search_fields = ("user_branch__user__phone_number", "user_branch__branch__name", "title")
    readonly_fields = ("created_at", "updated_at")


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ("user_branch", "subject", "experience_years")
    search_fields = ("subject", "user_branch__user__phone_number", "user_branch__branch__name")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("user_branch",)


class StudentRelativeInline(admin.TabularInline):
    """O'quvchi yaqinlari inline."""
    model = StudentRelative
    extra = 1
    fields = (
        'relationship_type',
        'first_name',
        'middle_name',
        'last_name',
        'phone_number',
        'email',
        'is_primary_contact',
        'is_guardian',
    )
    readonly_fields = ()
    autocomplete_fields = ()
    verbose_name = _('Yaqin')
    verbose_name_plural = _('Yaqinlar')
    can_delete = True
    show_change_link = True
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(deleted_at__isnull=True).order_by('relationship_type', 'first_name')


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = (
        'personal_number_display',
        'student_name_display',
        'branch_display',
        'class_display',
        'phone_display',
        'gender_display',
        'date_of_birth',
        'relatives_count',
        'created_at'
    )
    list_filter = (
        'gender',
        'user_branch__branch',
        'date_of_birth',
        'created_at',
    )
    search_fields = (
        'personal_number',
        'user_branch__user__phone_number',
        'user_branch__user__first_name',
        'user_branch__user__last_name',
        'middle_name',
        'user_branch__branch__name',
    )
    autocomplete_fields = ('user_branch',)
    readonly_fields = (
        'personal_number',
        'created_at',
        'updated_at',
        'deleted_at',
        'created_by',
        'updated_by',
        'full_name_display',
        'current_class_display',
        'relatives_count_display',
    )
    date_hierarchy = 'created_at'
    list_per_page = 50
    inlines = [StudentRelativeInline]
    
    fieldsets = (
        (_('Asosiy ma\'lumotlar'), {
            'fields': ('personal_number', 'user_branch', 'full_name_display', 'middle_name', 'gender', 'date_of_birth', 'address')
        }),
        (_('Hujjatlar'), {
            'fields': ('birth_certificate',)
        }),
        (_('Qo\'shimcha ma\'lumotlar'), {
            'fields': ('additional_fields', 'current_class_display', 'relatives_count_display')
        }),
        (_('Eski fieldlar (backward compatibility)'), {
            'classes': ('collapse',),
            'fields': ('grade', 'enrollment_date', 'parent_name')
        }),
        (_('Tizim ma\'lumotlari'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'user_branch',
            'user_branch__user',
            'user_branch__branch'
        ).prefetch_related('relatives')
    
    @admin.display(description=_('Shaxsiy raqam'))
    def personal_number_display(self, obj):
        if obj.personal_number:
            return format_html('<strong style="color:#0066cc;">{}</strong>', obj.personal_number)
        return format_html('<span style="color:#999;">-</span>')
    
    @admin.display(description=_('O\'quvchi'))
    def student_name_display(self, obj):
        return obj.full_name or obj.user_branch.user.phone_number
    
    @admin.display(description=_('Filial'))
    def branch_display(self, obj):
        return obj.user_branch.branch.name if obj.user_branch.branch else '-'
    
    @admin.display(description=_('Sinf'))
    def class_display(self, obj):
        current_class = obj.current_class
        if current_class:
            return current_class.name
        return '-'
    
    @admin.display(description=_('Telefon'))
    def phone_display(self, obj):
        return obj.user_branch.user.phone_number
    
    @admin.display(description=_('Jinsi'))
    def gender_display(self, obj):
        return obj.get_gender_display()
    
    @admin.display(description=_('To\'liq ism'))
    def full_name_display(self, obj):
        return obj.full_name or '-'
    
    @admin.display(description=_('Joriy sinf'))
    def current_class_display(self, obj):
        current_class = obj.current_class
        if current_class:
            return f"{current_class.name} ({current_class.academic_year.name})"
        return _('Sinfga biriktirilmagan')
    
    @admin.display(description=_('Yaqinlar soni'))
    def relatives_count(self, obj):
        count = obj.relatives.count()
        if count > 0:
            return format_html('<span style="color:#090;">{}</span>', count)
        return format_html('<span style="color:#999;">{}</span>', count)
    
    @admin.display(description=_('Yaqinlar soni'))
    def relatives_count_display(self, obj):
        return obj.relatives.count()


@admin.register(StudentRelative)
class StudentRelativeAdmin(admin.ModelAdmin):
    list_display = (
        'relative_name_display',
        'student_display',
        'relationship_type_display',
        'phone_display',
        'is_primary_contact_badge',
        'is_guardian_badge',
        'created_at'
    )
    list_filter = (
        'relationship_type',
        'is_primary_contact',
        'is_guardian',
        'gender',
        'student_profile__user_branch__branch',
        'created_at',
    )
    search_fields = (
        'first_name',
        'last_name',
        'middle_name',
        'phone_number',
        'email',
        'student_profile__user_branch__user__phone_number',
        'student_profile__user_branch__user__first_name',
        'student_profile__user_branch__user__last_name',
    )
    autocomplete_fields = ('student_profile',)
    readonly_fields = (
        'created_at',
        'updated_at',
        'deleted_at',
        'created_by',
        'updated_by',
        'full_name_display',
    )
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    fieldsets = (
        (_('Asosiy ma\'lumotlar'), {
            'fields': (
                'student_profile',
                'relationship_type',
                'full_name_display',
                'first_name',
                'middle_name',
                'last_name',
                'gender',
                'date_of_birth',
            )
        }),
        (_('Kontakt ma\'lumotlari'), {
            'fields': ('phone_number', 'email', 'address')
        }),
        (_('Ish joyi'), {
            'fields': ('workplace', 'position')
        }),
        (_('Hujjatlar'), {
            'fields': ('passport_number', 'photo')
        }),
        (_('Status'), {
            'fields': ('is_primary_contact', 'is_guardian')
        }),
        (_('Qo\'shimcha ma\'lumotlar'), {
            'fields': ('additional_info', 'notes')
        }),
        (_('Tizim ma\'lumotlari'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'student_profile',
            'student_profile__user_branch',
            'student_profile__user_branch__user',
            'student_profile__user_branch__branch'
        )
    
    @admin.display(description=_('Yaqin'))
    def relative_name_display(self, obj):
        return obj.full_name
    
    @admin.display(description=_('O\'quvchi'))
    def student_display(self, obj):
        return obj.student_profile.full_name or obj.student_profile.user_branch.user.phone_number
    
    @admin.display(description=_('Munosabat'))
    def relationship_type_display(self, obj):
        return obj.get_relationship_type_display()
    
    @admin.display(description=_('Telefon'))
    def phone_display(self, obj):
        return obj.phone_number or '-'
    
    @admin.display(description=_('Asosiy kontakt'), boolean=True)
    def is_primary_contact_badge(self, obj):
        if obj.is_primary_contact:
            return format_html('<span style="color:#090;">✓</span>')
        return format_html('<span style="color:#999;">-</span>')
    
    @admin.display(description=_('Vasiy'), boolean=True)
    def is_guardian_badge(self, obj):
        if obj.is_guardian:
            return format_html('<span style="color:#090;">✓</span>')
        return format_html('<span style="color:#999;">-</span>')
    
    @admin.display(description=_('To\'liq ism'))
    def full_name_display(self, obj):
        return obj.full_name


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = ("user_branch",)
    search_fields = ("user_branch__user__phone_number", "user_branch__branch__name")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("user_branch",)


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ("user_branch", "is_super_admin", "title", "created_at")
    search_fields = (
        "user_branch__user__phone_number",
        "user_branch__branch__name",
        "title",
    )
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("user_branch",)
    filter_horizontal = ("managed_branches",)
