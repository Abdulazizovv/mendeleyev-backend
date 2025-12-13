from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
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


class EmploymentType(models.TextChoices):
    """Employment types for staff members."""
    FULL_TIME = 'full_time', "To'liq stavka"
    PART_TIME = 'part_time', 'Yarim stavka'
    CONTRACT = 'contract', 'Shartnoma asosida'


class Role(BaseModel):
    """Role model with permissions and salary guidance.
    
    Unified role model for all staff types (teachers, admins, guards, cooks, etc).
    Roles can be branch-specific or global (branch=None).
    Permissions are stored as JSON for flexibility.
    
    Examples:
    - Teacher: permissions={'academic': ['view_grades', 'edit_attendance']}
    - Guard: permissions={'security': ['view_schedule', 'access_gates']}
    - Cook: permissions={'kitchen': ['view_menu', 'manage_inventory']}
    - Branch Admin: permissions={'admin': ['manage_staff', 'view_reports']}
    
    Note: Salary is stored in BranchMembership, not in Role.
    salary_range_min/max are optional guidance values only.
    """
    
    name = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name='Rol nomi',
        help_text='Rol nomi (masalan: O\'qituvchi, Qorovul, Oshpaz, Direktor)'
    )
    code = models.CharField(
        max_length=50,
        db_index=True,
        blank=True,
        default='',
        verbose_name='Kod',
        help_text='Unikal kod (masalan: teacher, guard, cook, director)'
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
    
    # Salary range guidance (optional, for HR purposes)
    salary_range_min = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Minimal maosh (yo\'riqnoma)',
        help_text='Tavsiya etilgan minimal maosh (so\'m). Faqat yo\'riqnoma - haqiqiy maosh BranchMembership\'da.'
    )
    salary_range_max = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Maksimal maosh (yo\'riqnoma)',
        help_text='Tavsiya etilgan maksimal maosh (so\'m). Faqat yo\'riqnoma - haqiqiy maosh BranchMembership\'da.'
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
            models.Index(fields=['code']),
        ]

    def __str__(self) -> str:
        branch_name = self.branch.name if self.branch else "Umumiy"
        return f"{self.name} @ {branch_name}"
    
    def get_memberships_count(self):
        """Get count of active memberships using this role."""
        return self.role_memberships.filter(deleted_at__isnull=True).count()


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
        related_name='role_memberships',
        verbose_name='Rol (to\'liq)',
        help_text='Role modeliga havola. Barcha xodim turlari uchun: o\'qituvchi, admin, oshpaz, qorovul va boshqalar.'
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
    
    # Employment tracking fields (faqat staff uchun)
    hire_date = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name='Ishga olish sanasi',
        help_text='Xodim ishga qabul qilingan sana'
    )
    
    termination_date = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name='Ishdan chiqish sanasi',
        help_text='Xodim ishdan chiqqan sana. Bo\'sh bo\'lsa - hali ishlamoqda.'
    )
    
    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME,
        blank=True,
        verbose_name='Bandlik turi',
        help_text='To\'liq stavka, yarim stavka yoki shartnoma'
    )
    
    # Personal information (faqat staff uchun)
    passport_serial = models.CharField(
        max_length=2,
        blank=True,
        verbose_name='Pasport seriyasi',
        help_text='Masalan: AA'
    )
    
    passport_number = models.CharField(
        max_length=7,
        blank=True,
        verbose_name='Pasport raqami',
        help_text='Masalan: 1234567'
    )
    
    address = models.TextField(
        blank=True,
        verbose_name='Manzil',
        help_text='Yashash manzili'
    )
    
    emergency_contact = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Favqulodda aloqa',
        help_text='Favqulodda vaziyatlarda bog\'lanish uchun: Ism va telefon'
    )
    
    # Additional data
    notes = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Qo\'shimcha ma\'lumotlar',
        help_text='JSON formatida qo\'shimcha ma\'lumotlar'
    )

    class Meta:
        unique_together = ("user", "branch")
        verbose_name = "Filial a'zoligi"
        verbose_name_plural = "Filial a'zoliklari"
        indexes = [
            models.Index(fields=["branch", "role"]),
            models.Index(fields=["user", "role"]),
            models.Index(fields=["user", "branch", "role"]),
            models.Index(fields=["hire_date"]),
            models.Index(fields=["termination_date"]),
            models.Index(fields=["employment_type"]),
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
        qs = cls.objects.filter(user_id=user_id, branch_id=branch_id, deleted_at__isnull=True)
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
    
    # NEW: Staff management helper methods
    @property
    def is_staff(self):
        """Check if this membership represents a staff member (not student/parent).
        
        Returns True for: TEACHER, BRANCH_ADMIN, SUPER_ADMIN, OTHER
        Returns False for: STUDENT, PARENT
        """
        return self.role not in [BranchRole.STUDENT, BranchRole.PARENT]
    
    @property
    def is_active_employment(self):
        """Check if employment is currently active.
        
        Returns True if hire_date exists and termination_date is None.
        """
        return bool(self.hire_date and not self.termination_date)
    
    @property
    def days_employed(self):
        """Calculate number of days employed.
        
        Returns:
            int: Number of days from hire_date to termination_date or today.
            None: If hire_date is not set.
        """
        if not self.hire_date:
            return None
        
        from django.utils import timezone
        end_date = self.termination_date or timezone.now().date()
        return (end_date - self.hire_date).days
    
    @property
    def years_employed(self):
        """Calculate number of years employed (rounded).
        
        Returns:
            float: Number of years employed.
            None: If hire_date is not set.
        """
        days = self.days_employed
        if days is None:
            return None
        return round(days / 365.25, 1)
    
    def get_effective_salary(self):
        """Get effective salary based on salary_type.
        
        Alias for get_salary() for consistency with HR module.
        """
        return self.get_salary()
    
    @property
    def balance_status(self):
        """Get balance status: 'positive', 'negative', or 'zero'."""
        if self.balance > 0:
            return 'positive'
        elif self.balance < 0:
            return 'negative'
        return 'zero'


# Import choices for transaction models
from apps.branch.choices import TransactionType, PaymentMethod, PaymentStatus


class BalanceTransaction(BaseModel):
    """Balance transaction record with full audit trail.
    
    Every balance change creates a transaction record with:
    - Type (salary, bonus, deduction, advance, fine, adjustment)
    - Amount (always positive - type determines if it's credit or debit)
    - Previous and new balance snapshots
    - Reference (invoice number, payment ID, etc.)
    - Description
    
    This ensures complete financial history and allows reconciliation.
    All transactions are linked to BranchMembership (not StaffProfile).
    """
    
    membership = models.ForeignKey(
        'branch.BranchMembership',
        on_delete=models.CASCADE,
        related_name='balance_transactions',
        verbose_name='Filial a\'zoligi'
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        verbose_name='Tranzaksiya turi'
    )
    
    # Amount in UZS (som), stored as integer
    amount = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Summa',
        help_text='Tranzaksiya summasi (so\'m, butun son, musbat)'
    )
    
    # Balance snapshots for audit
    previous_balance = models.IntegerField(
        verbose_name='Oldingi balans',
        help_text='Tranzaksiya oldidagi balans'
    )
    new_balance = models.IntegerField(
        verbose_name='Yangi balans',
        help_text='Tranzaksiya keyingi balans'
    )
    
    # Metadata
    reference = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Ma\'lumotnoma',
        help_text='Invoice raqami, to\'lov ID yoki boshqa reference'
    )
    description = models.TextField(
        verbose_name='Tavsif'
    )
    
    # Link to salary payment if applicable
    salary_payment = models.ForeignKey(
        'branch.SalaryPayment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='Maosh to\'lovi'
    )
    
    # Processed by
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='processed_balance_transactions',
        verbose_name='Kim tomonidan'
    )

    class Meta:
        verbose_name = 'Balans tranzaksiyasi'
        verbose_name_plural = 'Balans tranzaksiyalari'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['membership', '-created_at']),
            models.Index(fields=['transaction_type', '-created_at']),
            models.Index(fields=['reference']),
            models.Index(fields=['salary_payment']),
        ]

    def __str__(self) -> str:
        return f"{self.get_transaction_type_display()} - {self.amount:_} so'm @ {self.created_at.strftime('%Y-%m-%d')}"


