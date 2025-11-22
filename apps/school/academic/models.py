from django.db import models
from django.conf import settings
from apps.common.models import BaseModel
from apps.branch.models import Branch


class AcademicYear(BaseModel):
    """Akademik yil modeli.
    
    Har bir filial uchun akademik yillar saqlanadi.
    Faqat bitta akademik yil active bo'lishi mumkin.
    """
    
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='academic_years',
        verbose_name='Filial'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Akademik yil nomi',
        help_text='Masalan: "2024-2025"'
    )
    start_date = models.DateField(
        verbose_name='Boshlanish sanasi'
    )
    end_date = models.DateField(
        verbose_name='Tugash sanasi'
    )
    is_active = models.BooleanField(
        default=False,
        verbose_name='Joriy akademik yil',
        help_text='Faqat bitta akademik yil active bo\'lishi mumkin'
    )
    
    class Meta:
        verbose_name = 'Akademik yil'
        verbose_name_plural = 'Akademik yillar'
        unique_together = [('branch', 'name')]
        indexes = [
            models.Index(fields=['branch', 'is_active']),
            models.Index(fields=['start_date', 'end_date']),
        ]
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.name} @ {self.branch.name}"
    
    def save(self, *args, **kwargs):
        """Agar is_active=True bo'lsa, boshqa akademik yillarni active=False qilish."""
        if self.is_active:
            AcademicYear.objects.filter(
                branch=self.branch,
                is_active=True
            ).exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)


class Quarter(BaseModel):
    """Chorak modeli.
    
    Har bir akademik yil uchun 4 ta chorak bo'ladi.
    """
    
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='quarters',
        verbose_name='Akademik yil'
    )
    name = models.CharField(
        max_length=50,
        verbose_name='Chorak nomi',
        help_text='Masalan: "1-chorak", "2-chorak"'
    )
    number = models.IntegerField(
        choices=[(1, '1-chorak'), (2, '2-chorak'), (3, '3-chorak'), (4, '4-chorak')],
        verbose_name='Chorak raqami'
    )
    start_date = models.DateField(
        verbose_name='Boshlanish sanasi'
    )
    end_date = models.DateField(
        verbose_name='Tugash sanasi'
    )
    is_active = models.BooleanField(
        default=False,
        verbose_name='Joriy chorak',
        help_text='Faqat bitta chorak active bo\'lishi mumkin'
    )
    
    class Meta:
        verbose_name = 'Chorak'
        verbose_name_plural = 'Choraklar'
        unique_together = [('academic_year', 'number')]
        indexes = [
            models.Index(fields=['academic_year', 'is_active']),
            models.Index(fields=['start_date', 'end_date']),
        ]
        ordering = ['academic_year', 'number']
    
    def __str__(self):
        return f"{self.name} - {self.academic_year.name}"
    
    def save(self, *args, **kwargs):
        """Agar is_active=True bo'lsa, boshqa choraklarni active=False qilish."""
        if self.is_active:
            Quarter.objects.filter(
                academic_year=self.academic_year,
                is_active=True
            ).exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)

