"""
Moliya tizimi modellari.

Bu modellar moliyaviy operatsiyalarni, balanslarni, to'lovlarni va 
statistikani boshqarish uchun ishlatiladi.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils import timezone
from apps.common.models import BaseModel
from apps.branch.models import Branch, BranchMembership
from auth.profiles.models import StudentProfile


class TransactionType(models.TextChoices):
    """Tranzaksiya turlari."""
    INCOME = 'income', 'Kirim'
    EXPENSE = 'expense', 'Chiqim'
    TRANSFER = 'transfer', 'O\'tkazma'
    PAYMENT = 'payment', 'To\'lov'
    SALARY = 'salary', 'Maosh'
    REFUND = 'refund', 'Qaytarish'


class TransactionStatus(models.TextChoices):
    """Tranzaksiya holati."""
    PENDING = 'pending', 'Kutilmoqda'
    COMPLETED = 'completed', 'Bajarilgan'
    CANCELLED = 'cancelled', 'Bekor qilingan'
    FAILED = 'failed', 'Muvaffaqiyatsiz'


class PaymentMethod(models.TextChoices):
    """To'lov usullari."""
    CASH = 'cash', 'Naqd pul'
    CARD = 'card', 'Karta'
    BANK_TRANSFER = 'bank_transfer', 'Bank o\'tkazmasi'
    MOBILE_PAYMENT = 'mobile_payment', 'Mobil to\'lov'
    OTHER = 'other', 'Boshqa'


class SubscriptionPeriod(models.TextChoices):
    """Abonement davri."""
    MONTHLY = 'monthly', 'Oylik'
    YEARLY = 'yearly', 'Yillik'
    QUARTERLY = 'quarterly', 'Choraklik'
    SEMESTER = 'semester', 'Semestr'


class DiscountType(models.TextChoices):
    """Chegirma turi."""
    PERCENTAGE = 'percentage', 'Foiz'
    FIXED = 'fixed', 'Aniq summa'


