# Filial Sozlamalari API

## Umumiy Ma'lumot

Filial sozlamalari API har bir filialning individual sozlamalarini boshqarish uchun ishlatiladi. Dars jadvali, maosh hisoblash, moliya va ish vaqti sozlamalarini o'z ichiga oladi.

**Base URL:** `/api/v1/branches/settings/`  
**Authentication:** Bearer Token required

---

## Endpoints

### 1. Barcha Filiallar Sozlamalari

Barcha filiallarning sozlamalarini olish (faqat superadmin).

**GET** `/api/v1/branches/settings/`

**Permissions:** SuperAdmin

**Response:** `200 OK`

```json
[
  {
    "id": "uuid",
    "branch_id": "uuid",
    "branch_name": "Toshkent filiali",
    
    "lesson_duration_minutes": 45,
    "break_duration_minutes": 10,
    "school_start_time": "08:00:00",
    "school_end_time": "17:00:00",
    
    "academic_year_start_month": 9,
    "academic_year_end_month": 6,
    
    "currency": "UZS",
    "currency_symbol": "so'm",
    
    "salary_calculation_time": "00:00:00",
    "auto_calculate_salary": true,
    "salary_calculation_day": 1,
    
    "late_payment_penalty_percent": "5.00",
    "early_payment_discount_percent": "2.00",
    
    "work_days_per_week": 6,
    "work_hours_per_day": 8,
    
    "additional_settings": {
      "max_students_per_class": 30,
      "grading_system": "5",
      "allow_online_classes": true
    },
    
    "created_at": "2024-01-15T08:00:00Z",
    "updated_at": "2024-12-18T10:00:00Z"
  }
]
```

---

### 2. Bitta Filial Sozlamalari

Konkret filialning sozlamalarini olish.

**GET** `/api/v1/branches/settings/{branch_id}/`

**Parameters:**

| Parameter | Type | Location | Description |
|-----------|------|----------|-------------|
| branch_id | UUID | Path | Filial ID |

**Permissions:** 
- SuperAdmin - barcha filiallar
- BranchAdmin - o'z filiallari

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "branch_id": "branch-uuid",
  "branch_name": "Toshkent filiali",
  
  "lesson_duration_minutes": 45,
  "break_duration_minutes": 10,
  "school_start_time": "08:00:00",
  "school_end_time": "17:00:00",
  
  "academic_year_start_month": 9,
  "academic_year_end_month": 6,
  
  "currency": "UZS",
  "currency_symbol": "so'm",
  
  "salary_calculation_time": "00:00:00",
  "auto_calculate_salary": true,
  "salary_calculation_day": 1,
  
  "late_payment_penalty_percent": "5.00",
  "early_payment_discount_percent": "2.00",
  
  "work_days_per_week": 6,
  "work_hours_per_day": 8,
  
  "additional_settings": {
    "max_students_per_class": 30,
    "grading_system": "5",
    "allow_online_classes": true,
    "sms_notifications": false
  },
  
  "created_at": "2024-01-15T08:00:00Z",
  "updated_at": "2024-12-18T10:00:00Z"
}
```

**Error Responses:**

```json
// 404 - Filial topilmadi
{
  "detail": "Not found."
}

