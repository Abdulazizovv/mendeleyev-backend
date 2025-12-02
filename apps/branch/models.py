from django.db import models
from django.core.validators import RegexValidator
from django.conf import settings
from apps.common.models import BaseModel, BaseManager
from django.utils.text import slugify


class BranchTypes(models.TextChoices):
    SCHOOL = 'school', 'Maktab'
    CENTER = 'center', 'Markaz'

class BranchStatuses(models.TextChoices):
    PENDING = 'pending', 'Kutilmoqda'
    ACTIVE = 'active', 'Faol'
    INACTIVE = 'inactive', 'Nofaol'
    ARCHIVED = 'archived', 'Arxivlangan'


class BranchQuerySet(models.QuerySet):
    """Extra helpers for filtering branches by type and status"""

    # Type filters
    def schools(self):
        return self.filter(type=BranchTypes.SCHOOL)

    def centers(self):
        return self.filter(type=BranchTypes.CENTER)

    # Status filters (note: not to be confused with BaseModel.active which means not soft-deleted)
    def status_pending(self):
        return self.filter(status=BranchStatuses.PENDING)

    def status_active(self):
        return self.filter(status=BranchStatuses.ACTIVE)

    def status_inactive(self):
        return self.filter(status=BranchStatuses.INACTIVE)

    def status_archived(self):
        return self.filter(status=BranchStatuses.ARCHIVED)


class BranchManager(BaseManager.from_queryset(BranchQuerySet)):
    """Manager that combines soft-delete helpers and branch-specific filters"""
    pass

class Branch(BaseModel):
    name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name='Nomi',
        help_text='Filial nomi'
    )
    type = models.CharField(
        max_length=20,
        choices=BranchTypes.choices,
        default=BranchTypes.SCHOOL,
        verbose_name='Turi'
    )

    slug = models.SlugField(
        max_length=255,
        unique=True,
        verbose_name='Slug',
        help_text='Filial uchun unikal nom (slug)'
    )
    
    code = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        blank=True,
        null=True,
        verbose_name='Filial kodi',
        help_text='Filial kodi (masalan: TAS, SAM, BUK) - shaxsiy raqam generatsiyasi uchun'
    )

    status = models.CharField(
        max_length=20,
        choices=BranchStatuses.choices,
        default=BranchStatuses.PENDING,
        verbose_name='Holati'
    )

    address = models.TextField(blank=True, null=True, verbose_name='Manzil')
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[RegexValidator(r'^\+?[0-9]{7,15}$', 'Telefon raqami noto\'g\'ri formatda')],
        verbose_name='Telefon raqami'
    )
    email = models.EmailField(blank=True, null=True, verbose_name='Email')

    # Attach combined manager
    objects = BranchManager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Filial'
        verbose_name_plural = 'Filiallar'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['type']),
            models.Index(fields=['name', 'type']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_settings(self):
        """Get branch settings, create if not exists."""
        settings, created = BranchSettings.objects.get_or_create(branch=self)
        return settings


class BranchSettings(BaseModel):
    """Filial sozlamalari.
    
    Har bir filial o'z sozlamalariga ega bo'ladi.
    Masalan: dars vaqti, tanaffus vaqti, boshqa konfiguratsiyalar.
    """
    
    branch = models.OneToOneField(
        Branch,
        on_delete=models.CASCADE,
        related_name='settings',
        verbose_name='Filial'
    )
    
    # Dars jadvali sozlamalari
    lesson_duration_minutes = models.IntegerField(
        default=45,
        verbose_name='Dars davomiyligi (daqiqa)',
        help_text='Har bir darsning davomiyligi daqiqada'
    )
    break_duration_minutes = models.IntegerField(
        default=10,
        verbose_name='Tanaffus davomiyligi (daqiqa)',
        help_text='Darslar orasidagi tanaffus davomiyligi'
    )
    school_start_time = models.TimeField(
        default='08:00',
        verbose_name='Maktab boshlanish vaqti',
        help_text='Kunlik darslar boshlanish vaqti'
    )
    school_end_time = models.TimeField(
        default='17:00',
        verbose_name='Maktab tugash vaqti',
        help_text='Kunlik darslar tugash vaqti'
    )
    
    # Akademik sozlamalar
    academic_year_start_month = models.IntegerField(
        default=9,
        choices=[(i, f'{i}-oy') for i in range(1, 13)],
        verbose_name='Akademik yil boshlanish oyi',
        help_text='Akademik yil qaysi oyda boshlanadi (1-12)'
    )
    academic_year_end_month = models.IntegerField(
        default=6,
        choices=[(i, f'{i}-oy') for i in range(1, 13)],
        verbose_name='Akademik yil tugash oyi',
        help_text='Akademik yil qaysi oyda tugaydi (1-12)'
    )
    
    # Moliya sozlamalari
    currency = models.CharField(
        max_length=10,
        default='UZS',
        verbose_name='Valyuta',
        help_text='Filial valyutasi (masalan: UZS, USD)'
    )
    currency_symbol = models.CharField(
        max_length=5,
        default='so\'m',
        verbose_name='Valyuta belgisi',
        help_text='Valyuta belgisi (masalan: so\'m, $)'
    )
    
    # Boshqa sozlamalar (JSON formatida)
    additional_settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Qo\'shimcha sozlamalar',
        help_text='Qo\'shimcha sozlamalar JSON formatida. Masalan: {"max_students_per_class": 30, "grading_system": "5"}'
    )
    
    class Meta:
        verbose_name = 'Filial sozlamalari'
        verbose_name_plural = 'Filial sozlamalari'
        indexes = [
            models.Index(fields=['branch']),
        ]
    
    def __str__(self):
        return f"Sozlamalar: {self.branch.name}"
    
    def save(self, *args, **kwargs):
        """Auto-create settings when branch is created."""
        if not self.pk:
            # Ensure branch exists
            if not self.branch_id:
                raise ValueError("Branch must be set before saving settings")
        super().save(*args, **kwargs)


