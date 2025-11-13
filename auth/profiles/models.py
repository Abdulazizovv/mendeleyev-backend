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
	"""Backward-compatible generic role-aware profile.

	Phase 1: Keep this model for existing code (display_name/title/about), while we add
	new specialized per-role profile models below. Future phases may deprecate this.
	"""

	user_branch = models.OneToOneField('users.UserBranch', on_delete=models.CASCADE, related_name='generic_profile')
	display_name = models.CharField(max_length=150, blank=True, default='', help_text='Role-specific display name')
	title = models.CharField(max_length=150, blank=True, default='', help_text='e.g., Physics Teacher, 9A Student')
	about = models.TextField(blank=True, default='')
	contacts = models.JSONField(blank=True, null=True, help_text='{"phone":"+998...","email":"..."}')

	class Meta:
		verbose_name = 'Rolga xos profil (umumiy)'
		verbose_name_plural = 'Rolga xos profillar (umumiy)'

	def __str__(self):  # pragma: no cover - trivial
		return f"UserBranchProfile<{self.user_branch_id}>"


class TeacherProfile(BaseModel):
	"""Teacher-specific profile fields linked to a branch membership.

	We avoid multi-table inheritance for clarity and direct OneToOne composition.
	"""
	user_branch = models.OneToOneField('users.UserBranch', on_delete=models.CASCADE, related_name='teacher_profile')
	subject = models.CharField(max_length=120, blank=True, default='')
	experience_years = models.PositiveIntegerField(blank=True, null=True)
	bio = models.TextField(blank=True, default='')

	class Meta:
		verbose_name = 'O‘qituvchi profili'
		verbose_name_plural = 'O‘qituvchi profillari'

	def __str__(self):  # pragma: no cover - trivial
		return f"TeacherProfile<{self.user_branch_id}>"


class StudentProfile(BaseModel):
	"""Student-specific profile fields linked to a branch membership."""
	user_branch = models.OneToOneField('users.UserBranch', on_delete=models.CASCADE, related_name='student_profile')
	grade = models.CharField(max_length=32, blank=True, default='')
	enrollment_date = models.DateField(blank=True, null=True)
	parent_name = models.CharField(max_length=150, blank=True, default='')

	class Meta:
		verbose_name = 'O‘quvchi profili'
		verbose_name_plural = 'O‘quvchi profillari'

	def __str__(self):  # pragma: no cover - trivial
		return f"StudentProfile<{self.user_branch_id}>"


class ParentProfile(BaseModel):
	"""Parent-specific profile fields linked to a branch membership."""
	user_branch = models.OneToOneField('users.UserBranch', on_delete=models.CASCADE, related_name='parent_profile')
	notes = models.TextField(blank=True, default='')
	related_students = models.ManyToManyField(StudentProfile, blank=True, related_name='parent_links')

	class Meta:
		verbose_name = 'Ota-ona profili'
		verbose_name_plural = 'Ota-ona profillari'

	def __str__(self):  # pragma: no cover - trivial
		return f"ParentProfile<{self.user_branch_id}>"


class AdminProfile(BaseModel):
		"""Admin-specific profile for branch_admin and super_admin memberships.

		Note on relation target:
		- We intentionally link to the legacy concrete model 'users.UserBranch' rather than the
			proxy 'apps.branch.BranchMembership'. Django does not allow ForeignKey/OneToOne to
			proxy models because they don't have their own table. Since BranchMembership is a
			proxy over the same table, using 'users.UserBranch' keeps backward compatibility and
			requires no schema changes, while still working transparently with the proxy in code.
		"""

		# Keep field name consistent with other role profiles for DX and admin inlines
		user_branch = models.OneToOneField('users.UserBranch', on_delete=models.CASCADE, related_name='admin_profile')

		# True when the membership role is super_admin; branch_admin remains False
		is_super_admin = models.BooleanField(default=False)

		# Optional: which branches this admin manages; useful for UI scoping/filters
		managed_branches = models.ManyToManyField('branch.Branch', blank=True, related_name='managed_by_admin_profiles')

		# Optional fields for display in UI
		title = models.CharField(max_length=255, blank=True, default='')
		notes = models.TextField(blank=True, default='')

		class Meta:
				verbose_name = 'Admin profili'
				verbose_name_plural = 'Admin profillari'

		def __str__(self):  # pragma: no cover - trivial
				return f"AdminProfile<{self.user_branch_id}, super={self.is_super_admin}>"