class SalaryPayment(BaseModel):
    """Salary payment record.
    
    Tracks actual salary payments to staff members.
    Each payment creates corresponding BalanceTransaction(s).
    All payments are linked to BranchMembership (not StaffProfile).
    """
    
    membership = models.ForeignKey(
        'branch.BranchMembership',
        on_delete=models.CASCADE,
        related_name='salary_payments',
        verbose_name='Filial a\'zoligi'
    )
    
    # Payment period
    month = models.DateField(
        db_index=True,
        verbose_name='Oy',
        help_text='Oy (masalan: 2024-01-01 uchun yanvar 2024)'
    )
    
    # Payment details
    amount = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Summa',
        help_text='To\'lov summasi (so\'m, butun son)'
    )
    payment_date = models.DateField(
        db_index=True,
        verbose_name='To\'lov sanasi'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
        verbose_name='To\'lov usuli'
    )
    
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
        verbose_name='Holat'
    )
    
    # Metadata
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='Izohlar'
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='To\'lov raqami',
        help_text='Bank to\'lov raqami yoki boshqa reference'
    )
    
    # Processed by
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='processed_salary_payments',
        verbose_name='Kim tomonidan'
    )

    class Meta:
        verbose_name = 'Maosh to\'lovi'
        verbose_name_plural = 'Maosh to\'lovlari'
        ordering = ['-payment_date', '-created_at']
        unique_together = [('membership', 'month')]
        indexes = [
            models.Index(fields=['membership', '-payment_date']),
            models.Index(fields=['month', 'status']),
            models.Index(fields=['status', '-payment_date']),
        ]

    def __str__(self) -> str:
        user_name = self.membership.user.get_full_name() or self.membership.user.phone_number
        return f"{user_name} - {self.month.strftime('%Y-%m')} - {self.amount:_} so'm"