// 403 - Ruxsat yo'q
{
  "detail": "You do not have permission to perform this action."
}
```

---

### 3. Filial Sozlamalarini Yangilash

Filial sozlamalarini o'zgartirish (qisman yangilash).

**PATCH** `/api/v1/branches/settings/{branch_id}/`

**Parameters:**

| Parameter | Type | Location | Description |
|-----------|------|----------|-------------|
| branch_id | UUID | Path | Filial ID |

**Permissions:** 
- SuperAdmin - barcha filiallar
- BranchAdmin - o'z filiallari

**Request Body:**

```json
{
  "lesson_duration_minutes": 50,
  "break_duration_minutes": 15,
  "school_start_time": "08:30:00",
  "salary_calculation_time": "01:00:00",
  "auto_calculate_salary": true,
  "salary_calculation_day": 5,
  "late_payment_penalty_percent": "10.00",
  "early_payment_discount_percent": "5.00",
  "work_days_per_week": 5,
  "additional_settings": {
    "max_students_per_class": 25,
    "sms_notifications": true
  }
}
```

**Response:** `200 OK`

```json
{
  "id": "uuid",
  "branch_id": "uuid",
  "branch_name": "Toshkent filiali",
  
  "lesson_duration_minutes": 50,
  "break_duration_minutes": 15,
  "school_start_time": "08:30:00",
  "school_end_time": "17:00:00",
  
  "academic_year_start_month": 9,
  "academic_year_end_month": 6,
  
  "currency": "UZS",
  "currency_symbol": "so'm",
  
  "salary_calculation_time": "01:00:00",
  "auto_calculate_salary": true,
  "salary_calculation_day": 5,
  
  "late_payment_penalty_percent": "10.00",
  "early_payment_discount_percent": "5.00",
  
  "work_days_per_week": 5,
  "work_hours_per_day": 8,
  
  "additional_settings": {
    "max_students_per_class": 25,
    "sms_notifications": true
  },
  
  "created_at": "2024-01-15T08:00:00Z",
  "updated_at": "2024-12-18T11:30:00Z"
}
```

**Error Responses:**

```json
// 400 - Validatsiya xatosi
{
  "salary_calculation_day": [
    "Kun 1 dan 31 gacha bo'lishi kerak"
  ],
  "work_days_per_week": [
    "Haftalik ish kunlari 1 dan 7 gacha bo'lishi kerak"
  ]
}

