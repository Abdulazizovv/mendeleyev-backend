
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from auth.profiles.models import Profile, UserBranchProfile
from auth.users.models import UserBranch


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
	"""Auto-create global Profile when a new user is created."""
	if created:
		Profile.objects.create(user=instance)


@receiver(post_save, sender=UserBranch)
def create_role_profile(sender, instance: UserBranch, created, **kwargs):
	"""Optionally auto-create role profile for a new branch membership."""
	if created:
		UserBranchProfile.objects.get_or_create(user_branch=instance)