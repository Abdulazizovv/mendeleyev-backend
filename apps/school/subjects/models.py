from django.db import models
from django.conf import settings
from apps.common.models import BaseModel
from apps.branch.models import Branch, BranchMembership
from apps.school.classes.models import Class
from apps.school.academic.models import Quarter


class Subject(BaseModel):
    """Fan modeli.
    
    Har bir filial uchun fanlar yaratiladi.
    """
    
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='subjects',
        verbose_name='Filial'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Fan nomi',
        help_text='Masalan: "Matematika", "Fizika"'
    )
    code = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name='Fan kodi',
        help_text='Masalan: "MATH", "PHYS"'
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='Fan tavsifi',
        help_text='Fan haqida qo\'shimcha ma\'lumot'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Faol fan',
        help_text='Bu fan faolmi?'
    )
    
    class Meta:
        verbose_name = 'Fan'
        verbose_name_plural = 'Fanlar'
        unique_together = [('branch', 'name')]
        indexes = [
            models.Index(fields=['branch', 'is_active']),
            models.Index(fields=['code']),
        ]
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} @ {self.branch.name}"


class ClassSubject(BaseModel):
    """Sinfga fan biriktirish modeli.
    
    Har bir sinf uchun fanlar va ularga o'qituvchilar tayinlanadi.
    """
    
    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='class_subjects',
        verbose_name='Sinf'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='class_subjects',
        verbose_name='Fan'
    )
    teacher = models.ForeignKey(
        BranchMembership,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='taught_subjects',
        verbose_name='O\'qituvchi',
        help_text='Bu fanni o\'qitadigan o\'qituvchi (role=teacher bo\'lishi kerak)',
        limit_choices_to={'role': 'teacher'}
    )
    hours_per_week = models.IntegerField(
        default=2,
        verbose_name='Haftada dars soatlari',
        help_text='Haftada necha soat dars o\'tiladi'
    )
    quarter = models.ForeignKey(
        Quarter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='class_subjects',
        verbose_name='Chorak',
        help_text='Qaysi chorakda o\'qitiladi (ixtiyoriy)'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Faol',
        help_text='Bu fan sinfda faolmi?'
    )
    
    class Meta:
        verbose_name = 'Sinf fani'
        verbose_name_plural = 'Sinf fanlari'
        unique_together = [('class_obj', 'subject')]
        indexes = [
            models.Index(fields=['class_obj', 'is_active']),
            models.Index(fields=['subject', 'is_active']),
            models.Index(fields=['teacher']),
            models.Index(fields=['quarter']),
        ]
        ordering = ['class_obj', 'subject__name']
    
    def __str__(self):
        return f"{self.class_obj.name} - {self.subject.name}"
    
    def save(self, *args, **kwargs):
        """Validate that teacher belongs to the same branch and is a teacher."""
        if self.teacher:
            if self.teacher.role != 'teacher':
                raise ValueError("Teacher must have role='teacher'")
            if self.teacher.branch != self.class_obj.branch:
                raise ValueError("Teacher must belong to the same branch as the class")
        
        # Validate subject belongs to the same branch
        if self.subject.branch != self.class_obj.branch:
            raise ValueError("Subject must belong to the same branch as the class")
        
        # Validate quarter belongs to the same academic year
        if self.quarter:
            if self.quarter.academic_year != self.class_obj.academic_year:
                raise ValueError("Quarter must belong to the same academic year as the class")
        
        super().save(*args, **kwargs)

