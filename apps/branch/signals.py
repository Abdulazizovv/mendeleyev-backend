"""
Signals for branch app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Branch, BranchSettings


@receiver(post_save, sender=Branch)
def create_branch_settings(sender, instance: Branch, created, **kwargs):
    """Auto-create BranchSettings when a new Branch is created."""
    if created:
        BranchSettings.objects.get_or_create(
            branch=instance,
            defaults={
                'created_by': instance.created_by,
                'updated_by': instance.updated_by,
            }
        )