// 403 - Ruxsat yo'q
{
  "detail": "You do not have permission to perform this action."
}
```

---

## Sozlamalar Maydonlari

### Dars Jadvali Sozlamalari

| Maydon | Turi | Default | Tavsif |
|--------|------|---------|--------|
| `lesson_duration_minutes` | integer | 45 | Dars davomiyligi (daqiqa) |
| `break_duration_minutes` | integer | 10 | Tanaffus davomiyligi (daqiqa) |
| `school_start_time` | time | "08:00" | Darslar boshlanish vaqti |
| `school_end_time` | time | "17:00" | Darslar tugash vaqti |

**Foydalanish:**
- Dars jadvali tuzishda
- Xona band qilishda
- Darslarga qo'ng'iroq vaqtlarini belgilashda

---

### Akademik Sozlamalar

| Maydon | Turi | Default | Tavsif |
|--------|------|---------|--------|
| `academic_year_start_month` | integer (1-12) | 9 | Akademik yil boshlanish oyi |
| `academic_year_end_month` | integer (1-12) | 6 | Akademik yil tugash oyi |

**Foydalanish:**
- Yillik hisobotlar
- O'quvchilarni kurs bo'yicha o'tkazish
- Statistika

---

### Moliya Sozlamalari

| Maydon | Turi | Default | Tavsif |
|--------|------|---------|--------|
| `currency` | string | "UZS" | Valyuta kodi |
| `currency_symbol` | string | "so'm" | Valyuta belgisi |

**Foydalanish:**
- To'lovlarni ko'rsatishda
- Hisobotlarda
- Cheklarda

---

### Maosh Hisoblash Sozlamalari

| Maydon | Turi | Default | Tavsif |
|--------|------|---------|--------|
| `salary_calculation_time` | time | "00:00" | Maosh hisoblash vaqti |
| `auto_calculate_salary` | boolean | true | Avtomatik maosh hisoblash yoqilganmi |
| `salary_calculation_day` | integer (1-31) | 1 | Har oy qaysi kuni maosh to'lanadi |

**Maosh Hisoblash Vaqti (`salary_calculation_time`):**
- Default: `"00:00:00"` - har kuni yarim tunda
- Celery Beat task ushbu vaqtda ishga tushadi
- 24 soatlik formatda (00:00 dan 23:59 gacha)
- Misol: `"01:00:00"` - soat 1 da, `"09:30:00"` - soat 9:30 da

**Avtomatik Hisoblash (`auto_calculate_salary`):**
- `true`: Har kuni avtomatik ravishda xodimlarning oylik maoshini hisoblaydi
- `false`: Faqat qo'lda maosh qo'shish mumkin

**Maosh To'lash Kuni (`salary_calculation_day`):**
- 1-31 oralig'ida
- Har oy shu kuni xodimlarga maosh to'lanishi kerak
- Misol: 1 - har oy 1-sanada, 15 - har oy 15-sanada

---

### To'lov va Chegirmalar

| Maydon | Turi | Default | Tavsif |
|--------|------|---------|--------|
| `late_payment_penalty_percent` | decimal | 0.00 | Kechikish jarima foizi (%) |
| `early_payment_discount_percent` | decimal | 0.00 | Erta to'lash chegirmasi (%) |

**Kechikish Jarimasi:**
- To'lovni muddatidan keyin to'lasa qo'llaniladigan jarima
- Foizda (%)
- Misol: 5.00 = 5% jarima

**Erta To'lash Chegirmasi:**
- To'lovni muddatidan oldin to'lasa beriladigan chegirma
- Foizda (%)
- Misol: 2.00 = 2% chegirma

---

### Ish Vaqti Sozlamalari

| Maydon | Turi | Default | Tavsif |
|--------|------|---------|--------|
| `work_days_per_week` | integer (1-7) | 6 | Haftada ish kunlari soni |
| `work_hours_per_day` | integer | 8 | Kunlik ish soatlari |

**Foydalanish:**
- Xodimlar ish vaqtini hisoblashda
- Soatlik maoshni hisoblashda
- Ish kunlari rejasini tuzishda

---

### Qo'shimcha Sozlamalar

| Maydon | Turi | Default | Tavsif |
|--------|------|---------|--------|
| `additional_settings` | JSON | {} | Qo'shimcha sozlamalar |

**JSON Struktura (misol):**

```json
{
  "max_students_per_class": 30,
  "grading_system": "5",
  "allow_online_classes": true,
  "sms_notifications": false,
  "email_notifications": true,
  "attendance_tracking": "automatic",
  "homework_submission": "online",
  "parent_portal_access": true,
  "report_card_template": "standard",
  "language": "uz"
}
```

**Umumiy sozlamalar:**
- `max_students_per_class`: Sinfda maksimal o'quvchilar soni
- `grading_system`: Baholash tizimi ("5", "100", "letter")
- `allow_online_classes`: Online darslar ruxsat etilganmi
- `sms_notifications`: SMS xabarnomalar yoqilganmi
- `attendance_tracking`: Davomat kuzatuvi ("manual", "automatic", "biometric")

---

## Foydalanish Misollari

### 1. Filial Sozlamalarini Olish

```bash
curl -X GET "http://localhost:8000/api/v1/branches/settings/550e8400-e29b-41d4-a716-446655440000/" \
  -H "Authorization: Bearer {token}"
```

### 2. Maosh Hisoblash Vaqtini O'zgartirish

```bash
curl -X PATCH "http://localhost:8000/api/v1/branches/settings/550e8400-e29b-41d4-a716-446655440000/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "salary_calculation_time": "02:00:00",
    "auto_calculate_salary": true,
    "salary_calculation_day": 5
  }'
```

### 3. Chegirma va Jarima Sozlash

```bash
curl -X PATCH "http://localhost:8000/api/v1/branches/settings/550e8400-e29b-41d4-a716-446655440000/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "late_payment_penalty_percent": "10.00",
    "early_payment_discount_percent": "3.00"
  }'
```

### 4. Dars Jadvali Sozlamalari

```bash
curl -X PATCH "http://localhost:8000/api/v1/branches/settings/550e8400-e29b-41d4-a716-446655440000/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "lesson_duration_minutes": 50,
    "break_duration_minutes": 15,
    "school_start_time": "08:30:00",
    "school_end_time": "16:30:00"
  }'
