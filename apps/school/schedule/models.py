from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.common.models import BaseModel
from apps.branch.models import Branch
from apps.school.academic.models import AcademicYear, Quarter
from apps.school.subjects.models import Subject, ClassSubject
from apps.school.classes.models import Class
from apps.school.rooms.models import Room
from apps.branch.models import BranchMembership
from datetime import time, timedelta


class DayOfWeek(models.TextChoices):
    """Days of the week for schedule."""
    MONDAY = 'monday', 'Dushanba'
    TUESDAY = 'tuesday', 'Seshanba'
    WEDNESDAY = 'wednesday', 'Chorshanba'
    THURSDAY = 'thursday', 'Payshanba'
    FRIDAY = 'friday', 'Juma'
    SATURDAY = 'saturday', 'Shanba'
    SUNDAY = 'sunday', 'Yakshanba'


class LessonStatus(models.TextChoices):
    """Status of a lesson instance."""
    PLANNED = 'planned', 'Rejalashtirilgan'
    COMPLETED = 'completed', 'Tugallangan'
    CANCELED = 'canceled', 'Bekor qilingan'
    IN_PROGRESS = 'in_progress', 'Davom etmoqda'


class TimetableTemplate(BaseModel):
    """Timetable template for an academic year.
    
    Represents the master timetable configuration for a branch's academic year.
    Used to generate actual lesson instances.
    """
    
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='timetable_templates',
        verbose_name='Filial'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='timetable_templates',
        verbose_name='Akademik yil'
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Nomi',
        help_text='Jadval shabloni nomi. Masalan: "2025-2026 Kuz semestri"'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Tavsif'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Faol',
        help_text='Faqat bitta shablon faol bo\'lishi mumkin'
    )
    effective_from = models.DateField(
        verbose_name='Amal qilish sanasi (boshlanish)',
        help_text='Ushbu jadval qachondan amal qila boshlaydi'
    )
    effective_until = models.DateField(
        null=True,
        blank=True,
        verbose_name='Amal qilish sanasi (tugash)',
        help_text='Ushbu jadval qachongacha amal qiladi'
    )
    
    class Meta:
        verbose_name = 'Dars jadvali shabloni'
        verbose_name_plural = 'Dars jadvali shablonlari'
        ordering = ['-effective_from', '-created_at']
        indexes = [
            models.Index(fields=['branch', 'academic_year']),
            models.Index(fields=['is_active', 'effective_from']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['branch', 'academic_year', 'is_active'],
                condition=models.Q(is_active=True, deleted_at__isnull=True),
                name='unique_active_timetable_per_year'
            )
        ]
    
    def __str__(self):
        return f"{self.name} ({self.academic_year})"
    
    def save(self, *args, **kwargs):
        """Validate before saving."""
        # Ensure effective_from is within academic year
        if self.academic_year:
            if self.effective_from < self.academic_year.start_date:
                raise ValidationError(
                    "Jadval amal qilish sanasi akademik yildan oldin bo'lmasligi kerak."
                )
            if self.effective_until and self.effective_until > self.academic_year.end_date:
                raise ValidationError(
                    "Jadval tugash sanasi akademik yildan keyin bo'lmasligi kerak."
                )
        
        # If setting this as active, deactivate other templates
        if self.is_active and not self.deleted_at:
            TimetableTemplate.objects.filter(
                branch=self.branch,
                academic_year=self.academic_year,
                is_active=True,
                deleted_at__isnull=True
            ).exclude(id=self.id).update(is_active=False)
        
        super().save(*args, **kwargs)