class CashRegister(BaseModel):
    """Kassa modeli.
    
    Har bir filial o'ziga bir nechta kassa yaratishi mumkin.
    Har bir kassada balans va tranzaksiyalar saqlanadi.
    """
    
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='cash_registers',
        verbose_name='Filial'
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Kassa nomi',
        help_text='Masalan: "Asosiy kassa", "Kichik kassa"'
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='Tavsif'
    )
    
    # Balans
    balance = models.BigIntegerField(
        default=0,
        verbose_name='Balans',
        help_text='Kassadagi joriy balans (so\'m, butun son)'
    )
    
    # Holat
    is_active = models.BooleanField(
        default=True,
        verbose_name='Faol',
        help_text='Kassa faolmi?'
    )
    
    # Qo'shimcha ma'lumotlar
    location = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='Manzil',
        help_text='Kassa joylashgan manzil'
    )
    
    class Meta:
        verbose_name = 'Kassa'
        verbose_name_plural = 'Kassalar'
        unique_together = [('branch', 'name')]
        indexes = [
            models.Index(fields=['branch', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.branch.name})"
    
    def update_balance(self, amount: int, transaction_type: str):
        """Kassa balansini yangilash."""
        if transaction_type in [TransactionType.INCOME, TransactionType.PAYMENT]:
            self.balance += amount
        elif transaction_type in [TransactionType.EXPENSE, TransactionType.SALARY]:
            self.balance -= amount
        self.save(update_fields=['balance', 'updated_at'])


class Transaction(BaseModel):
    """Tranzaksiya modeli.
    
    Barcha moliyaviy operatsiyalar uchun asosiy model.
    Har bir tranzaksiya mukammal tarzda saqlanadi va o'zgartirib bo'lmaydi.
    """
    
    # Asosiy ma'lumotlar
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='Filial'
    )
    cash_register = models.ForeignKey(
        CashRegister,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='Kassa'
    )
    
    # Tranzaksiya turi va holati
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        verbose_name='Tranzaksiya turi'
    )
    status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
        verbose_name='Holat'
    )
    
    # Summa
    amount = models.BigIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Summa',
        help_text='Tranzaksiya summasi (so\'m, butun son)'
    )
    
    # To'lov usuli
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
        verbose_name='To\'lov usuli'
    )
    
    # Ma'lumotlar
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='Tavsif',
        help_text='Tranzaksiya haqida qo\'shimcha ma\'lumot'
    )
    reference_number = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='Referens raqami',
        help_text='Chek, kvitansiya yoki boshqa hujjat raqami'
    )
    
    # Bog'lanishlar
    student_profile = models.ForeignKey(
        StudentProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='O\'quvchi',
        help_text='Agar tranzaksiya o\'quvchi bilan bog\'liq bo\'lsa'
    )
    employee_membership = models.ForeignKey(
        BranchMembership,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='Xodim',
        help_text='Agar tranzaksiya xodim bilan bog\'liq bo\'lsa (masalan, maosh)'
    )
    
    # Sana va vaqt
    transaction_date = models.DateTimeField(
        default=timezone.now,
        verbose_name='Tranzaksiya sanasi',
        help_text='Tranzaksiya amalga oshirilgan sana va vaqt'
    )
    
    # Qo'shimcha ma'lumotlar (JSON)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Qo\'shimcha ma\'lumotlar',
        help_text='Qo\'shimcha ma\'lumotlar JSON formatida'
    )
    
    class Meta:
        verbose_name = 'Tranzaksiya'
        verbose_name_plural = 'Tranzaksiyalar'
        indexes = [
            models.Index(fields=['branch', 'transaction_type', 'status']),
            models.Index(fields=['cash_register', 'transaction_date']),
            models.Index(fields=['student_profile', 'transaction_date']),
            models.Index(fields=['employee_membership', 'transaction_date']),
            models.Index(fields=['transaction_date']),
        ]
        ordering = ['-transaction_date']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} so'm ({self.branch.name})"
    
    def save(self, *args, **kwargs):
        """Tranzaksiyani saqlash va kassa balansini yangilash."""
        is_new = self.pk is None
        
        # Agar yangi tranzaksiya bo'lsa va status COMPLETED bo'lsa
        if is_new and self.status == TransactionStatus.COMPLETED:
            self.cash_register.update_balance(self.amount, self.transaction_type)
        
        super().save(*args, **kwargs)
    
    def complete(self):
        """Tranzaksiyani bajarilgan deb belgilash."""
        if self.status == TransactionStatus.COMPLETED:
            return
        
        self.status = TransactionStatus.COMPLETED
        self.save(update_fields=['status', 'updated_at'])
        self.cash_register.update_balance(self.amount, self.transaction_type)
    
    def cancel(self):
        """Tranzaksiyani bekor qilish."""
        if self.status == TransactionStatus.CANCELLED:
            return
        
        # Agar tranzaksiya bajarilgan bo'lsa, balansni qaytarish
        if self.status == TransactionStatus.COMPLETED:
            # Balansni teskari yo'nalishda yangilash
            reverse_type = TransactionType.EXPENSE if self.transaction_type == TransactionType.INCOME else TransactionType.INCOME
            self.cash_register.update_balance(self.amount, reverse_type)
        
        self.status = TransactionStatus.CANCELLED
        self.save(update_fields=['status', 'updated_at'])


class StudentBalance(BaseModel):
    """O'quvchi balansi.
    
    Har bir o'quvchi uchun alohida balans saqlanadi.
    Balans to'lovlar va tranzaksiyalar asosida yangilanadi.
    """
    
    student_profile = models.OneToOneField(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='balance',
        verbose_name='O\'quvchi'
    )
    
    # Balans
    balance = models.BigIntegerField(
        default=0,
        verbose_name='Balans',
        help_text='O\'quvchining joriy balansi (so\'m, butun son)'
    )
    
    # Qo'shimcha ma'lumotlar
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='Eslatmalar'
    )
    
    class Meta:
        verbose_name = 'O\'quvchi balansi'
        verbose_name_plural = 'O\'quvchi balanslari'
    
    def __str__(self):
        return f"{self.student_profile} - {self.balance} so'm"
    
    def add_amount(self, amount: int):
        """Balansga summa qo'shish."""
        self.balance += amount
        self.save(update_fields=['balance', 'updated_at'])
    
    def subtract_amount(self, amount: int):
        """Balansdan summa ayirish."""
        if self.balance < amount:
            raise ValueError("Balans yetarli emas")
        self.balance -= amount
        self.save(update_fields=['balance', 'updated_at'])


