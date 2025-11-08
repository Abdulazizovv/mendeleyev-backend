from __future__ import annotations

from django.db import models
from django.conf import settings
from apps.common.models import BaseModel


class Gender(models.TextChoices):
	MALE = 'male', 'Male'
	FEMALE = 'female', 'Female'
	OTHER = 'other', 'Other'
	UNSPECIFIED = 'unspecified', 'Unspecified'


class Profile(BaseModel):
	"""Global profile for a user, independent of branch/role."""

	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
	avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
	date_of_birth = models.DateField(blank=True, null=True)
	gender = models.CharField(max_length=16, choices=Gender.choices, default=Gender.UNSPECIFIED)
	language = models.CharField(max_length=16, default='uz', blank=True)
	timezone = models.CharField(max_length=64, default='Asia/Tashkent', blank=True)
	bio = models.TextField(blank=True, default='')
	address = models.CharField(max_length=255, blank=True, default='')
	socials = models.JSONField(blank=True, null=True, help_text='{"telegram":"@user", "instagram":"u"}')

	class Meta:
		verbose_name = 'Profil'
		verbose_name_plural = 'Profillar'

	def __str__(self):  # pragma: no cover - trivial
		return f"Profile<{self.user_id}>"



class UserBranchProfile(BaseModel):
	"""Role-aware profile attached to a specific UserBranch membership."""

	# We import lazily by string to avoid circular import at import time
	user_branch = models.OneToOneField('users.UserBranch', on_delete=models.CASCADE, related_name='role_profile')
	display_name = models.CharField(max_length=150, blank=True, default='', help_text='Role-specific display name')
	title = models.CharField(max_length=150, blank=True, default='', help_text='e.g., Physics Teacher, 9A Student')
	about = models.TextField(blank=True, default='')
	contacts = models.JSONField(blank=True, null=True, help_text='{"phone":"+998...","email":"..."}')

	class Meta:
		verbose_name = 'Rolga xos profil'
		verbose_name_plural = 'Rolga xos profillar'

	def __str__(self):  # pragma: no cover - trivial
		return f"UserBranchProfile<{self.user_branch_id}>"
