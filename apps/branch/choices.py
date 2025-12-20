"""Choices for branch app models."""

from django.db import models


class TransactionType(models.TextChoices):
    """Balance transaction types - balansga qo'shish yoki ayirish."""
    SALARY_ACCRUAL = 'salary_accrual', 'Oylik hisoblash'
    BONUS = 'bonus', 'Bonus'
    DEDUCTION = 'deduction', 'Balansdan chiqarish'
    ADVANCE = 'advance', 'Avans berish'
    FINE = 'fine', 'Jarima'
    ADJUSTMENT = 'adjustment', "To'g'rilash"
    OTHER = 'other', 'Boshqa'


class PaymentMethod(models.TextChoices):
    """Payment method choices."""
    CASH = 'cash', 'Naqd'
    BANK_TRANSFER = 'bank_transfer', "Bank o'tkazmasi"
    CARD = 'card', 'Karta'
    OTHER = 'other', 'Boshqa'


class PaymentStatus(models.TextChoices):
    """Payment status choices."""
    PENDING = 'pending', 'Kutilmoqda'
    PAID = 'paid', "To'langan"
    CANCELLED = 'cancelled', 'Bekor qilingan'
    FAILED = 'failed', 'Muvaffaqiyatsiz'


class PaymentType(models.TextChoices):
    """Payment type - xodimga to'lov turlari."""
    ADVANCE = 'advance', 'Avans to\'lovi'
    SALARY = 'salary', 'Oylik to\'lovi'
    BONUS_PAYMENT = 'bonus_payment', 'Bonus to\'lovi'
    OTHER = 'other', 'Boshqa to\'lov'
