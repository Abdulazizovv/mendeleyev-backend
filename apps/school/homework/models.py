from django.db import models
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.common.models import BaseModel
from apps.school.schedule.models import LessonInstance
from apps.school.subjects.models import ClassSubject
from apps.school.grades.models import Assessment
from auth.profiles.models import StudentProfile
import os


def homework_file_upload_path(instance, filename):
    """Generate upload path for homework files."""
    # homework/<class_id>/<subject_id>/<homework_id>/<filename>
    return f'homework/{instance.class_subject.class_obj_id}/{instance.class_subject.subject_id}/{instance.id}/{filename}'


def submission_file_upload_path(instance, filename):
    """Generate upload path for submission files."""
    # submissions/<homework_id>/<student_id>/<filename>
    return f'submissions/{instance.homework_id}/{instance.student_id}/{filename}'


class HomeworkStatus(models.TextChoices):
    """Homework status options."""
    ACTIVE = 'active', 'Faol'
    CLOSED = 'closed', 'Yopilgan'
    ARCHIVED = 'archived', 'Arxivlangan'


class SubmissionStatus(models.TextChoices):
    """Submission status options."""
    NOT_SUBMITTED = 'not_submitted', 'Topshirilmagan'
    SUBMITTED = 'submitted', 'Topshirilgan'
    LATE = 'late', 'Kechikkan'
    GRADED = 'graded', 'Baholangan'
    RETURNED = 'returned', 'Qaytarilgan'


