from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.common.models import BaseModel
from apps.school.schedule.models import LessonInstance
from apps.school.subjects.models import ClassSubject
from auth.profiles.models import StudentProfile
from datetime import timedelta


class AttendanceStatus(models.TextChoices):
    """Student attendance status options."""
    PRESENT = 'present', 'Keldi'
    ABSENT = 'absent', 'Kelmadi'
    LATE = 'late', 'Kechikdi'
    EXCUSED = 'excused', 'Sababli'
    SICK = 'sick', 'Kasal'


class LessonAttendance(BaseModel):
    """
    Attendance tracking for a specific lesson.
    
    Container for all student attendance records for a single lesson.
    Stores metadata about attendance marking.
    """
    
    lesson = models.ForeignKey(
        LessonInstance,
        on_delete=models.CASCADE,
        related_name='attendances',
        null=True,
        blank=True,
        verbose_name='Dars',
        help_text='Bog\'langan dars (agar mavjud bo\'lsa)'
    )
    class_subject = models.ForeignKey(
        ClassSubject,
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name='Sinf fani',
        help_text='Davomat uchun sinf fani'
    )
    date = models.DateField(
        verbose_name='Sana',
        db_index=True,
        help_text='Davomat olingan sana'
    )
    lesson_number = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Dars raqami',
        help_text='Kun ichidagi dars tartibi'
    )
    is_locked = models.BooleanField(
        default=False,
        verbose_name='Bloklangan',
        help_text='Agar true bo\'lsa, davomat o\'zgartirilishi mumkin emas'
    )
    locked_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Bloklangan vaqti',
        help_text='Davomat qachon bloklangan'
    )
    locked_by = models.ForeignKey(
        'branch.BranchMembership',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='locked_attendances',
        verbose_name='Bloklagan',
        help_text='Davomatni bloklagan xodim'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Izohlar',
        help_text='Ushbu dars uchun umumiy izohlar'
    )
    
    class Meta:
        verbose_name = 'Davomat'
        verbose_name_plural = 'Davomatlar'
        ordering = ['-date', '-lesson_number']
        indexes = [
            models.Index(fields=['class_subject', 'date']),
            models.Index(fields=['date', 'lesson_number']),
            models.Index(fields=['lesson']),
            models.Index(fields=['is_locked']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['class_subject', 'date', 'lesson_number'],
                condition=models.Q(deleted_at__isnull=True),
                name='unique_attendance_per_class_date_lesson'
            )
        ]
    
    def __str__(self):
        return (
            f"{self.class_subject.class_obj.name} - "
            f"{self.class_subject.subject.name} - "
            f"{self.date} - Dars {self.lesson_number}"
        )
    
    def clean(self):
        """Validate attendance data."""
        super().clean()
        
        # If lesson is provided, sync data from lesson
        if self.lesson:
            if self.lesson.class_subject_id != self.class_subject_id:
                raise ValidationError({
                    'lesson': 'Dars ushbu sinf faniga tegishli emas.'
                })
            # Sync date and lesson_number from lesson if not set
            if not self.date:
                self.date = self.lesson.date
            if not self.lesson_number or self.lesson_number == 1:
                self.lesson_number = self.lesson.lesson_number
    
    def save(self, *args, **kwargs):
        """Validate before saving."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def lock(self, locked_by=None):
        """Lock attendance to prevent further edits."""
        if not self.is_locked:
            self.is_locked = True
            self.locked_at = timezone.now()
            self.locked_by = locked_by
            self.save(update_fields=['is_locked', 'locked_at', 'locked_by', 'updated_at'])
    
    def unlock(self):
        """Unlock attendance to allow edits (admin override)."""
        if self.is_locked:
            self.is_locked = False
            self.locked_at = None
            self.locked_by = None
            self.save(update_fields=['is_locked', 'locked_at', 'locked_by', 'updated_at'])
    
    def get_present_count(self):
        """Get number of present students."""
        return self.records.filter(
            status=AttendanceStatus.PRESENT,
            deleted_at__isnull=True
        ).count()
    
    def get_absent_count(self):
        """Get number of absent students."""
        return self.records.filter(
            status=AttendanceStatus.ABSENT,
            deleted_at__isnull=True
        ).count()
    
    def get_late_count(self):
        """Get number of late students."""
        return self.records.filter(
            status=AttendanceStatus.LATE,
            deleted_at__isnull=True
        ).count()
    
    def get_total_count(self):
        """Get total number of students."""
        return self.records.filter(deleted_at__isnull=True).count()
    
    @property
    def teacher(self):
        """Get the teacher for this attendance."""
        return self.class_subject.teacher
    
    @property
    def class_obj(self):
        """Get the class for this attendance."""
        return self.class_subject.class_obj


class StudentAttendanceRecord(BaseModel):
    """
    Individual student attendance record.
    
    Tracks attendance status for a specific student in a specific lesson.
    """
    
    attendance = models.ForeignKey(
        LessonAttendance,
        on_delete=models.CASCADE,
        related_name='records',
        verbose_name='Davomat'
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        verbose_name='O\'quvchi'
    )
    status = models.CharField(
        max_length=20,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PRESENT,
        verbose_name='Holat'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Izoh',
        help_text='Ushbu o\'quvchi uchun maxsus izoh'
    )
    marked_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Belgilangan vaqti'
    )
    
    class Meta:
        verbose_name = 'O\'quvchi davomat yozuvi'
        verbose_name_plural = 'O\'quvchi davomat yozuvlari'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['attendance', 'student']),
            models.Index(fields=['student', 'status']),
            models.Index(fields=['marked_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['attendance', 'student'],
                condition=models.Q(deleted_at__isnull=True),
                name='unique_attendance_record_per_student'
            )
        ]
    
    def __str__(self):
        student_name = self.get_student_name()
        return f"{student_name} - {self.get_status_display()} - {self.attendance.date}"
    
    def get_student_name(self):
        """Get student's full name."""
        if self.student and self.student.membership:
            user = self.student.membership.user
            return f"{user.first_name} {user.last_name}"
        return "Unknown"
    
    def clean(self):
        """Validate record data."""
        super().clean()
        
        # Check if attendance is locked
        if self.attendance and self.attendance.is_locked:
            # Allow save if this is just an update (pk exists) and not a status change
            if self.pk:
                original = StudentAttendanceRecord.objects.get(pk=self.pk)
                if original.status != self.status:
                    raise ValidationError(
                        'Davomat bloklangan. Holatni o\'zgartirish mumkin emas.'
                    )
            else:
                # New record on locked attendance - only allow if admin override
                raise ValidationError(
                    'Davomat bloklangan. Yangi yozuv qo\'shish mumkin emas.'
                )
        
        # Validate student belongs to class
        if self.student and self.attendance:
            from apps.school.classes.models import ClassStudent
            
            # Check if student is enrolled in this class
            is_enrolled = ClassStudent.objects.filter(
                class_obj=self.attendance.class_obj,
                membership=self.student.membership,
                is_active=True,
                deleted_at__isnull=True
            ).exists()
            
            if not is_enrolled:
                raise ValidationError({
                    'student': 'O\'quvchi ushbu sinfga yozilmagan.'
                })
    
    def save(self, *args, **kwargs):
        """Validate before saving."""
        self.full_clean()
        super().save(*args, **kwargs)