class TimetableSlot(BaseModel):
    """Individual slot in a timetable template.
    
    Defines when and where a subject is taught for a specific class.
    Used to generate LessonInstance records.
    """
    
    timetable = models.ForeignKey(
        TimetableTemplate,
        on_delete=models.CASCADE,
        related_name='slots',
        verbose_name='Jadval shabloni'
    )
    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='timetable_slots',
        verbose_name='Sinf'
    )
    class_subject = models.ForeignKey(
        ClassSubject,
        on_delete=models.CASCADE,
        related_name='timetable_slots',
        verbose_name='Sinf fani',
        help_text='Subject assigned to this class'
    )
    day_of_week = models.CharField(
        max_length=10,
        choices=DayOfWeek.choices,
        verbose_name='Hafta kuni'
    )
    lesson_number = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(15)],
        verbose_name='Dars raqami',
        help_text='Kun ichidagi dars tartibi (1-15)'
    )
    start_time = models.TimeField(
        verbose_name='Boshlanish vaqti'
    )
    end_time = models.TimeField(
        verbose_name='Tugash vaqti'
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='timetable_slots',
        verbose_name='Xona',
        help_text='Dars o\'tiladigan xona'
    )
    
    class Meta:
        verbose_name = 'Dars jadvali sloti'
        verbose_name_plural = 'Dars jadvali slotlari'
        ordering = ['day_of_week', 'lesson_number', 'start_time']
        indexes = [
            models.Index(fields=['timetable', 'class_obj']),
            models.Index(fields=['day_of_week', 'lesson_number']),
            models.Index(fields=['class_subject']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['timetable', 'class_obj', 'day_of_week', 'lesson_number'],
                condition=models.Q(deleted_at__isnull=True),
                name='unique_slot_per_class_day_lesson'
            )
        ]
    
    def __str__(self):
        return (
            f"{self.class_obj.name} - {self.class_subject.subject.name} - "
            f"{self.get_day_of_week_display()} - {self.lesson_number}"
        )
    
    def clean(self):
        """Validate slot data."""
        super().clean()
        
        # Validate times
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({
                'end_time': 'Tugash vaqti boshlanish vaqtidan keyin bo\'lishi kerak.'
            })
        
        # Validate class_subject belongs to class
        if self.class_subject and self.class_obj:
            if self.class_subject.class_obj_id != self.class_obj_id:
                raise ValidationError({
                    'class_subject': 'Tanlangan fan ushbu sinfga tegishli emas.'
                })
        
        # Validate room belongs to same branch
        if self.room and self.class_obj:
            if self.room.branch_id != self.class_obj.branch_id:
                raise ValidationError({
                    'room': 'Xona filialga tegishli emas.'
                })
    
    def save(self, *args, **kwargs):
        """Validate before saving."""
        self.full_clean()
        super().save(*args, **kwargs)


class LessonTopic(BaseModel):
    """Syllabus topics for a subject.
    
    Defines curriculum topics in order for each subject.
    Teachers assign topics to lesson instances.
    """
    
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='topics',
        verbose_name='Fan'
    )
    quarter = models.ForeignKey(
        Quarter,
        on_delete=models.CASCADE,
        related_name='lesson_topics',
        verbose_name='Chorak',
        null=True,
        blank=True,
        help_text='Agar chorakka bog\'langan bo\'lsa'
    )
    title = models.CharField(
        max_length=500,
        verbose_name='Mavzu nomi'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Tavsif'
    )
    position = models.PositiveIntegerField(
        default=0,
        verbose_name='Tartibi',
        help_text='Mavzuning o\'quv dasturidagi tartibi (manual ordering)'
    )
    estimated_hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=1.0,
        validators=[MinValueValidator(0.5)],
        verbose_name='Taxminiy soatlar',
        help_text='Ushbu mavzuga kerak bo\'lgan taxminiy soatlar'
    )
    
    class Meta:
        verbose_name = 'Dars mavzusi'
        verbose_name_plural = 'Dars mavzulari'
        ordering = ['subject', 'quarter', 'position', 'created_at']
        indexes = [
            models.Index(fields=['subject', 'quarter']),
            models.Index(fields=['position']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['subject', 'quarter', 'position'],
                condition=models.Q(deleted_at__isnull=True),
                name='unique_topic_position_per_subject_quarter'
            )
        ]
    
    def __str__(self):
        quarter_str = f" - {self.quarter.name}" if self.quarter else ""
        return f"{self.subject.name}{quarter_str} - {self.position}. {self.title}"


