"""Choices for branch app models."""

from django.db import models


class TransactionType(models.TextChoices):
    """Balance transaction types."""
    SALARY = 'salary', 'Maosh'
    BONUS = 'bonus', 'Bonus'
    DEDUCTION = 'deduction', 'Ushlab qolish'
    ADVANCE = 'advance', 'Avans'
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
