"""Choices for finance app models."""

from django.db import models


class CategoryType(models.TextChoices):
    """Kategoriya turi."""
    INCOME = 'income', 'Kirim'
    EXPENSE = 'expense', 'Chiqim'


class IncomeCategory(models.TextChoices):
    """Kirim turlari."""
    STUDENT_PAYMENT = 'student_payment', "O'quvchi to'lovi"
    COURSE_FEE = 'course_fee', "Kurs to'lovi"
    REGISTRATION_FEE = 'registration_fee', "Ro'yxatdan o'tish to'lovi"
    EXAM_FEE = 'exam_fee', "Imtihon to'lovi"
    CERTIFICATE_FEE = 'certificate_fee', "Sertifikat to'lovi"
    BOOK_SALE = 'book_sale', "Kitob sotish"
    MATERIAL_SALE = 'material_sale', "Material sotish"
    SPONSORSHIP = 'sponsorship', "Homiylik"
    GRANT = 'grant', "Grant"
    OTHER_INCOME = 'other_income', "Boshqa kirim"


class ExpenseCategory(models.TextChoices):
    """Chiqim turlari."""
    SALARY = 'salary', "Xodim maoshi"
    RENT = 'rent', "Ijara haqi"
    UTILITIES = 'utilities', "Kommunal xizmatlar"
    INTERNET = 'internet', "Internet"
    PHONE = 'phone', "Telefon"
    OFFICE_SUPPLIES = 'office_supplies', "Ofis buyumlari"
    BOOKS_MATERIALS = 'books_materials', "Kitob va materiallar"
    EQUIPMENT = 'equipment', "Asbob-uskunalar"
    MAINTENANCE = 'maintenance', "Ta'mirlash"
    CLEANING = 'cleaning', "Tozalash xizmati"
    SECURITY = 'security', "Xavfsizlik"
    MARKETING = 'marketing', "Marketing"
    TRAINING = 'training', "O'qitish va treninglar"
    TAX = 'tax', "Soliq"
    INSURANCE = 'insurance', "Sug'urta"
    TRANSPORTATION = 'transportation', "Transport"
    FOOD = 'food', "Ovqat"
    OTHER_EXPENSE = 'other_expense', "Boshqa chiqim"
