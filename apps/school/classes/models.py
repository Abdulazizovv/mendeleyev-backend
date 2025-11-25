from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from apps.common.models import BaseModel
from apps.branch.models import Branch, BranchMembership
from apps.school.academic.models import AcademicYear


class Class(BaseModel):
    """Sinf modeli.
    
    Har bir filial va akademik yil uchun sinflar yaratiladi.
    Sinfga o'qituvchi va o'quvchilar biriktiriladi.
    """
    
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='classes',
        verbose_name='Filial'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='classes',
        verbose_name='Akademik yil'
    )
    name = models.CharField(
        max_length=50,
        verbose_name='Sinf nomi',
        help_text='Masalan: "1-A", "5-B"'
    )
    grade_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(11)],
        verbose_name='Sinf darajasi',
        help_text='Sinf darajasi (1-11)'
    )
    section = models.CharField(
        max_length=10,
        blank=True,
        default='',
        verbose_name='Bo\'lim',
        help_text='Bo\'lim (A, B, C, ...)'
    )
    class_teacher = models.ForeignKey(
        BranchMembership,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='taught_classes',
        verbose_name='Sinf o\'qituvchisi',
        help_text='Sinf o\'qituvchisi (role=teacher bo\'lishi kerak)',
        limit_choices_to={'role': 'teacher'}
    )
    max_students = models.IntegerField(
        default=30,
        validators=[MinValueValidator(1)],
        verbose_name='Maksimal o\'quvchilar soni',
        help_text='Sinfda bo\'lishi mumkin bo\'lgan maksimal o\'quvchilar soni'
    )
    room = models.ForeignKey(
        'rooms.Room',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='classes',
        verbose_name='Xona'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Faol sinf',
        help_text='Bu sinf faolmi?'
    )
    
    class Meta:
        verbose_name = 'Sinf'
        verbose_name_plural = 'Sinflar'
        unique_together = [('branch', 'academic_year', 'name')]
        indexes = [
            models.Index(fields=['branch', 'academic_year', 'is_active']),
            models.Index(fields=['grade_level', 'section']),
            models.Index(fields=['class_teacher']),
        ]
        ordering = ['academic_year', 'grade_level', 'section', 'name']
    
    def __str__(self):
        return f"{self.name} @ {self.branch.name} ({self.academic_year.name})"
    
    @property
    def current_students_count(self):
        """Joriy o'quvchilar soni."""
        return self.class_students.filter(
            deleted_at__isnull=True,
            is_active=True,
            membership__deleted_at__isnull=True
        ).count()
    
    def can_add_student(self):
        """Sinfga yana o'quvchi qo'shish mumkinmi?"""
        return self.current_students_count < self.max_students


class ClassStudent(BaseModel):
    """Sinf o'quvchilari through model.
    
    O'quvchini sinfga biriktirish uchun.
    """
    
    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='class_students',
        verbose_name='Sinf'
    )
    membership = models.ForeignKey(
        BranchMembership,
        on_delete=models.CASCADE,
        related_name='class_enrollments',
        verbose_name='O\'quvchi a\'zoligi',
        help_text='O\'quvchi BranchMembership (role=student bo\'lishi kerak)',
        limit_choices_to={'role': 'student'}
    )
    enrollment_date = models.DateField(
        auto_now_add=True,
        verbose_name='Qo\'shilgan sana',
        help_text='O\'quvchi sinfga qo\'shilgan sana'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Faol',
        help_text='O\'quvchi hozirgi vaqtda bu sinfda o\'qiydimi?'
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='Izohlar',
        help_text='Qo\'shimcha izohlar'
    )
    
    class Meta:
        verbose_name = 'Sinf o\'quvchisi'
        verbose_name_plural = 'Sinf o\'quvchilari'
        unique_together = [('class_obj', 'membership')]
        indexes = [
            models.Index(fields=['class_obj', 'is_active']),
            models.Index(fields=['membership', 'is_active']),
            models.Index(fields=['enrollment_date']),
        ]
        ordering = ['-enrollment_date', 'membership__user__first_name']
    
    def __str__(self):
        user = self.membership.user
        return f"{user.get_full_name() or user.phone_number} - {self.class_obj.name}"
    
    def save(self, *args, **kwargs):
        """Validate that membership is a student."""
        if self.membership.role != 'student':
            raise ValueError("Membership must have role='student'")
        super().save(*args, **kwargs)
    
    @property
    def student(self):
        """O'quvchi BranchMembership."""
        return self.membership
    
    @property
    def user(self):
        """O'quvchi User."""
        return self.membership.user