```

### 5. Qo'shimcha Sozlamalar

```bash
curl -X PATCH "http://localhost:8000/api/v1/branches/settings/550e8400-e29b-41d4-a716-446655440000/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "additional_settings": {
      "max_students_per_class": 25,
      "grading_system": "100",
      "allow_online_classes": true,
      "sms_notifications": true,
      "language": "uz"
    }
  }'
```

---

## Validatsiya Qoidalari

### 1. Maosh To'lash Kuni

```
1 <= salary_calculation_day <= 31
```

**Xato:**
```json
{
  "salary_calculation_day": [
    "Kun 1 dan 31 gacha bo'lishi kerak"
  ]
}
```

### 2. Haftalik Ish Kunlari

```
1 <= work_days_per_week <= 7
```

**Xato:**
```json
{
  "work_days_per_week": [
    "Haftalik ish kunlari 1 dan 7 gacha bo'lishi kerak"
  ]
}
```

### 3. Vaqt Formati

```
HH:MM:SS (24-soatlik format)
```

**To'g'ri:** `"08:00:00"`, `"14:30:00"`, `"23:59:00"`  
**Noto'g'ri:** `"8:00"`, `"25:00:00"`, `"noon"`

### 4. Akademik Oy

```
1 <= month <= 12
```

---

## Celery Integration

Sozlamalar Celery Beat schedule bilan integratsiyalangan:

### Maosh Hisoblash Schedule

```python
# core/settings.py
CELERY_BEAT_SCHEDULE = {
    'calculate-daily-salary-accrual': {
        'task': 'apps.branch.tasks.calculate_daily_salary_accrual',
        'schedule': crontab(hour=0, minute=0),  # Default
        'options': {'expires': 3600}
    },
}
```

**Dinamik Schedule:**
- Har bir filial o'z `salary_calculation_time` ga ega
- Celery Beat har filial uchun alohida task yaratadi
- `auto_calculate_salary=false` bo'lsa, task o'chiriladi

---

## Frontend Integratsiya

### Settings Form

```javascript
const updateBranchSettings = async (branchId, settings) => {
  const response = await fetch(
    `/api/v1/branches/settings/${branchId}/`,
    {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(settings),
    }
  );
  
  return response.json();
};

// Foydalanish
await updateBranchSettings('branch-uuid', {
  salary_calculation_time: '02:00:00',
  auto_calculate_salary: true,
  late_payment_penalty_percent: '5.00',
});
```

### Settings Display

```javascript
const settings = await fetchBranchSettings(branchId);

// Maosh hisoblash vaqti
console.log(`Maosh ${settings.salary_calculation_time} da hisoblanadi`);

// Avtomatik hisoblash holati
console.log(`Avtomatik: ${settings.auto_calculate_salary ? 'Yoqilgan' : 'O'chirilgan'}`);

// Chegirmalar
console.log(`Erta to'lash chegirmasi: ${settings.early_payment_discount_percent}%`);
console.log(`Kechikish jarimasi: ${settings.late_payment_penalty_percent}%`);
```

---

## Muhim Eslatmalar

1. **Read-Only Maydonlar:**
   - `id`, `branch_id`, `branch_name`, `created_at`, `updated_at`
   - Bu maydonlarni yangilab bo'lmaydi

2. **Avtomatik Yaratilish:**
   - Yangi filial yaratilganda, sozlamalar avtomatik yaratiladi
   - Default qiymatlar o'rnatiladi

3. **Permissions:**
   - SuperAdmin - barcha filiallar
   - BranchAdmin - faqat o'z filiallari
   - Boshqa rollar - kirish yo'q

4. **Timezone:**
   - Barcha vaqtlar `Asia/Tashkent` timezone da
   - Celery Beat ham shu timezone dan foydalanadi

5. **JSON Validation:**
   - `additional_settings` - istalgan JSON struktura
   - Backend validatsiya yo'q, frontend validatsiyasi tavsiya etiladi

---

**Versiya:** 1.0  
**Sana:** 2024-12-18  
**Holat:** Production Ready
