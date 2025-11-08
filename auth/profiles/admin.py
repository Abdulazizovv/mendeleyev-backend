from django.contrib import admin
from .models import Profile, UserBranchProfile


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
