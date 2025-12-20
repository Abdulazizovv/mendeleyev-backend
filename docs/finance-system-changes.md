# Finance System Summary

## Qo'shilgan Yangiliklar

### 1. Kirim va Chiqim Kategoriyalari

**File:** `apps/school/finance/choices.py`

- **IncomeCategory**: 10 ta kirim turi (student_payment, course_fee, exam_fee, ...)
- **ExpenseCategory**: 18 ta chiqim turi (salary, rent, utilities, marketing, ...)

**Transaction modelga qo'shildi:**
- `income_category` - kirim bo'lsa
- `expense_category` - chiqim bo'lsa

### 2. Avtomatik Kunlik Maosh

**File:** `apps/branch/tasks.py`

**Task:** `calculate_daily_salary_accrual`
- Har kuni soat 00:00 da avtomatik ishga tushadi
- Oylik maoshni oyning kun soniga bo'ladi
- Har kuni xodim balansiga qo'shadi
- BalanceTransaction yaratadi

**Misol:**
```
Oylik maosh: 3,000,000 so'm
Dekabr: 31 kun
Kunlik: 3,000,000 / 31 = 96,774 so'm

1-kun: 96,774
2-kun: 193,548
...
31-kun: 3,000,000
```

### 3. Celery Beat Schedule

**File:** `core/settings.py`

```python
CELERY_BEAT_SCHEDULE = {
    'calculate-daily-salary-accrual': {
        'task': 'apps.branch.tasks.calculate_daily_salary_accrual',
        'schedule': crontab(hour=0, minute=0),
    },
}
```

### 4. Balans Qayta Hisoblash

**Task:** `recalculate_staff_balances`
- Barcha tranzaksiyalarni ko'rib chiqadi
- Balansni qayta hisoblaydi
- Xatoliklarni tuzatadi

## Ishga Tushirish

### 1. Migration

```bash
docker compose exec django python manage.py makemigrations finance
docker compose exec django python manage.py migrate finance
```

### 2. Celery

```bash
# Worker va Beat ishga tushirish
docker compose up -d celery celery-beat

# Loglarni ko'rish
docker compose logs -f celery celery-beat
```

### 3. Test

```bash
# Django shell
docker compose exec django python manage.py shell

# Task ni test qilish
from apps.branch.tasks import calculate_daily_salary_accrual
result = calculate_daily_salary_accrual.delay()
print(result.get())
```

## Fayl Tuzilmasi

```
apps/
├── branch/
│   └── tasks.py              # Yangi - maosh tasklari
│
├── school/
│   └── finance/
│       ├── choices.py        # Yangi - kategoriyalar
│       └── models.py         # Yangilandi - income/expense_category
│
core/
└── settings.py               # Yangilandi - CELERY_BEAT_SCHEDULE

docs/
└── finance-salary-automation.md  # To'liq hujjat
```

## Keyingi Qadamlar

1. ✅ Modellar yaratildi
2. ✅ Celery tasklar yaratildi
3. ✅ Schedule sozlandi
4. ⏳ Migration qo'llash
5. ⏳ Test qilish
6. ⏳ API endpoints (kelajakda)

## Muhim Eslatmalar

- Faqat `salary_type='monthly'` bo'lgan xodimlar uchun ishlaydi
- Faol xodimlar uchun (`termination_date=None`)
- Har kuni soat 00:00 da avtomatik
- Barcha tranzaksiyalar saqlanadi (audit)
- `processed_by=None` - avtomatik system tomonidan

## Monitoring

```bash
# Celery beat schedule
docker compose exec celery-beat celery -A core inspect scheduled

# Active tasks
docker compose exec celery celery -A core inspect active

# Task results
# Django Admin → Celery Results → Task Results
```
