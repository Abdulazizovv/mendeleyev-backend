# Moliya Tizimi - Kassa va Avtomatik Maosh Hisoblash

## Umumiy Ma'lumot

Bu hujjat moliya tizimidagi yangi funksiyalar haqida:
1. Kirim va chiqim turlari (kategoriyalar)
2. Avtomatik kunlik maosh hisoblash
3. Balanslarni qayta hisoblash

---

## 1. Kirim va Chiqim Kategoriyalari

### Kirim Turlari (IncomeCategory)

Transaction yaratishda kirim turini belgilash mumkin:

- `student_payment` - O'quvchi to'lovi
- `course_fee` - Kurs to'lovi  
- `registration_fee` - Ro'yxatdan o'tish to'lovi
- `exam_fee` - Imtihon to'lovi
- `certificate_fee` - Sertifikat to'lovi
- `book_sale` - Kitob sotish
- `material_sale` - Material sotish
- `sponsorship` - Homiylik
- `grant` - Grant
- `other_income` - Boshqa kirim

### Chiqim Turlari (ExpenseCategory)

Transaction yaratishda chiqim turini belgilash mumkin:

- `salary` - Xodim maoshi
- `rent` - Ijara haqi
- `utilities` - Kommunal xizmatlar
- `internet` - Internet
- `phone` - Telefon
- `office_supplies` - Ofis buyumlari
- `books_materials` - Kitob va materiallar
- `equipment` - Asbob-uskunalar
- `maintenance` - Ta'mirlash
- `cleaning` - Tozalash xizmati
- `security` - Xavfsizlik
- `marketing` - Marketing
- `training` - O'qitish va treninglar
- `tax` - Soliq
- `insurance` - Sug'urta
- `transportation` - Transport
- `food` - Ovqat
- `other_expense` - Boshqa chiqim

### Foydalanish Misoli

```python
# Kirim yaratish
from apps.school.finance.models import Transaction
from apps.school.finance.choices import IncomeCategory

transaction = Transaction.objects.create(
    branch=branch,
    cash_register=cash_register,
    transaction_type='income',
    income_category=IncomeCategory.STUDENT_PAYMENT,
    amount=1000000,
    description="O'quvchi to'lovi - Dekabr oyi",
    status='completed'
)

# Chiqim yaratish
from apps.school.finance.choices import ExpenseCategory

transaction = Transaction.objects.create(
    branch=branch,
    cash_register=cash_register,
    transaction_type='expense',
    expense_category=ExpenseCategory.RENT,
    amount=5000000,
    description="Ofis ijarasi - Dekabr",
    status='completed'
)
```

---

## 2. Avtomatik Kunlik Maosh Hisoblash

### Ishlash Prinsipi

Har kuni soat **00:00** da Celery Beat task ishga tushadi va:

1. Barcha **faol xodimlarni** topadi (termination_date=None)
2. **Oylik maoshli** xodimlarni filtrlaydi (salary_type='monthly')
3. Har bir xodim uchun **kunlik maosh** hisoblanadi:
   - 30 kunlik oyda: `monthly_salary / 30`
   - 31 kunlik oyda: `monthly_salary / 31`
   - 28/29 kunlik oyda: `monthly_salary / 28 (yoki 29)`

4. Xodim balansiga kunlik maosh qo'shiladi
5. BalanceTransaction yaratiladi (audit uchun)

### Misol Hisoblash

```
Xodim: Ali Valiyev
Oylik maosh: 3,000,000 so'm
Oy: Dekabr (31 kun)

Kunlik maosh = 3,000,000 / 31 = 96,774 so'm

Har kuni:
- Balance: 0 → 96,774 → 193,548 → ... → 3,000,000
- Transaction yaratiladi: "Kunlik maosh hisoblash: 01.12.2024 (1/31 kun)"
```

### Celery Task