class SubscriptionPlan(BaseModel):
    """Abonement tarifi.
    
    Har bir filial uchun sinf darajasi bo'yicha abonement tariflari.
    Masalan: 1-4 sinflar 1400000, 5-9 sinflar 1900000.
    """
    
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='subscription_plans',
        null=True,
        blank=True,
        verbose_name='Filial',
        help_text='Agar bo\'sh bo\'lsa, bu umumiy tarif (barcha filiallar uchun)'
    )
    
    # Sinf darajasi
    grade_level_min = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(11)],
        verbose_name='Minimal sinf darajasi',
        help_text='Minimal sinf darajasi (1-11)'
    )
    grade_level_max = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(11)],
        verbose_name='Maksimal sinf darajasi',
        help_text='Maksimal sinf darajasi (1-11)'
    )
    
    # Davr va narx
    period = models.CharField(
        max_length=20,
        choices=SubscriptionPeriod.choices,
        default=SubscriptionPeriod.MONTHLY,
        verbose_name='Davr',
        help_text='Abonement davri'
    )
    price = models.BigIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Narx',
        help_text='Abonement narxi (so\'m, butun son)'
    )
    
    # Holat
    is_active = models.BooleanField(
        default=True,
        verbose_name='Faol',
        help_text='Tarif faolmi?'
    )
    
    # Qo'shimcha ma'lumotlar
    name = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='Tarif nomi',
        help_text='Masalan: "1-4 sinflar oylik tarifi"'
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='Tavsif'
    )
    
    class Meta:
        verbose_name = 'Abonement tarifi'
        verbose_name_plural = 'Abonement tariflari'
        indexes = [
            models.Index(fields=['branch', 'is_active']),
            models.Index(fields=['grade_level_min', 'grade_level_max']),
            models.Index(fields=['is_active']),  # Umumiy tariflar uchun
        ]
    
    def __str__(self):
        period_display = self.get_period_display()
        branch_name = self.branch.name if self.branch else "Umumiy"
        return f"{self.grade_level_min}-{self.grade_level_max} sinflar ({period_display}) - {self.price:,} so'm @ {branch_name}"
    
    def matches_grade_level(self, grade_level: int) -> bool:
        """Sinf darajasi tarifga mos keladimi?"""
        return self.grade_level_min <= grade_level <= self.grade_level_max


