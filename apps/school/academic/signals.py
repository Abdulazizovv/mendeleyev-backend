"""Signals for academic module."""
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime
from .models import AcademicYear, Quarter


@receiver(post_save, sender=AcademicYear)
def create_quarters_for_academic_year(sender, instance, created, **kwargs):
    """
    Akademik yil yaratilganda avtomatik 4 ta chorak yaratish.
    
    Choraklar sanalar:
    - 1-chorak: 2-sentyabr - 4-noyabr
    - 2-chorak: 10-noyabr - 27-dekabr
    - 3-chorak: 5-yanvar - 20-mart
    - 4-chorak: 28-mart - 31-may
    """
    if created:
        year = instance.start_date.year
        
        # 1-chorak
        Quarter.objects.create(
            academic_year=instance,
            name='1-chorak',
            number=1,
            start_date=datetime(year, 9, 2).date(),
            end_date=datetime(year, 11, 4).date(),
            is_active=False
        )
        
        # 2-chorak
        Quarter.objects.create(
            academic_year=instance,
            name='2-chorak',
            number=2,
            start_date=datetime(year, 11, 10).date(),
            end_date=datetime(year, 12, 27).date(),
            is_active=False
        )
        
        # 3-chorak (keyingi yilga o'tadi)
        next_year = year + 1
        Quarter.objects.create(
            academic_year=instance,
            name='3-chorak',
            number=3,
            start_date=datetime(next_year, 1, 5).date(),
            end_date=datetime(next_year, 3, 20).date(),
            is_active=False
        )
        
        # 4-chorak
        Quarter.objects.create(
            academic_year=instance,
            name='4-chorak',
            number=4,
            start_date=datetime(next_year, 3, 28).date(),
            end_date=datetime(next_year, 5, 31).date(),
            is_active=False
        )
