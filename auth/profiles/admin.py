from django.contrib import admin
from .models import (
    Profile,
    UserBranchProfile,
    TeacherProfile,
    StudentProfile,
    ParentProfile,
    AdminProfile,
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


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("user_branch", "grade", "enrollment_date")
    search_fields = ("grade", "user_branch__user__phone_number", "user_branch__branch__name")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("user_branch",)


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
