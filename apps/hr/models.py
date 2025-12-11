"""HR Models - Xodimlar Boshqaruvi.

This module provides comprehensive staff management:
- StaffRole: Branch-specific roles with permissions and salary ranges
- StaffProfile: Staff member profiles with employment and financial data
- BalanceTransaction: Tracks all balance changes with full audit trail
- SalaryPayment: Records salary payments

Architecture Notes:
- StaffProfile links User + Branch + StaffRole
- All financial fields use IntegerField for UZS (som) to avoid decimal precision issues
- Balance is atomic via select_for_update in BalanceService
- BranchMembership remains lightweight, HR-specific data lives here
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from apps.common.models import BaseModel


class StaffRole(BaseModel):
    """Role definition for staff members.
    
    Roles can be branch-specific or global (branch=None).
    Defines permissions and optional salary range guidance.
    
    Examples:
    - Teacher (branch-specific): permissions=['view_grades', 'edit_attendance']
    - Guard (branch-specific): permissions=['view_schedule']
    - Cook (branch-specific): permissions=['view_menu', 'manage_inventory']
    """
    
    name = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name='Rol nomi',
        help_text='Rol nomi (masalan: Oshpaz, Qorovul, O\'qituvchi)'
    )
    code = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name='Kod',
        help_text='Unikal kod (masalan: cook, guard, teacher)'
    )
    branch = models.ForeignKey(
        'branch.Branch',
        on_delete=models.CASCADE,
        related_name='staff_roles',
        verbose_name='Filial',
        help_text='Filial (har filial o\'z rollarini boshqaradi)'
    )
    
    # Permissions stored as JSON
    permissions = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Ruxsatlar',
        help_text='Ruxsatlar ro\'yxati. Masalan: ["view_salary", "manage_menu", "view_schedule"]'
    )
    
    # Salary range guidance (optional)
    salary_range_min = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Minimal maosh',
        help_text='Minimal maosh (so\'m). Optional - faqat yo\'riqnoma'
    )
    salary_range_max = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Maksimal maosh',
        help_text='Maksimal maosh (so\'m). Optional - faqat yo\'riqnoma'
    )
    
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='Tavsif'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Faol'
    )

    class Meta:
        verbose_name = 'Xodim roli'
        verbose_name_plural = 'Xodim rollari'
        unique_together = [('branch', 'code')]
        constraints = [
            models.CheckConstraint(
                check=models.Q(salary_range_min__lte=models.F('salary_range_max')) | 
                      models.Q(salary_range_min__isnull=True) | 
                      models.Q(salary_range_max__isnull=True),
                name='hr_staffrole_valid_salary_range'
            ),
        ]
        indexes = [
            models.Index(fields=['branch', 'is_active']),
            models.Index(fields=['code']),
        ]

    def __str__(self) -> str:
        return f"{self.name} @ {self.branch.name}"


class StaffProfile(BaseModel):
    """Staff member profile with employment and financial data.
    
    Links User + Branch + StaffRole and stores all HR-related data.
    Keeps BranchMembership lightweight by moving financial fields here.
    
    Balance is managed via BalanceTransaction to ensure full audit trail.
    """
    
    # Core relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='staff_profiles',
        verbose_name='Foydalanuvchi'
    )
    branch = models.ForeignKey(
        'branch.Branch',
        on_delete=models.CASCADE,
        related_name='staff_profiles',
        verbose_name='Filial'
    )
    membership = models.OneToOneField(
        'branch.BranchMembership',
        on_delete=models.CASCADE,
        related_name='staff_profile',
        null=True,
        blank=True,
        verbose_name='A\'zolik',
        help_text='BranchMembership bilan bog\'lanish (backward compatibility)'
    )
    staff_role = models.ForeignKey(
        'hr.StaffRole',
        on_delete=models.PROTECT,
        related_name='staff_members',
        verbose_name='Rol'
    )
    
    # Employment details
    employment_type = models.CharField(
        max_length=20,
        choices=[],  # Will be set from choices.EmploymentType
        default='full_time',
        verbose_name='Ish turi'
    )
    hire_date = models.DateField(
        verbose_name='Ishga qabul qilingan sana'
    )
    termination_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Ishdan bo\'shatilgan sana'
    )
    
    # Financial fields (all in UZS, stored as integer to avoid decimal issues)
    base_salary = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Asosiy maosh',
        help_text='Oylik asosiy maosh (so\'m, butun son)'
    )
    current_balance = models.IntegerField(
        default=0,
        verbose_name='Joriy balans',
        help_text='Joriy balans (so\'m, butun son). Tranzaksiyalar orqali o\'zgaradi'
    )
    
    # Banking details
    bank_account = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='Bank hisob raqami'
    )
    tax_id = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='Soliq ID (INN/PINFL)'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[],  # Will be set from choices.StaffStatus
        default='active',
        verbose_name='Holat'
    )
    
    # Additional metadata
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='Izohlar'
    )

    class Meta:
        verbose_name = 'Xodim profili'
        verbose_name_plural = 'Xodim profillari'
        unique_together = [('user', 'branch')]
        indexes = [
            models.Index(fields=['branch', 'status']),
            models.Index(fields=['staff_role', 'status']),
            models.Index(fields=['hire_date']),
        ]

    def __str__(self) -> str:
        return f"{self.user.get_full_name() or self.user.phone_number} - {self.staff_role.name}"


class BalanceTransaction(BaseModel):
    """Balance transaction record with full audit trail.
    
    Every balance change creates a transaction record with:
    - Type (deposit, withdrawal, salary, bonus, fine, etc.)
    - Amount (positive for credits, negative for debits in the type field logic)
    - Previous and new balance snapshots
    - Reference (invoice number, payment ID, etc.)
    - Description
    
    This ensures complete financial history and allows reconciliation.
    """
    
    staff = models.ForeignKey(
        'hr.StaffProfile',
        on_delete=models.CASCADE,
        related_name='balance_transactions',
        verbose_name='Xodim'
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=[],  # Will be set from choices.TransactionType
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
        'hr.SalaryPayment',
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
        related_name='processed_transactions',
        verbose_name='Kim tomonidan'
    )

    class Meta:
        verbose_name = 'Balans tranzaksiyasi'
        verbose_name_plural = 'Balans tranzaksiyalari'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['staff', '-created_at']),
            models.Index(fields=['transaction_type', '-created_at']),
            models.Index(fields=['reference']),
        ]

    def __str__(self) -> str:
        return f"{self.get_transaction_type_display()} - {self.amount} so'm @ {self.created_at.strftime('%Y-%m-%d')}"


class SalaryPayment(BaseModel):
    """Salary payment record.
    
    Tracks actual salary payments to staff members.
    Each payment creates corresponding BalanceTransaction(s).
    """
    
    staff = models.ForeignKey(
        'hr.StaffProfile',
        on_delete=models.CASCADE,
        related_name='salary_payments',
        verbose_name='Xodim'
    )
    
    # Payment period
    month = models.DateField(
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
        verbose_name='To\'lov sanasi'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=[],  # Will be set from choices.PaymentMethod
        default='cash',
        verbose_name='To\'lov usuli'
    )
    
    status = models.CharField(
        max_length=20,
        choices=[],  # Will be set from choices.PaymentStatus
        default='pending',
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
        unique_together = [('staff', 'month')]
        indexes = [
            models.Index(fields=['staff', '-payment_date']),
            models.Index(fields=['month', 'status']),
            models.Index(fields=['status', '-payment_date']),
        ]

    def __str__(self) -> str:
        return f"{self.staff.user.get_full_name()} - {self.month.strftime('%Y-%m')} - {self.amount} so'm"


# Set choices after class definition to avoid circular imports
from apps.hr.choices import (
    EmploymentType, StaffStatus, TransactionType, 
    PaymentMethod, PaymentStatus
)

StaffProfile._meta.get_field('employment_type').choices = EmploymentType.choices
StaffProfile._meta.get_field('status').choices = StaffStatus.choices
BalanceTransaction._meta.get_field('transaction_type').choices = TransactionType.choices
SalaryPayment._meta.get_field('payment_method').choices = PaymentMethod.choices
SalaryPayment._meta.get_field('status').choices = PaymentStatus.choices
