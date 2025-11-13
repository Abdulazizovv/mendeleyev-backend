
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from auth.profiles.models import (
	Profile,
	TeacherProfile,
	StudentProfile,
	ParentProfile,
	UserBranchProfile,
	AdminProfile,
)
from auth.users.models import UserBranch, BranchRole
from apps.branch.models import BranchMembership


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
	"""Auto-create global Profile when a new user is created."""
	if created:
		Profile.objects.create(user=instance)


@receiver(post_save, sender=UserBranch)
def create_role_profiles_legacy(sender, instance: UserBranch, created, **kwargs):
	"""Auto-create generic + role-specific profiles on membership save.

	Phase 4: Also provision AdminProfile for admin-class roles. We intentionally run on every save
	(not only when created) to ensure idempotent backfill if roles are updated later.

	Trade-off: We do not automatically soft-delete the old role-specific profile when a role changes.
	Leaving previous profiles intact can be useful for auditing. TODO: Consider adding a soft-delete
	or archival policy for previous role profiles.
	"""
	# Always maintain backward-compatible generic profile
	UserBranchProfile.objects.get_or_create(user_branch=instance)
	role = instance.role
	if role == BranchRole.TEACHER:
		TeacherProfile.objects.get_or_create(user_branch=instance)
	elif role == BranchRole.STUDENT:
		StudentProfile.objects.get_or_create(user_branch=instance)
	elif role == BranchRole.PARENT:
		ParentProfile.objects.get_or_create(user_branch=instance)
	elif role in (BranchRole.BRANCH_ADMIN, BranchRole.SUPER_ADMIN):
		# Ensure AdminProfile exists; flip is_super_admin depending on role
		ap, _ = AdminProfile.objects.get_or_create(user_branch=instance)
		should_be_super = role == BranchRole.SUPER_ADMIN
		if ap.is_super_admin != should_be_super:
			ap.is_super_admin = should_be_super
			ap.save(update_fields=["is_super_admin", "updated_at"])


@receiver(post_save, sender=BranchMembership)
def create_role_profiles(sender, instance: BranchMembership, created, **kwargs):
	"""Mirror receiver for canonical BranchMembership to keep behavior identical.

	Runs on every save to handle role transitions and idempotent backfill.
	"""
	UserBranchProfile.objects.get_or_create(user_branch=instance)
	role = instance.role
	if role == BranchRole.TEACHER:
		TeacherProfile.objects.get_or_create(user_branch=instance)
	elif role == BranchRole.STUDENT:
		StudentProfile.objects.get_or_create(user_branch=instance)
	elif role == BranchRole.PARENT:
		ParentProfile.objects.get_or_create(user_branch=instance)
	elif role in (BranchRole.BRANCH_ADMIN, BranchRole.SUPER_ADMIN):
		ap, _ = AdminProfile.objects.get_or_create(user_branch=instance)
		should_be_super = role == BranchRole.SUPER_ADMIN
		if ap.is_super_admin != should_be_super:
			ap.is_super_admin = should_be_super
			ap.save(update_fields=["is_super_admin", "updated_at"])