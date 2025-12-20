# Xodimlar Statistikasi API

## Umumiy Ma'lumot

Xodimlar statistikasi API filial yoki barcha filiallar bo'yicha xodimlar haqida to'liq statistik ma'lumot beradi.

## Endpoint

```
GET /api/v1/branches/staff/stats/
```

## Parametrlar

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| branch | UUID | Yo'q | Filial ID (ko'rsatilmasa barcha filiallar) |

## Response Structure

```json
{
    "total_staff": 25,
    "active_staff": 23,
    "terminated_staff": 2,
    "by_employment_type": [
        {
            "employment_type": "full_time",
            "count": 20
        },
        {
            "employment_type": "part_time",
            "count": 3
        }
    ],
    "by_role": [
        {
            "role": "teacher",
            "count": 15
        },
        {
            "role": "branch_admin",
            "count": 5
        },
        {
            "role": "other",
            "count": 3
        }
    ],
    "by_custom_role": [
        {
            "role_ref__id": "550e8400-e29b-41d4-a716-446655440000",
            "role_ref__name": "Matematika o'qituvchisi",
            "count": 8
        },
        {
            "role_ref__id": "550e8400-e29b-41d4-a716-446655440001",
            "role_ref__name": "Ingliz tili o'qituvchisi",
            "count": 7
        }
    ],
    "average_salary": 3500000.00,
    "total_salary_budget": 80500000,
    "max_salary": 8000000,
    "min_salary": 2000000,
    "total_paid": 156000000,
    "total_pending": 12500000,
    "paid_payments_count": 45,
    "pending_payments_count": 8,
    "total_balance": -2500000
}
```

## Ma'lumotlar Tushunchasi

### Xodimlar Soni
- **total_staff**: Jami xodimlar soni (faol + ishdan bo'shatilgan)
- **active_staff**: Hozirda ishlab turgan xodimlar soni
- **terminated_staff**: Ishdan bo'shatilgan xodimlar soni

### Lavozim Bo'yicha Statistika
- **by_employment_type**: Ish turi bo'yicha (to'liq vaqtli, yarim vaqtli, shartnoma, mavsumiy)
- **by_role**: Asosiy lavozim turlari (o'qituvchi, filial admin, boshqa)
- **by_custom_role**: Maxsus lavozimlar (masalan, "Matematika o'qituvchisi", "Ingliz tili o'qituvchisi")

### Maosh Statistikasi
- **average_salary**: O'rtacha oylik maosh (so'm)
- **total_salary_budget**: Oylik umumiy maosh byudjeti - barcha faol xodimlarning oylik maoshi yig'indisi
- **max_salary**: Eng yuqori maosh
- **min_salary**: Eng past maosh

### To'lovlar Statistikasi
- **total_paid**: Jami to'langan summa (barcha vaqt davomida)
- **total_pending**: Kutilayotgan to'lovlar summasi (hali to'lanmagan)
- **paid_payments_count**: To'langan to'lovlar soni
- **pending_payments_count**: Kutilayotgan to'lovlar soni

### Balans Statistikasi
- **total_balance**: Xodimlarning umumiy balansi
  - Musbat balans: Xodimlar qarzdor (avans olgan)
  - Manfiy balans: Xodimlarning berish kerak bo'lgan maoshi bor

## Foydalanish Misollari

### 1. Barcha filiallar statistikasi

```bash
curl -X GET "http://localhost:8000/api/v1/branches/staff/stats/" \
  -H "Authorization: Bearer {token}"
```

### 2. Bitta filial statistikasi

```bash
curl -X GET "http://localhost:8000/api/v1/branches/staff/stats/?branch=550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer {token}"
```

## Biznes Hisob-kitoblar

### 1. Oylik Maosh Byudjeti
`total_salary_budget` - bu har oyda to'lash kerak bo'lgan umumiy summa

### 2. To'lash Kerak Bo'lgan Summa
```
to'lash_kerak = total_salary_budget - total_paid
```

### 3. Qarzdorlik Holati
- Agar `total_balance < 0`: Xodimlarning maoshi qolgan (kompaniya qarzdor)
- Agar `total_balance > 0`: Xodimlar avans olgan (xodimlar qarzdor)

### 4. To'lov Foizi
```python
to'lov_foizi = (total_paid / (total_salary_budget * 12)) * 100  # Yillik
```

## Muhim Eslatmalar

1. **Faqat Faol Xodimlar**: Maosh statistikasi faqat faol xodimlar uchun hisoblanadi
2. **To'lovlar Tarixi**: To'lovlar statistikasi barcha vaqt davomida to'langan summalari
3. **Balans**: Balans musbat yoki manfiy bo'lishi mumkin
4. **Filtr**: `branch` parametri ko'rsatilmasa, barcha filiallar uchun statistika qaytariladi

## Error Kodlari

| Kod | Tavsif |
|-----|--------|
| 200 | Muvaffaqiyatli |
| 401 | Autentifikatsiya xatosi |
| 403 | Ruxsat yo'q |
| 404 | Filial topilmadi |

## Frontend Uchun Maslahatlar

### Dashboard Widget
```javascript
// Asosiy ko'rsatkichlar
const stats = await fetchStaffStats(branchId);

const widgets = [
  {
    title: "Xodimlar",
    value: stats.active_staff,
    subtitle: `Jami: ${stats.total_staff}`,
  },
  {
    title: "Oylik Byudjet",
    value: formatMoney(stats.total_salary_budget),
    subtitle: `O'rtacha: ${formatMoney(stats.average_salary)}`,
  },
  {
    title: "To'langan",
    value: formatMoney(stats.total_paid),
    subtitle: `${stats.paid_payments_count} ta to'lov`,
  },
  {
    title: "Kutilmoqda",
    value: formatMoney(stats.total_pending),
    subtitle: `${stats.pending_payments_count} ta to'lov`,
  },
];
```

### Chart Ma'lumotlari
```javascript
// Lavozim bo'yicha donut chart
const roleChartData = stats.by_role.map(item => ({
  label: item.role,
  value: item.count,
}));

// Ish turi bo'yicha bar chart
const employmentChartData = stats.by_employment_type.map(item => ({
  category: item.employment_type,
  count: item.count,
}));
```

## Yangilanishlar

- **v1.0** (2025-12-16): Dastlabki versiya
  - Xodimlar soni
  - Maosh statistikasi
  - To'lovlar statistikasi
  - Balans ma'lumotlari