```python
# Task nomi
calculate_daily_salary_accrual

# Schedule
Har kuni soat 00:00 (timezone: Asia/Tashkent)

# Qo'lda ishga tushirish
from apps.branch.tasks import calculate_daily_salary_accrual
result = calculate_daily_salary_accrual.delay()

# Natija
{
    'date': '2024-12-18',
    'staff_count': 25,
    'total_amount': 2500000,
    'days_in_month': 31
}
```

### Django Admin orqali Monitoring

Celery taskni ko'rish:
1. Django Admin → Celery Results → Task Results
2. Task nomi: `apps.branch.tasks.calculate_daily_salary_accrual`
3. Status: SUCCESS / FAILURE / PENDING

### Loglar

```bash
# Celery worker loglarini ko'rish
docker compose logs -f celery

# Django loglarida kunlik maosh hisoblash
[INFO] Daily salary accrued: Ali Valiyev - 96,774 so'm (Toshkent filiali)
[INFO] Daily salary accrual completed: 25 staff members, total amount: 2,500,000 so'm
```

---

## 3. Balanslarni Qayta Hisoblash

### Qachon Kerak?

- Ma'lumotlar bazasida xatolik bo'lsa
- Manual tranzaksiyalar kiritilgandan keyin
- Data migration qilingandan keyin
- Balanslar noto'g'ri ko'rsatilsa

### Task

```python
# Barcha xodimlar uchun
from apps.branch.tasks import recalculate_staff_balances
result = recalculate_staff_balances.delay()

# Bitta filial uchun
result = recalculate_staff_balances.delay(branch_id='uuid')

# Natija
{
    'updated_count': 5,
    'branch_id': 'uuid'
}
```

### Ishlash Prinsipi

1. Barcha xodimlarni oladi (yoki bitta filial)
2. Har bir xodim uchun barcha tranzaksiyalarni sanasi bo'yicha tartiblaydi
3. Balansni qayta hisoblaydi:
   - SALARY, BONUS: balansga qo'shiladi (+)
   - DEDUCTION, ADVANCE, FINE: balansdan ayiriladi (-)
4. Agar hozirgi balans bilan farq bo'lsa, yangilaydi

---

## 4. Migration va Setup

### Migration Yaratish

```bash
docker compose exec django python manage.py makemigrations finance
docker compose exec django python manage.py migrate finance
```

### Celery Worker Ishga Tushirish

```bash
# Celery worker
docker compose up -d celery

# Celery beat (periodic tasks)
docker compose up -d celery-beat

# Loglarni ko'rish
docker compose logs -f celery celery-beat
```

### Test Qilish

```python
# Django shell
docker compose exec django python manage.py shell

# Task ni qo'lda ishga tushirish
from apps.branch.tasks import calculate_daily_salary_accrual
result = calculate_daily_salary_accrual.delay()

# Natijani ko'rish (task ID bilan)
from celery.result import AsyncResult
task = AsyncResult(result.id)
print(task.status)  # SUCCESS / FAILURE / PENDING
print(task.result)  # Natija
```

---

## 5. Database Schema

### Transaction Model Yangi Maydonlar

```python
class Transaction(BaseModel):
    # ... mavjud maydonlar ...
    
    # Yangi maydonlar
    income_category = models.CharField(
        max_length=50,
        choices=IncomeCategory.choices,
        null=True,
        blank=True
    )
    expense_category = models.CharField(
        max_length=50,
        choices=ExpenseCategory.choices,
        null=True,
        blank=True
    )
```

### BalanceTransaction Model (mavjud)

Xodimlar uchun balans tranzaksiyalari:

```python
class BalanceTransaction(BaseModel):
    membership = ForeignKey(BranchMembership)
    transaction_type = CharField(choices=TransactionType)
    amount = IntegerField()
    previous_balance = IntegerField()
    new_balance = IntegerField()
    description = TextField()
    reference = CharField()
    processed_by = ForeignKey(User, null=True)  # None = avtomatik
```

---

