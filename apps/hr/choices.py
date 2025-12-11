"""HR module choices and enums."""
from django.db import models


class EmploymentType(models.TextChoices):
    """Employment types for staff members."""
    FULL_TIME = 'full_time', 'To\'liq vaqt'
    PART_TIME = 'part_time', 'Qisman vaqt'
    CONTRACT = 'contract', 'Shartnoma'
    TEMPORARY = 'temporary', 'Vaqtinchalik'


class SalaryType(models.TextChoices):
    """Salary calculation types."""
    MONTHLY = 'monthly', 'Oylik (aniq belgilangan)'
    HOURLY = 'hourly', 'Soatlik'
    PER_LESSON = 'per_lesson', 'Dars uchun'


class PaymentStatus(models.TextChoices):
    """Payment statuses."""
    PENDING = 'pending', 'Kutilmoqda'
    PAID = 'paid', 'To\'langan'
    CANCELLED = 'cancelled', 'Bekor qilingan'
    FAILED = 'failed', 'Muvaffaqiyatsiz'


class PaymentMethod(models.TextChoices):
    """Payment methods."""
    CASH = 'cash', 'Naqd pul'
    BANK_TRANSFER = 'bank_transfer', 'Bank o\'tkazmasi'
    CARD = 'card', 'Karta'
    CLICK = 'click', 'Click'
    PAYME = 'payme', 'Payme'
    OTHER = 'other', 'Boshqa'


class TransactionType(models.TextChoices):
    """Balance transaction types."""
    DEPOSIT = 'deposit', 'Kirim (to\'lov)'
    WITHDRAWAL = 'withdrawal', 'Chiqim'
    SALARY = 'salary', 'Maosh'
    BONUS = 'bonus', 'Bonus'
    FINE = 'fine', 'Jarima'
    ADJUSTMENT = 'adjustment', 'Tuzatish'
    ADVANCE = 'advance', 'Avans'


class StaffStatus(models.TextChoices):
    """Staff status."""
    ACTIVE = 'active', 'Faol'
    INACTIVE = 'inactive', 'Nofaol'
    ON_LEAVE = 'on_leave', 'Ta\'tilda'
    TERMINATED = 'terminated', 'Ishdan bo\'shatilgan'
