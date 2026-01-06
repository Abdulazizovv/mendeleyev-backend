"""Signals for schedule module."""
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from .models import TimetableSlot, LessonInstance, LessonStatus
import logging

logger = logging.getLogger(__name__)


@receiver(pre_delete, sender=TimetableSlot)
def delete_future_generated_lessons(sender, instance, **kwargs):
    """
    When a TimetableSlot is deleted, delete all future auto-generated lessons 
    that are still in PLANNED status.
    
    This prevents orphaned lessons from existing after their template is removed.
    """
    from django.utils import timezone
    
    if instance.deleted_at is None:  # Soft delete
        today = timezone.now().date()
        
        # Find all auto-generated lessons from this slot that are in the future and planned
        future_lessons = LessonInstance.objects.filter(
            timetable_slot=instance,
            is_auto_generated=True,
            status=LessonStatus.PLANNED,
            date__gte=today,
            deleted_at__isnull=True
        )
        
        count = future_lessons.count()
        if count > 0:
            logger.info(
                f"Deleting {count} future planned lessons from slot {instance.id} "
                f"({instance.class_obj.name} - {instance.day_of_week} - lesson {instance.lesson_number})"
            )
            future_lessons.delete()
