"""
Signals for finance app.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='profiles.StudentProfile')
def create_student_balance(sender, instance, created, **kwargs):
    """Auto-create StudentBalance when a new StudentProfile is created.
    
    Note: Using string reference 'profiles.StudentProfile' to avoid circular imports.
    """
    if created:
        # Lazy import to avoid circular dependency
        from .models import StudentBalance
        
        StudentBalance.objects.get_or_create(
            student_profile=instance,
            defaults={
                'balance': 0,
                'created_by': instance.created_by,
                'updated_by': instance.updated_by,
            }
        )