class BranchRole(models.TextChoices):
    """Role choices for branch memberships."""
    SUPER_ADMIN = 'super_admin', 'Super Admin'
    BRANCH_ADMIN = 'branch_admin', 'Branch Admin'
    TEACHER = 'teacher', 'Teacher'
    STUDENT = 'student', 'Student'
    PARENT = 'parent', 'Parent'
    OTHER = 'other', 'Boshqa xodim'


class SalaryType(models.TextChoices):
    """Salary calculation types for employees."""
    MONTHLY = 'monthly', 'Oylik (aniq belgilangan)'
    HOURLY = 'hourly', 'Soatlik'
    PER_LESSON = 'per_lesson', 'Dars uchun'


class Role(BaseModel):
    """Role model with permissions.
    
    Roles can be branch-specific or global (branch=None).
    Permissions are stored as JSON for flexibility.
    
    Note: Salary is now stored in BranchMembership, not in Role.
    This allows each employee to have a different salary even with the same role.
    """
    
    name = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name='Rol nomi',
        help_text='Rol nomi (masalan: Director, Teacher, Guard)'
    )
    branch = models.ForeignKey(
        'branch.Branch',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='roles',
        verbose_name='Filial',
        help_text='Agar bo\'sh bo\'lsa, bu umumiy rol (barcha filiallar uchun)'
    )
    
    # Permissions stored as JSON
    permissions = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Ruxsatlar',
        help_text='Ruxsatlar JSON formatida. Masalan: {"academic": ["view_grades", "edit_grades"], "finance": ["view_payments"]}'
    )
    
    # Additional fields
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='Tavsif',
        help_text='Rol haqida qo\'shimcha ma\'lumot'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Faol',
        help_text='Bu rol faolmi?'
    )

    class Meta:
        verbose_name = 'Rol'
        verbose_name_plural = 'Rollar'
        unique_together = [('name', 'branch')]  # Same role name can exist in different branches
        indexes = [
            models.Index(fields=['branch', 'is_active']),
            models.Index(fields=['name']),
        ]

    def __str__(self) -> str:
        branch_name = self.branch.name if self.branch else "Umumiy"
        return f"{self.name} @ {branch_name}"