class Discount(BaseModel):
    """Chegirma modeli.
    
    Har bir filial o'ziga chegirmalar yaratishi mumkin.
    Chegirma foiz yoki aniq summa bo'lishi mumkin.
    """
    
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='discounts',
        null=True,
        blank=True,
        verbose_name='Filial',
        help_text='Agar bo\'sh bo\'lsa, bu umumiy chegirma (barcha filiallar uchun)'
    )
    
    # Chegirma ma'lumotlari
    name = models.CharField(
        max_length=255,
        verbose_name='Chegirma nomi',
        help_text='Masalan: "Yangi o\'quvchilar uchun chegirma"'
    )
    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
        default=DiscountType.PERCENTAGE,
        verbose_name='Chegirma turi'
    )
    
    # Summa yoki foiz
    amount = models.BigIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Summa yoki foiz',
        help_text='Foiz bo\'lsa 0-100 orasida (butun son), summa bo\'lsa aniq summa (so\'m, butun son)'
    )
    
    # Holat
    is_active = models.BooleanField(
        default=True,
        verbose_name='Faol',
        help_text='Chegirma faolmi?'
    )
    
    # Sana cheklovlari
    valid_from = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Boshlanish sanasi',
        help_text='Chegirma qachondan amal qiladi'
    )
    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Tugash sanasi',
        help_text='Chegirma qachongacha amal qiladi'
    )
    
    # Qo'shimcha ma'lumotlar
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='Tavsif'
    )
    
    # Qo'shimcha shartlar (JSON)
    conditions = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Qo\'shimcha shartlar',
        help_text='Qo\'shimcha shartlar JSON formatida (masalan, minimal summa)'
    )
    
    class Meta:
        verbose_name = 'Chegirma'
        verbose_name_plural = 'Chegirmalar'
        indexes = [
            models.Index(fields=['branch', 'is_active']),
            models.Index(fields=['valid_from', 'valid_until']),
            models.Index(fields=['is_active']),  # Umumiy chegirmalar uchun
        ]
    
    def __str__(self):
        branch_name = self.branch.name if self.branch else "Umumiy"
        if self.discount_type == DiscountType.PERCENTAGE:
            return f"{self.name} - {self.amount}% @ {branch_name}"
        return f"{self.name} - {self.amount:,} so'm @ {branch_name}"
    
    def calculate_discount(self, base_amount: int) -> int:
        """Chegirmani hisoblash."""
        if not self.is_active:
            return 0
        
        # Sana tekshiruvi
        now = timezone.now()
        if self.valid_from and now < self.valid_from:
            return 0
        if self.valid_until and now > self.valid_until:
            return 0
        
        # Chegirmani hisoblash
        if self.discount_type == DiscountType.PERCENTAGE:
            # Foiz bo'lsa
            if self.amount > 100:
                return 0
            return int((base_amount * self.amount) / 100)
        else:
            # Aniq summa bo'lsa
            return min(self.amount, base_amount)
    
    def is_valid(self) -> bool:
        """Chegirma hozir amal qiladimi?"""
        if not self.is_active:
            return False
        
        now = timezone.now()
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        
        return True


class Payment(BaseModel):
    """To'lov modeli.
    
    O'quvchilarning to'lovlari uchun model.
    Har bir to'lov tranzaksiya bilan bog'langan.
    """
    
    # Asosiy ma'lumotlar
    student_profile = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='O\'quvchi'
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Filial'
    )
    
    # Abonement tarifi
    subscription_plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name='Abonement tarifi',
        help_text='Qaysi tarif uchun to\'lov'
    )
    
    # Summa
    base_amount = models.BigIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Asosiy summa',
        help_text='Chegirma qo\'llanmagan summa (so\'m, butun son)'
    )
    discount_amount = models.BigIntegerField(
        default=0,
        verbose_name='Chegirma summasi',
        help_text='Qo\'llangan chegirma summasi (so\'m, butun son)'
    )
    final_amount = models.BigIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Yakuniy summa',
        help_text='Chegirma qo\'llanganidan keyingi summa (so\'m, butun son)'
    )
    
    # Chegirma
    discount = models.ForeignKey(
        Discount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name='Chegirma',
        help_text='Qo\'llangan chegirma'
    )
    
    # To'lov usuli
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
        verbose_name='To\'lov usuli'
    )
    
    # Davr
    period = models.CharField(
        max_length=20,
        choices=SubscriptionPeriod.choices,
        default=SubscriptionPeriod.MONTHLY,
        verbose_name='Davr',
        help_text='Qaysi davr uchun to\'lov'
    )
    
    # Sana
    payment_date = models.DateTimeField(
        default=timezone.now,
        verbose_name='To\'lov sanasi'
    )
    period_start = models.DateField(
        verbose_name='Davr boshlanishi',
        help_text='Abonement davrining boshlanish sanasi'
    )
    period_end = models.DateField(
        verbose_name='Davr tugashi',
        help_text='Abonement davrining tugash sanasi'
    )
    
    # Tranzaksiya
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.CASCADE,
        related_name='payment',
        verbose_name='Tranzaksiya',
        help_text='To\'lov bilan bog\'liq tranzaksiya'
    )
    
    # Qo'shimcha ma'lumotlar
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='Eslatmalar'
    )
    
    class Meta:
        verbose_name = 'To\'lov'
        verbose_name_plural = 'To\'lovlar'
        indexes = [
            models.Index(fields=['student_profile', 'payment_date']),
            models.Index(fields=['branch', 'payment_date']),
            models.Index(fields=['period_start', 'period_end']),
        ]
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.student_profile} - {self.final_amount} so'm ({self.payment_date.strftime('%Y-%m-%d')})"

