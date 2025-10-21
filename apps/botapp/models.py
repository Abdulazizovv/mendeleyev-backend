from django.db import models
from apps.common.models import BaseModel


class BotUserStatuses(models.TextChoices):
	ACTIVE = "active", "Faol"
	BLOCKED_BY_USER = "blocked", "Foydalanuvchi bloklagan"
	DEACTIVATED = "deactivated", "Foydalanuvchi o'chirilgan"
	BANNED_BY_ADMIN = "banned", "Admin taqiqlagan"


class BotUser(BaseModel):
	telegram_id = models.BigIntegerField(unique=True, db_index=True, verbose_name="Telegram ID")
	is_bot = models.BooleanField(default=False)
	first_name = models.CharField(max_length=255, blank=True)
	last_name = models.CharField(max_length=255, blank=True)
	username = models.CharField(max_length=255, blank=True, db_index=True)
	language_code = models.CharField(max_length=16, blank=True)
	status = models.CharField(max_length=20, choices=BotUserStatuses.choices, default=BotUserStatuses.ACTIVE, db_index=True)
	started_at = models.DateTimeField(null=True, blank=True, verbose_name="Start bosilgan vaqti")
	last_seen_at = models.DateTimeField(null=True, blank=True, verbose_name="Oxirgi faollik")

	def __str__(self) -> str:  # pragma: no cover - trivial
		return f"{self.username or self.first_name or self.telegram_id}"

	# Convenience helpers
	def ban(self, save: bool = True):
		self.status = BotUserStatuses.BANNED_BY_ADMIN
		if save:
			self.save(update_fields=["status", "updated_at"])
		return self

	def unban(self, save: bool = True):
		self.status = BotUserStatuses.ACTIVE
		if save:
			self.save(update_fields=["status", "updated_at"])
		return self

	class Meta:
		verbose_name = "Bot foydalanuvchisi"
		verbose_name_plural = "Bot foydalanuvchilari"
		indexes = [
			models.Index(fields=["username"]),
			models.Index(fields=["telegram_id"]),  # redundant to unique but explicit
			models.Index(fields=["status"]),
		]