class BranchMembership(BaseModel):
    """Canonical membership model linking User, Branch, and Role.
    
    This is the primary model for managing user-branch relationships with roles.
    Replaces the deprecated UserBranch model.
    
    Each membership has a balance for salary management.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='branch_memberships',
        verbose_name='Foydalanuvchi'
    )
    branch = models.ForeignKey(
        'branch.Branch',
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name='Filial'
    )
    
    # Role can be either a string (legacy) or ForeignKey to Role model
    role = models.CharField(
        max_length=32,
        choices=BranchRole.choices,
        verbose_name='Rol (legacy)',
        help_text='Eski tizim bilan moslik uchun. role_ref ustunlik beradi.'
    )
    role_ref = models.ForeignKey(
        'branch.Role',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='memberships',
        verbose_name='Rol (yangi)',
        help_text='Rol modeliga havola. Agar belgilansa, role maydoni e\'tiborsiz qoldiriladi.'
    )
    
    title = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Optional local title (e.g., Physics Teacher)",
        verbose_name='Lavozim'
    )
    
    # Salary configuration - stored per membership, not per role
    salary_type = models.CharField(
        max_length=20,
        choices=SalaryType.choices,
        default=SalaryType.MONTHLY,
        verbose_name='Maosh turi',
        help_text='Maosh qanday hisoblanadi: oylik, soatlik yoki dars uchun'
    )
    
    # Salary fields - depends on salary_type
    monthly_salary = models.IntegerField(
        default=0,
        verbose_name='Oylik maosh',
        help_text='Oylik maosh (so\'m, butun son). salary_type="monthly" bo\'lganda ishlatiladi.'
    )
    hourly_rate = models.IntegerField(
        default=0,
        null=True,
        blank=True,
        verbose_name='Soatlik stavka',
        help_text='Soatlik stavka (so\'m, butun son). salary_type="hourly" bo\'lganda ishlatiladi.'
    )
    per_lesson_rate = models.IntegerField(
        default=0,
        null=True,
        blank=True,
        verbose_name='Dars uchun stavka',
        help_text='Har bir dars uchun stavka (so\'m, butun son). salary_type="per_lesson" bo\'lganda ishlatiladi.'
    )
    
    # Balance for salary management
    balance = models.IntegerField(
        default=0,
        verbose_name='Balans',
        help_text='Xodimning balansi (so\'m, butun son). Ish haqini ko\'rish va boshqarish uchun.'
    )

    class Meta:
        unique_together = ("user", "branch")
        verbose_name = "Filial a'zoligi"
        verbose_name_plural = "Filial a'zoliklari"
        indexes = [
            models.Index(fields=["branch", "role"]),
            models.Index(fields=["user", "role"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.phone_number} @ {self.branch.name} ({self.get_role_display()})"

    @classmethod
    def for_user_and_branch(cls, user_id, branch_id):
        """Get membership for a specific user and branch."""
        return cls.objects.filter(user_id=user_id, branch_id=branch_id).first()

    @classmethod
    def has_role(cls, user_id, branch_id, roles: list[str] | tuple[str, ...] | None = None) -> bool:
        """Check if user has a specific role (or any role) in a branch."""
        qs = cls.objects.filter(user_id=user_id, branch_id=branch_id)
        if roles:
            qs = qs.filter(role__in=list(roles))
        return qs.exists()
    
    def get_effective_role(self):
        """Get effective role - prefer role_ref over legacy role field."""
        if self.role_ref:
            return self.role_ref.name
        return self.role
    
    def get_salary(self):
        """Get current salary based on salary_type.
        
        Returns:
            - For monthly: monthly_salary
            - For hourly: hourly_rate (per hour)
            - For per_lesson: per_lesson_rate (per lesson)
        """
        if self.salary_type == SalaryType.MONTHLY:
            return self.monthly_salary
        elif self.salary_type == SalaryType.HOURLY:
            return self.hourly_rate or 0
        elif self.salary_type == SalaryType.PER_LESSON:
            return self.per_lesson_rate or 0
        return 0
    
    def get_salary_display(self):
        """Get human-readable salary information."""
        if self.salary_type == SalaryType.MONTHLY:
            return f"{self.monthly_salary:,} so'm/oy"
        elif self.salary_type == SalaryType.HOURLY:
            return f"{self.hourly_rate or 0:,} so'm/soat"
        elif self.salary_type == SalaryType.PER_LESSON:
            return f"{self.per_lesson_rate or 0:,} so'm/dars"
        return "Maosh belgilanmagan"
    
    def add_to_balance(self, amount: int):
        """Add amount to balance."""
        self.balance += amount
        self.save(update_fields=['balance', 'updated_at'])
    
    def subtract_from_balance(self, amount: int):
        """Subtract amount from balance."""
        if self.balance >= amount:
            self.balance -= amount
            self.save(update_fields=['balance', 'updated_at'])
            return True
        return False