class Homework(BaseModel):
    """
    Homework/assignment for a class.
    
    Teachers create homework for students with optional file attachments.
    """
    
    class_subject = models.ForeignKey(
        ClassSubject,
        on_delete=models.CASCADE,
        related_name='homeworks',
        verbose_name='Sinf fani'
    )
    lesson = models.ForeignKey(
        LessonInstance,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='homeworks',
        verbose_name='Dars',
        help_text='Qaysi dars uchun vazifa (ixtiyoriy)'
    )
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='homeworks',
        verbose_name='Nazorat',
        help_text='Agar baholanishi kerak bo\'lsa'
    )
    title = models.CharField(
        max_length=500,
        verbose_name='Sarlavha'
    )
    description = models.TextField(
        verbose_name='Tavsif',
        help_text='Vazifa tavsifi va yo\'riqnoma'
    )
    assigned_date = models.DateField(
        verbose_name='Berilgan sana',
        db_index=True
    )
    due_date = models.DateField(
        verbose_name='Topshirish muddati',
        db_index=True
    )
    allow_late_submission = models.BooleanField(
        default=True,
        verbose_name='Kechiktirib topshirishga ruxsat',
        help_text='Agar true bo\'lsa, muddatdan keyin ham topshirish mumkin'
    )
    max_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Maksimal ball',
        help_text='Agar baholanishi kerak bo\'lsa'
    )
    status = models.CharField(
        max_length=20,
        choices=HomeworkStatus.choices,
        default=HomeworkStatus.ACTIVE,
        verbose_name='Holat'
    )
    attachments = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Fayllar',
        help_text='File metadata as JSON array: [{name, url, size, type}]'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Izohlar',
        help_text='O\'qituvchi uchun qo\'shimcha ma\'lumot'
    )
    
    class Meta:
        verbose_name = 'Uyga vazifa'
        verbose_name_plural = 'Uyga vazifalar'
        ordering = ['-due_date', '-assigned_date']
        indexes = [
            models.Index(fields=['class_subject', 'due_date']),
            models.Index(fields=['assigned_date', 'due_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return (
            f"{self.title} - {self.class_subject.class_obj.name} - "
            f"{self.class_subject.subject.name}"
        )
    
    def clean(self):
        """Validate homework data."""
        super().clean()
        
        # Validate due_date >= assigned_date
        if self.due_date and self.assigned_date and self.due_date < self.assigned_date:
            raise ValidationError({
                'due_date': 'Topshirish muddati berilgan sanadan oldin bo\'lmasligi kerak.'
            })
        
        # Validate lesson belongs to class_subject
        if self.lesson and self.class_subject:
            if self.lesson.class_subject_id != self.class_subject_id:
                raise ValidationError({
                    'lesson': 'Dars ushbu sinf faniga tegishli emas.'
                })
        
        # Validate assessment belongs to class_subject
        if self.assessment and self.class_subject:
            if self.assessment.class_subject_id != self.class_subject_id:
                raise ValidationError({
                    'assessment': 'Nazorat ushbu sinf faniga tegishli emas.'
                })
    
    def save(self, *args, **kwargs):
        """Validate before saving."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def is_overdue(self):
        """Check if homework is past due date."""
        return timezone.now().date() > self.due_date
    
    def get_submission_count(self):
        """Get number of submissions."""
        return self.submissions.filter(deleted_at__isnull=True).count()
    
    def get_graded_count(self):
        """Get number of graded submissions."""
        return self.submissions.filter(
            status=SubmissionStatus.GRADED,
            deleted_at__isnull=True
        ).count()
    
    def get_completion_rate(self):
        """Get percentage of students who submitted."""
        from apps.school.classes.models import ClassStudent
        
        total_students = ClassStudent.objects.filter(
            class_obj=self.class_subject.class_obj,
            is_active=True,
            deleted_at__isnull=True
        ).count()
        
        if total_students == 0:
            return 0
        
        submitted = self.submissions.filter(
            status__in=[SubmissionStatus.SUBMITTED, SubmissionStatus.GRADED],
            deleted_at__isnull=True
        ).count()
        
        return round((submitted / total_students) * 100, 2)
    
    @property
    def teacher(self):
        """Get the teacher for this homework."""
        return self.class_subject.teacher


class HomeworkSubmission(BaseModel):
    """
    Student submission for homework.
    
    Students submit homework with optional file attachments.
    """
    
    homework = models.ForeignKey(
        Homework,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name='Vazifa'
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='homework_submissions',
        verbose_name='O\'quvchi'
    )
    submission_text = models.TextField(
        blank=True,
        null=True,
        verbose_name='Topshiriq matni',
        help_text='O\'quvchi javob matni'
    )
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Topshirilgan vaqti'
    )
    status = models.CharField(
        max_length=20,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.NOT_SUBMITTED,
        verbose_name='Holat'
    )
    is_late = models.BooleanField(
        default=False,
        verbose_name='Kechikkan',
        help_text='Muddatdan keyin topshirilganmi'
    )
    score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Ball'
    )
    teacher_feedback = models.TextField(
        blank=True,
        null=True,
        verbose_name='O\'qituvchi sharhi'
    )
    graded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Baholangan vaqti'
    )
    attachments = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Fayllar',
        help_text='Submitted file metadata as JSON'
    )
    
    class Meta:
        verbose_name = 'Vazifa topshirig\'i'
        verbose_name_plural = 'Vazifa topshiriqlari'
        ordering = ['-submitted_at', '-created_at']
        indexes = [
            models.Index(fields=['homework', 'student']),
            models.Index(fields=['student', 'status']),
            models.Index(fields=['submitted_at']),
            models.Index(fields=['is_late']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['homework', 'student'],
                condition=models.Q(deleted_at__isnull=True),
                name='unique_submission_per_student'
            )
        ]
    
    def __str__(self):
        student_name = self.get_student_name()
        return (
            f"{student_name} - {self.homework.title} - "
            f"{self.get_status_display()}"
        )
    
    def get_student_name(self):
        """Get student's full name."""
        if self.student and self.student.membership:
            user = self.student.membership.user
            return f"{user.first_name} {user.last_name}"
        return "Unknown"
    
    def clean(self):
        """Validate submission data."""
        super().clean()
        
        # Validate student belongs to class
        if self.student and self.homework:
            from apps.school.classes.models import ClassStudent
            
            is_enrolled = ClassStudent.objects.filter(
                class_obj=self.homework.class_subject.class_obj,
                membership=self.student.membership,
                is_active=True,
                deleted_at__isnull=True
            ).exists()
            
            if not is_enrolled:
                raise ValidationError({
                    'student': 'O\'quvchi ushbu sinfga yozilmagan.'
                })
        
        # Validate score <= max_score
        if self.score and self.homework and self.homework.max_score:
            if self.score > self.homework.max_score:
                raise ValidationError({
                    'score': f'Ball maksimal balldan oshmasligi kerak ({self.homework.max_score})'
                })
    
    def save(self, *args, **kwargs):
        """Handle submission logic."""
        # Auto-set submitted_at if status changes to submitted
        if self.status in [SubmissionStatus.SUBMITTED, SubmissionStatus.LATE]:
            if not self.submitted_at:
                self.submitted_at = timezone.now()
            
            # Check if late
            if self.submitted_at.date() > self.homework.due_date:
                self.is_late = True
                self.status = SubmissionStatus.LATE
        
        # Auto-set graded_at if status changes to graded
        if self.status == SubmissionStatus.GRADED:
            if not self.graded_at:
                self.graded_at = timezone.now()
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def submit(self, submission_text=None, attachments=None):
        """Submit homework."""
        self.submission_text = submission_text or self.submission_text
        if attachments:
            self.attachments = attachments
        
        self.submitted_at = timezone.now()
        
        # Check if late
        if self.submitted_at.date() > self.homework.due_date:
            if not self.homework.allow_late_submission:
                raise ValidationError('Muddatdan keyin topshirishga ruxsat berilmagan.')
            self.is_late = True
            self.status = SubmissionStatus.LATE
        else:
            self.status = SubmissionStatus.SUBMITTED
        
        self.save()
    
    def grade(self, score, feedback=None):
        """Grade submission."""
        self.score = score
        self.teacher_feedback = feedback or self.teacher_feedback
        self.status = SubmissionStatus.GRADED
        self.graded_at = timezone.now()
        self.save()
    
    def return_for_revision(self, feedback):
        """Return submission for revision."""
        self.status = SubmissionStatus.RETURNED
        self.teacher_feedback = feedback
        self.save()
