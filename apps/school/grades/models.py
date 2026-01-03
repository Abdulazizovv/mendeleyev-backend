from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Avg, Sum, Count, Q
from apps.common.models import BaseModel
from apps.branch.models import Branch
from apps.school.subjects.models import ClassSubject
from apps.school.academic.models import Quarter
from apps.school.schedule.models import LessonInstance
from auth.profiles.models import StudentProfile


class AssessmentType(BaseModel):
    """
    Types of assessments (oral, homework, quiz, exam, etc.).
    
    Configured per branch for flexibility across different schools.
    """
    
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='assessment_types',
        verbose_name='Filial'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Nomi',
        help_text='Nazorat turi nomi. Masalan: Og\'zaki, Uyga vazifa, Test, Nazorat ishi'
    )
    code = models.CharField(
        max_length=50,
        verbose_name='Kod',
        help_text='Unikal kod. Masalan: oral, homework, quiz, exam'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Tavsif'
    )
    default_max_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=5.00,
        validators=[MinValueValidator(0)],
        verbose_name='Standart maksimal ball',
        help_text='Ushbu nazorat turi uchun standart maksimal ball'
    )
    default_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00,
        validators=[MinValueValidator(0)],
        verbose_name='Standart og\'irligi',
        help_text='Yakuniy bahoga hissa (masalan: imtihon = 0.40, test = 0.20)'
    )
    color = models.CharField(
        max_length=7,
        default='#3498db',
        verbose_name='Rang',
        help_text='HEX formatida rang. Masalan: #3498db'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Faol'
    )
    
    class Meta:
        verbose_name = 'Nazorat turi'
        verbose_name_plural = 'Nazorat turlari'
        ordering = ['branch', 'name']
        indexes = [
            models.Index(fields=['branch', 'is_active']),
            models.Index(fields=['code']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['branch', 'code'],
                condition=models.Q(deleted_at__isnull=True),
                name='unique_assessment_type_per_branch'
            )
        ]
    
    def __str__(self):
        return f"{self.name} ({self.branch.name})"


class Assessment(BaseModel):
    """
    Individual assessment/exam instance for a class subject.
    
    Defines when and how students will be assessed on a topic.
    """
    
    class_subject = models.ForeignKey(
        ClassSubject,
        on_delete=models.CASCADE,
        related_name='assessments',
        verbose_name='Sinf fani'
    )
    assessment_type = models.ForeignKey(
        AssessmentType,
        on_delete=models.PROTECT,
        related_name='assessments',
        verbose_name='Nazorat turi'
    )
    lesson = models.ForeignKey(
        LessonInstance,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assessments',
        verbose_name='Dars',
        help_text='Nazorat qaysi darsda o\'tkazilgan (ixtiyoriy)'
    )
    quarter = models.ForeignKey(
        Quarter,
        on_delete=models.CASCADE,
        related_name='assessments',
        verbose_name='Chorak'
    )
    title = models.CharField(
        max_length=255,
        verbose_name='Nomi',
        help_text='Nazorat nomi. Masalan: "1-chorak yakuniy nazorat ishi"'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Tavsif'
    )
    date = models.DateField(
        verbose_name='Sana',
        db_index=True
    )
    max_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Maksimal ball'
    )
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00,
        validators=[MinValueValidator(0)],
        verbose_name='Og\'irligi',
        help_text='Yakuniy bahoga hissa. 0 bo\'lsa, faqat ma\'lumot uchun'
    )
    is_locked = models.BooleanField(
        default=False,
        verbose_name='Bloklangan',
        help_text='Agar true bo\'lsa, baholar o\'zgartirilishi mumkin emas'
    )
    locked_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Bloklangan vaqti'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Izohlar'
    )
    
    class Meta:
        verbose_name = 'Nazorat'
        verbose_name_plural = 'Nazoratlar'
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['class_subject', 'quarter']),
            models.Index(fields=['date']),
            models.Index(fields=['is_locked']),
        ]
    
    def __str__(self):
        return (
            f"{self.title} - {self.class_subject.class_obj.name} - "
            f"{self.class_subject.subject.name} - {self.date}"
        )
    
    def clean(self):
        """Validate assessment data."""
        super().clean()
        
        # Validate quarter belongs to class subject's academic year
        if self.quarter and self.class_subject:
            if self.quarter.academic_year_id != self.class_subject.class_obj.academic_year_id:
                raise ValidationError({
                    'quarter': 'Chorak sinf akademik yiliga tegishli emas.'
                })
        
        # Validate assessment type belongs to same branch
        if self.assessment_type and self.class_subject:
            if self.assessment_type.branch_id != self.class_subject.class_obj.branch_id:
                raise ValidationError({
                    'assessment_type': 'Nazorat turi filialga tegishli emas.'
                })
        
        # Validate lesson belongs to class subject
        if self.lesson and self.class_subject:
            if self.lesson.class_subject_id != self.class_subject_id:
                raise ValidationError({
                    'lesson': 'Dars ushbu sinf faniga tegishli emas.'
                })
    
    def save(self, *args, **kwargs):
        """Validate before saving."""
        # Auto-set max_score and weight from assessment_type if not provided
        if not self.max_score and self.assessment_type:
            self.max_score = self.assessment_type.default_max_score
        if self.weight is None and self.assessment_type:
            self.weight = self.assessment_type.default_weight
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def lock(self):
        """Lock assessment to prevent further grade edits."""
        if not self.is_locked:
            self.is_locked = True
            self.locked_at = timezone.now()
            self.save(update_fields=['is_locked', 'locked_at', 'updated_at'])
    
    def unlock(self):
        """Unlock assessment to allow grade edits (admin override)."""
        if self.is_locked:
            self.is_locked = False
            self.locked_at = None
            self.save(update_fields=['is_locked', 'locked_at', 'updated_at'])
    
    def get_average_score(self):
        """Get average score for this assessment."""
        return self.grades.filter(
            deleted_at__isnull=True
        ).aggregate(avg=Avg('score'))['avg'] or 0
    
    def get_completion_rate(self):
        """Get percentage of students who have been graded."""
        from apps.school.classes.models import ClassStudent
        
        total_students = ClassStudent.objects.filter(
            class_obj=self.class_subject.class_obj,
            is_active=True,
            deleted_at__isnull=True
        ).count()
        
        if total_students == 0:
            return 0
        
        graded_count = self.grades.filter(deleted_at__isnull=True).count()
        return round((graded_count / total_students) * 100, 2)
    
    @property
    def teacher(self):
        """Get the teacher for this assessment."""
        return self.class_subject.teacher