## 6. API Endpoints (kelajakda)

### Kassalar

```
GET    /api/v1/finance/cash-registers/
POST   /api/v1/finance/cash-registers/
GET    /api/v1/finance/cash-registers/{id}/
PATCH  /api/v1/finance/cash-registers/{id}/
DELETE /api/v1/finance/cash-registers/{id}/
```

### Tranzaksiyalar

```
GET    /api/v1/finance/transactions/
POST   /api/v1/finance/transactions/
GET    /api/v1/finance/transactions/{id}/

# Filterlar
?transaction_type=income
?income_category=student_payment
?expense_category=salary
?cash_register={uuid}
?branch={uuid}
?date_from=2024-12-01
?date_to=2024-12-31
```

### Statistika

```
GET /api/v1/finance/stats/
  - Total income by category
  - Total expense by category
  - Net profit/loss
  - Cash register balances

GET /api/v1/finance/stats/monthly/
  - Month-by-month breakdown
```

---

## 7. Monitoring va Troubleshooting

### Celery Beat Ishlaganini Tekshirish

```bash
# Beat schedule ko'rish
docker compose exec celery-beat celery -A core inspect scheduled

# Active tasklar
docker compose exec celery celery -A core inspect active

# Registered tasks
docker compose exec celery celery -A core inspect registered
```

### Umumiy Xatolar

#### 1. Task ishlamayapti

**Sabab:** Celery beat ishlamayapti

**Yechim:**
```bash
docker compose up -d celery-beat
docker compose logs -f celery-beat
```

#### 2. Balans noto'g'ri

**Sabab:** Manual tranzaksiya kiritilgan

**Yechim:**
```python
from apps.branch.tasks import recalculate_staff_balances
recalculate_staff_balances.delay()
```

#### 3. Tasklar to'planib qolgan

**Sabab:** Worker ishlamayapti

**Yechim:**
```bash
docker compose restart celery
```

---

## 8. Best Practices

### 1. Tranzaksiya yaratishda

```python
# Har doim transaction_type va tegishli category ko'rsating
if transaction_type == 'income':
    income_category = IncomeCategory.STUDENT_PAYMENT
    expense_category = None
elif transaction_type == 'expense':
    income_category = None
    expense_category = ExpenseCategory.SALARY
```

### 2. Balans bilan ishlashda

```python
# Balansni bevosita o'zgartirmang!
# ❌ staff.balance += 1000000  # NOTO'G'RI

# ✅ TO'G'RI - Transaction yarating
BalanceTransaction.objects.create(
    membership=staff,
    transaction_type=TransactionType.SALARY,
    amount=1000000,
    # ...
)
```

### 3. Kunlik maosh

```python
# Faqat oylik maoshli xodimlar uchun
# Soatlik va darslik maoshli xodimlar uchun boshqa mexanizm kerak
```

---

## 9. Kelajak Rejalar

- [ ] API endpoints yaratish
- [ ] Dashboard statistikasi
- [ ] Excel export
- [ ] SMS notification (kunlik maosh haqida)
- [ ] Email reports (oylik)
- [ ] Multi-currency support
- [ ] Tax calculations
- [ ] Payroll integration

---

## 10. Xulosa

Yangi funksiyalar:

✅ **Kirim/Chiqim kategoriyalari** - 10 ta kirim, 18 ta chiqim turi
✅ **Avtomatik kunlik maosh** - Har kuni soat 00:00 da
✅ **Balans qayta hisoblash** - Manual yoki avtomatik
✅ **Celery Beat integration** - Periodic tasks
✅ **Audit trail** - Har bir tranzaksiya saqlanadi

**Keyingi qadamlar:**
1. Migration yaratish va qo'llash
2. Celery beat ishga tushirish
3. Test qilish
4. API endpoints yaratish
5. Frontend integratsiya

---

**Versiya:** 1.0  
**Sana:** 2024-12-18  
**Muallif:** Development Team