class LessonInstance(BaseModel):
    """Actual lesson instance generated from timetable.
    
    Represents a specific lesson occurrence on a specific date.
    Generated automatically from TimetableSlot or created manually.
    """
    
    class_subject = models.ForeignKey(
        ClassSubject,
        on_delete=models.CASCADE,
        related_name='lesson_instances',
        verbose_name='Sinf fani'
    )
    date = models.DateField(
        verbose_name='Sana',
        db_index=True
    )
    lesson_number = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(15)],
        verbose_name='Dars raqami',
        help_text='Kun ichidagi dars tartibi'
    )
    start_time = models.TimeField(
        verbose_name='Boshlanish vaqti'
    )
    end_time = models.TimeField(
        verbose_name='Tugash vaqti'
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lesson_instances',
        verbose_name='Xona'
    )
    topic = models.ForeignKey(
        LessonTopic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lesson_instances',
        verbose_name='Mavzu',
        help_text='Darsda o\'tilgan mavzu'
    )
    homework = models.TextField(
        blank=True,
        null=True,
        verbose_name='Uy vazifasi',
        help_text='Ushbu dars uchun uy vazifasi'
    )
    teacher_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='O\'qituvchi izohi',
        help_text='O\'qituvchining shaxsiy izoh va qaydlari'
    )
    status = models.CharField(
        max_length=20,
        choices=LessonStatus.choices,
        default=LessonStatus.PLANNED,
        verbose_name='Holati'
    )
    is_auto_generated = models.BooleanField(
        default=False,
        verbose_name='Avtomatik yaratilgan',
        help_text='Jadvaldan avtomatik yaratilganmi yoki qo\'lda qo\'shilganmi'
    )
    timetable_slot = models.ForeignKey(
        TimetableSlot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_lessons',
        verbose_name='Jadval sloti',
        help_text='Qaysi jadval slotidan yaratilgan (agar avtomatik bo\'lsa)'
    )
    
    class Meta:
        verbose_name = 'Dars'
        verbose_name_plural = 'Darslar'
        ordering = ['date', 'lesson_number', 'start_time']
        indexes = [
            models.Index(fields=['class_subject', 'date']),
            models.Index(fields=['date', 'lesson_number']),
            models.Index(fields=['status']),
            models.Index(fields=['is_auto_generated']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['class_subject', 'date', 'lesson_number'],
                condition=models.Q(deleted_at__isnull=True),
                name='unique_lesson_per_class_date_number'
            )
        ]
    
    def __str__(self):
        return (
            f"{self.class_subject.class_obj.name} - "
            f"{self.class_subject.subject.name} - "
            f"{self.date} - Dars {self.lesson_number}"
        )
    
    def clean(self):
        """Validate lesson data."""
        super().clean()
        
        # Validate times
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({
                'end_time': 'Tugash vaqti boshlanish vaqtidan keyin bo\'lishi kerak.'
            })
        
        # Validate topic belongs to subject
        if self.topic and self.class_subject:
            if self.topic.subject_id != self.class_subject.subject_id:
                raise ValidationError({
                    'topic': 'Mavzu ushbu fanga tegishli emas.'
                })
        
        # Validate room belongs to same branch
        if self.room and self.class_subject:
            if self.room.branch_id != self.class_subject.class_obj.branch_id:
                raise ValidationError({
                    'room': 'Xona filialga tegishli emas.'
                })
    
    def save(self, *args, **kwargs):
        """Validate before saving."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def mark_completed(self):
        """Mark lesson as completed."""
        self.status = LessonStatus.COMPLETED
        self.save(update_fields=['status', 'updated_at'])
    
    def mark_canceled(self):
        """Mark lesson as canceled."""
        self.status = LessonStatus.CANCELED
        self.save(update_fields=['status', 'updated_at'])
    
    @property
    def teacher(self):
        """Get the teacher for this lesson."""
        return self.class_subject.teacher
    
    @property
    def class_obj(self):
        """Get the class for this lesson."""
        return self.class_subject.class_obj
    
    @property
    def subject(self):
        """Get the subject for this lesson."""
        return self.class_subject.subject