class Grade(BaseModel):
    """
    Individual student grade for an assessment.
    
    Stores the score and provides calculated and final score options.
    """
    
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name='grades',
        verbose_name='Nazorat'
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='grades',
        verbose_name='O\'quvchi'
    )
    score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Ball',
        help_text='O\'quvchi olgan ball'
    )
    calculated_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Hisoblangan ball',
        help_text='Avtomatik hisoblangan ball (scale conversion)'
    )
    final_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Yakuniy ball',
        help_text='Yakuniy ball (manual override yoki calculated_score)'
    )
    override_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name='O\'zgartirish sababi',
        help_text='Agar o\'qituvchi bahoni qo\'lda o\'zgartirgan bo\'lsa, sabab'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Izoh',
        help_text='O\'qituvchining izohi'
    )
    graded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Baholangan vaqti'
    )
    
    class Meta:
        verbose_name = 'Baho'
        verbose_name_plural = 'Baholar'
        ordering = ['-graded_at']
        indexes = [
            models.Index(fields=['assessment', 'student']),
            models.Index(fields=['student', 'assessment']),
            models.Index(fields=['graded_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['assessment', 'student'],
                condition=models.Q(deleted_at__isnull=True),
                name='unique_grade_per_student_assessment'
            )
        ]
    
    def __str__(self):
        student_name = self.get_student_name()
        return (
            f"{student_name} - {self.assessment.title} - "
            f"{self.score}/{self.assessment.max_score}"
        )
    
    def get_student_name(self):
        """Get student's full name."""
        if self.student and self.student.membership:
            user = self.student.membership.user
            return f"{user.first_name} {user.last_name}"
        return "Unknown"
    
    def clean(self):
        """Validate grade data."""
        super().clean()
        
        # Check if assessment is locked
        if self.assessment and self.assessment.is_locked:
            # Allow update if it's just a note change
            if self.pk:
                original = Grade.objects.get(pk=self.pk)
                if original.score != self.score or original.final_score != self.final_score:
                    raise ValidationError(
                        'Nazorat bloklangan. Bahoni o\'zgartirish mumkin emas.'
                    )
        
        # Validate score <= max_score
        if self.assessment and self.score > self.assessment.max_score:
            raise ValidationError({
                'score': f'Ball maksimal balldan oshmasligi kerak ({self.assessment.max_score})'
            })
        
        # Validate student belongs to class
        if self.student and self.assessment:
            from apps.school.classes.models import ClassStudent
            
            is_enrolled = ClassStudent.objects.filter(
                class_obj=self.assessment.class_subject.class_obj,
                membership=self.student.membership,
                is_active=True,
                deleted_at__isnull=True
            ).exists()
            
            if not is_enrolled:
                raise ValidationError({
                    'student': 'O\'quvchi ushbu sinfga yozilmagan.'
                })
    
    def save(self, *args, **kwargs):
        """Calculate scores before saving."""
        # Auto-calculate: normalize to 5-point scale (or branch standard)
        if self.assessment:
            # Calculate percentage
            percentage = (self.score / self.assessment.max_score) * 100
            
            # Convert to 5-point scale (standard Uzbekistan grading)
            if percentage >= 85:
                self.calculated_score = 5.0
            elif percentage >= 70:
                self.calculated_score = 4.0
            elif percentage >= 55:
                self.calculated_score = 3.0
            elif percentage >= 40:
                self.calculated_score = 2.0
            else:
                self.calculated_score = 1.0
            
            # Set final_score = calculated_score if not overridden
            if self.final_score is None:
                self.final_score = self.calculated_score
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def override_final_score(self, new_score, reason):
        """Override the final score with manual adjustment."""
        self.final_score = new_score
        self.override_reason = reason
        self.save(update_fields=['final_score', 'override_reason', 'updated_at'])
    
    def get_percentage(self):
        """Get score as percentage."""
        if self.assessment and self.assessment.max_score > 0:
            return round((self.score / self.assessment.max_score) * 100, 2)
        return 0


class QuarterGrade(BaseModel):
    """
    Calculated quarter grade for a student in a subject.
    
    Cached/computed grade based on all assessments in the quarter.
    Updated when grades change or on-demand.
    """
    
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='quarter_grades',
        verbose_name='O\'quvchi'
    )
    class_subject = models.ForeignKey(
        ClassSubject,
        on_delete=models.CASCADE,
        related_name='quarter_grades',
        verbose_name='Sinf fani'
    )
    quarter = models.ForeignKey(
        Quarter,
        on_delete=models.CASCADE,
        related_name='quarter_grades',
        verbose_name='Chorak'
    )
    calculated_grade = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Hisoblangan baho',
        help_text='O\'rtacha og\'irlikli baho (weighted average)'
    )
    final_grade = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Yakuniy baho',
        help_text='Yakuniy baho (manual override yoki calculated_grade)'
    )
    override_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name='O\'zgartirish sababi'
    )
    is_locked = models.BooleanField(
        default=False,
        verbose_name='Bloklangan',
        help_text='Chorak tugagach bloklash'
    )
    locked_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Bloklangan vaqti'
    )
    last_calculated = models.DateTimeField(
        auto_now=True,
        verbose_name='Oxirgi hisoblash vaqti'
    )
    
    class Meta:
        verbose_name = 'Chorak bahosi'
        verbose_name_plural = 'Chorak baholari'
        ordering = ['-quarter__start_date']
        indexes = [
            models.Index(fields=['student', 'class_subject', 'quarter']),
            models.Index(fields=['last_calculated']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'class_subject', 'quarter'],
                condition=models.Q(deleted_at__isnull=True),
                name='unique_quarter_grade_per_student'
            )
        ]
    
    def __str__(self):
        student_name = self.get_student_name()
        return (
            f"{student_name} - {self.class_subject.subject.name} - "
            f"{self.quarter.name} - {self.final_grade or self.calculated_grade}"
        )
    
    def get_student_name(self):
        """Get student's full name."""
        if self.student and self.student.membership:
            user = self.student.membership.user
            return f"{user.first_name} {user.last_name}"
        return "Unknown"
    
    def calculate(self):
        """Calculate weighted average grade from all assessments."""
        # Get all grades for this student in this quarter
        grades = Grade.objects.filter(
            student=self.student,
            assessment__class_subject=self.class_subject,
            assessment__quarter=self.quarter,
            deleted_at__isnull=True
        ).select_related('assessment')
        
        if not grades.exists():
            self.calculated_grade = 0
            if self.final_grade is None:
                self.final_grade = 0
            self.save()
            return
        
        # Calculate weighted average
        total_weight = 0
        weighted_sum = 0
        
        for grade in grades:
            weight = grade.assessment.weight
            final_score = grade.final_score or grade.calculated_score
            
            weighted_sum += final_score * weight
            total_weight += weight
        
        if total_weight > 0:
            self.calculated_grade = round(weighted_sum / total_weight, 2)
        else:
            # If all weights are 0, use simple average
            self.calculated_grade = round(
                grades.aggregate(avg=Avg('final_score'))['avg'] or 0,
                2
            )
        
        # Set final_grade = calculated_grade if not overridden
        if self.final_grade is None:
            self.final_grade = self.calculated_grade
        
        self.save()
    
    def lock(self):
        """Lock quarter grade after quarter ends."""
        if not self.is_locked:
            self.is_locked = True
            self.locked_at = timezone.now()
            self.save(update_fields=['is_locked', 'locked_at', 'updated_at'])
    
    def unlock(self):
        """Unlock quarter grade (admin override)."""
        if self.is_locked:
            self.is_locked = False
            self.locked_at = None
            self.save(update_fields=['is_locked', 'locked_at', 'updated_at'])
