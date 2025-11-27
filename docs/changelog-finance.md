# Changelog - Moliya Tizimi

## 2024-11-27 - Moliya Tizimi Qo'shildi

### Yangi Modellar

1. **CashRegister (Kassa)**
   - Har bir filial uchun bir nechta kassa yaratish imkoniyati
   - Kassa balansi (`BigIntegerField`, so'm)
   - Kassa holati (faol/nofaol)
   - Manzil va tavsif

2. **Transaction (Tranzaksiya)**
   - Barcha moliyaviy operatsiyalar uchun asosiy model
   - Tranzaksiya turlari: `income`, `expense`, `transfer`, `payment`, `salary`, `refund`
   - Tranzaksiya holati: `pending`, `completed`, `cancelled`, `failed`
   - To'lov usullari: `cash`, `card`, `bank_transfer`, `mobile_payment`, `other`
   - Kassa balansini avtomatik yangilash
   - O'quvchi va xodim bilan bog'lanish

3. **StudentBalance (O'quvchi Balansi)**
   - Har bir o'quvchi uchun alohida balans
   - To'lovlar asosida avtomatik yangilanish
   - Balansga qo'shish/ayirish metodlari

4. **SubscriptionPlan (Abonement Tarifi)**
   - Sinf darajasi bo'yicha tariflar (masalan: 1-4 sinflar 1400000, 5-9 sinflar 1900000)
   - Davrlar: `monthly`, `yearly`, `quarterly`, `semester`
   - **Umumiy tariflar**: Agar `branch` `null` bo'lsa, barcha filiallar uchun
   - Sinf darajasi diapazoni (1-11)

5. **Discount (Chegirma)**
   - Foiz yoki aniq summa
   - Sana cheklovlari (`valid_from`, `valid_until`)
   - **Umumiy chegirmalar**: Agar `branch` `null` bo'lsa, barcha filiallar uchun
   - Qo'shimcha shartlar (JSON)

6. **Payment (To'lov)**
   - O'quvchi to'lovlari
   - Abonement tarifi bilan bog'lanish
   - Chegirma qo'llash
   - Tranzaksiya bilan avtomatik bog'lanish
   - O'quvchi balansini avtomatik yangilash

### O'zgarishlar

1. **Valyuta**: Barcha summalar so'm (butun sonlar, `BigIntegerField`)
   - `DecimalField` → `BigIntegerField` o'zgartirildi
   - Barcha metodlar `int` bilan ishlaydi

2. **StudentProfile ga status qo'shildi**
   - `StudentStatus` choices: `active`, `archived`, `suspended`, `graduated`, `transferred`
   - Default: `active`
   - Filter va ordering qo'llab-quvvatlanadi

3. **Umumiy Tariflar va Chegirmalar**
   - `SubscriptionPlan.branch` va `Discount.branch` `null=True, blank=True`
   - Agar `branch` bo'sh bo'lsa, umumiy (barcha filiallar uchun)
   - Views da umumiy tariflar va chegirmalar ham ko'rsatiladi

### API Endpoints

1. **Kassalar**
   - `GET /api/v1/school/finance/cash-registers/` - Ro'yxat
   - `POST /api/v1/school/finance/cash-registers/` - Yaratish
   - `GET /api/v1/school/finance/cash-registers/{id}/` - Ma'lumotlar
   - `PUT/PATCH /api/v1/school/finance/cash-registers/{id}/` - Yangilash
   - `DELETE /api/v1/school/finance/cash-registers/{id}/` - O'chirish

2. **Tranzaksiyalar**
   - `GET /api/v1/school/finance/transactions/` - Ro'yxat
   - `POST /api/v1/school/finance/transactions/` - Yaratish
   - `GET /api/v1/school/finance/transactions/{id}/` - Ma'lumotlar
   - `PUT/PATCH /api/v1/school/finance/transactions/{id}/` - Yangilash
   - `DELETE /api/v1/school/finance/transactions/{id}/` - O'chirish

3. **O'quvchi Balanslari**
   - `GET /api/v1/school/finance/student-balances/` - Ro'yxat
   - `GET /api/v1/school/finance/student-balances/{id}/` - Ma'lumotlar

4. **Abonement Tariflari**
   - `GET /api/v1/school/finance/subscription-plans/` - Ro'yxat
   - `POST /api/v1/school/finance/subscription-plans/` - Yaratish
   - `GET /api/v1/school/finance/subscription-plans/{id}/` - Ma'lumotlar
   - `PUT/PATCH /api/v1/school/finance/subscription-plans/{id}/` - Yangilash
   - `DELETE /api/v1/school/finance/subscription-plans/{id}/` - O'chirish

5. **Chegirmalar**
   - `GET /api/v1/school/finance/discounts/` - Ro'yxat
   - `POST /api/v1/school/finance/discounts/` - Yaratish
   - `GET /api/v1/school/finance/discounts/{id}/` - Ma'lumotlar
   - `PUT/PATCH /api/v1/school/finance/discounts/{id}/` - Yangilash
   - `DELETE /api/v1/school/finance/discounts/{id}/` - O'chirish

6. **To'lovlar**
   - `GET /api/v1/school/finance/payments/` - Ro'yxat
   - `POST /api/v1/school/finance/payments/` - Yaratish
   - `GET /api/v1/school/finance/payments/{id}/` - Ma'lumotlar

7. **Statistika**
   - `GET /api/v1/school/finance/statistics/` - Moliya statistikasi

### Permissions

- `CanManageFinance` - Super Admin, Branch Admin uchun ruxsat
- Barcha moliya operatsiyalari uchun autentifikatsiya talab qilinadi

### Features

1. **Avtomatik Balans Yangilanishi**
   - Tranzaksiya yaratilganda kassa balansi avtomatik yangilanadi
   - To'lov yaratilganda o'quvchi balansi avtomatik yangilanadi

2. **Chegirma Hisoblash**
   - Foiz yoki aniq summa
   - Sana cheklovlari
   - Qo'shimcha shartlar

3. **Statistika**
   - Umumiy kirim va chiqim
   - Kassalar balansi
   - O'quvchi balanslari
   - To'lovlar statistikasi
   - Oylik statistika

4. **Filtering, Search, Ordering**
   - Barcha list view'larda qo'llab-quvvatlanadi
   - Pagination mavjud

### Hujjatlashtirish

- [Finance API Documentation](../api/finance.md) - To'liq API hujjatlari
- [Students API Documentation](../api/students.md) - O'quvchilar API hujjatlari (yangi)
- [API Index](../api/index.md) - Barcha API'lar ro'yxati (yangilangan)
- [API README](../api/README.md) - Umumiy API ma'lumotlari (yangi)

### Migratsiyalar

- `apps/school/finance/migrations/0001_initial.py` - Finance modellari
- `auth/profiles/migrations/0009_studentprofile_status_and_more.py` - StudentProfile ga status

### Signallar

1. **StudentBalance Auto-Creation**
   - `StudentProfile` yaratilganda `StudentBalance` avtomatik yaratiladi
   - Signal: `apps.school.finance.signals.create_student_balance`
   - Default balance: 0 so'm

2. **BranchSettings Auto-Creation** (mavjud)
   - `Branch` yaratilganda `BranchSettings` avtomatik yaratiladi
   - Signal: `apps.branch.signals.create_branch_settings`

### Tuzatilgan Muammolar

1. **PaymentCreateSerializer xatoligi**
   - `cash_register` field'i to'g'ri ishlaydi
   - `write_only=True` qo'shildi
   - Validatsiya yaxshilandi

2. **Migratsiya xatoligi**
   - `school.0002_remove_quarter_academic_year_and_more.py` o'chirildi (noto'g'ri migratsiya)