class AttendanceStatistics(BaseModel):
    """
    Cached attendance statistics for performance.
    
    Stores aggregated attendance data per student/class/quarter.
    Updated periodically or on-demand.
    """
    
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='attendance_statistics',
        null=True,
        blank=True,
        verbose_name='O\'quvchi',
        help_text='Agar ma\'lum bir o\'quvchi uchun bo\'lsa'
    )
    class_subject = models.ForeignKey(
        ClassSubject,
        on_delete=models.CASCADE,
        related_name='attendance_statistics',
        null=True,
        blank=True,
        verbose_name='Sinf fani',
        help_text='Agar ma\'lum bir fan uchun bo\'lsa'
    )
    start_date = models.DateField(
        verbose_name='Boshlanish sanasi'
    )
    end_date = models.DateField(
        verbose_name='Tugash sanasi'
    )
    total_lessons = models.PositiveIntegerField(
        default=0,
        verbose_name='Jami darslar'
    )
    present_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Kelgan darslar'
    )
    absent_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Kelmagan darslar'
    )
    late_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Kechikkan darslar'
    )
    excused_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Sababli darslar'
    )
    attendance_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name='Davomat foizi',
        help_text='(present + late + excused) / total * 100'
    )
    last_calculated = models.DateTimeField(
        auto_now=True,
        verbose_name='Oxirgi hisoblash vaqti'
    )
    
    class Meta:
        verbose_name = 'Davomat statistikasi'
        verbose_name_plural = 'Davomat statistikalari'
        ordering = ['-last_calculated']
        indexes = [
            models.Index(fields=['student', 'class_subject']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['last_calculated']),
        ]
    
    def __str__(self):
        if self.student:
            return f"Statistika: {self.get_student_name()} - {self.start_date} - {self.end_date}"
        elif self.class_subject:
            return f"Statistika: {self.class_subject} - {self.start_date} - {self.end_date}"
        return f"Statistika: {self.start_date} - {self.end_date}"
    
    def get_student_name(self):
        """Get student's full name."""
        if self.student and self.student.membership:
            user = self.student.membership.user
            return f"{user.first_name} {user.last_name}"
        return "Unknown"
    
    def calculate(self):
        """Calculate and update statistics."""
        # Build query
        query = StudentAttendanceRecord.objects.filter(
            attendance__date__gte=self.start_date,
            attendance__date__lte=self.end_date,
            deleted_at__isnull=True
        )
        
        if self.student:
            query = query.filter(student=self.student)
        
        if self.class_subject:
            query = query.filter(attendance__class_subject=self.class_subject)
        
        # Count by status
        from django.db.models import Count, Q
        
        stats = query.aggregate(
            total=Count('id'),
            present=Count('id', filter=Q(status=AttendanceStatus.PRESENT)),
            absent=Count('id', filter=Q(status=AttendanceStatus.ABSENT)),
            late=Count('id', filter=Q(status=AttendanceStatus.LATE)),
            excused=Count('id', filter=Q(status=AttendanceStatus.EXCUSED)),
        )
        
        self.total_lessons = stats['total']
        self.present_count = stats['present']
        self.absent_count = stats['absent']
        self.late_count = stats['late']
        self.excused_count = stats['excused']
        
        # Calculate attendance rate
        if self.total_lessons > 0:
            attended = self.present_count + self.late_count + self.excused_count
            self.attendance_rate = round((attended / self.total_lessons) * 100, 2)
        else:
            self.attendance_rate = 0.00
        
        self.save()
