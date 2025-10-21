from django.contrib import admin
from .models import BotUser, BotUserStatuses


@admin.register(BotUser)
class BotUserAdmin(admin.ModelAdmin):
	list_display = ("telegram_id", "username", "first_name", "last_name", "language_code", "status", "started_at", "last_seen_at")
	search_fields = ("telegram_id", "username", "first_name", "last_name")
	list_filter = ("language_code", "status", "created_at")
	readonly_fields = ("created_at", "updated_at", "deleted_at")
	ordering = ("-created_at",)
	actions = ("ban_users", "unban_users")

	@admin.action(description="Taqiqlash (ban)")
	def ban_users(self, request, queryset):
		updated = queryset.update(status=BotUserStatuses.BANNED_BY_ADMIN)
		self.message_user(request, f"{updated} ta foydalanuvchi taqiqlangan")

	@admin.action(description="Taqiqni olib tashlash (unban)")
	def unban_users(self, request, queryset):
		updated = queryset.update(status=BotUserStatuses.ACTIVE)
		self.message_user(request, f"{updated} ta foydalanuvchi faollashtirildi")
