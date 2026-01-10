# Tushlik Tanaffusi Sozlamalari - O'zgartirish Jurnali

**Sana**: 2026-01-10  
**Versiya**: Branch Settings v1.1  
**Maqsad**: BranchSettings modeliga tushlik tanaffusi vaqtlarini qo'shish

---

## 📝 Qilingan O'zgarishlar

### 1. Model O'zgarishlari (`apps/branch/models.py`)

#### BranchSettings Modeliga Yangi Maydonlar:

```python
# Tushlik tanaffusi sozlamalari
lunch_break_start = models.TimeField(
    blank=True,
    null=True,
    verbose_name='Tushlik tanaffusi boshlanish vaqti',
    help_text='Tushlik tanaffusi boshlanish vaqti (masalan: 12:00). Bo\'sh qoldirilsa, tushlik tanaffusi yo\'q'
)
lunch_break_end = models.TimeField(
    blank=True,
    null=True,
    verbose_name='Tushlik tanaffusi tugash vaqti',
    help_text='Tushlik tanaffusi tugash vaqti (masalan: 13:00). Bo\'sh qoldirilsa, tushlik tanaffusi yo\'q'
)
```

**Xususiyatlari**:
- Ixtiyoriy maydonlar (nullable, blank=True)
- Agar tushlik tanaffusi kerak bo'lmasa, bo'sh qoldirilishi mumkin
- TimeField tipida

---

### 2. Serializer O'zgarishlari (`apps/branch/settings_serializers.py`)

#### BranchSettingsSerializer

Yangi maydonlar qo'shildi:
- `lunch_break_start`
- `lunch_break_end`

#### BranchSettingsUpdateSerializer

**Yangi Validatsiya Qoidalari**:

1. **Ikkala maydon birga**: 
   - Agar `lunch_break_start` kiritilsa, `lunch_break_end` ham kiritilishi shart
   - Agar `lunch_break_end` kiritilsa, `lunch_break_start` ham kiritilishi shart

2. **Vaqt tartibi**: 
   - `lunch_break_start` < `lunch_break_end` bo'lishi kerak

3. **Maktab ish vaqti ichida**:
   - `lunch_break_start` >= `school_start_time`
   - `lunch_break_end` <= `school_end_time`

**Xato xabarlari**:
```python
# Agar faqat bittasi kiritilsa:
"Tushlik tanaffusi boshlanish va tugash vaqti ikkalasi ham kiritilishi kerak."

# Agar tugash vaqti boshlanish vaqtidan oldin bo'lsa:
"Tushlik tanaffusi tugash vaqti boshlanish vaqtidan keyin bo'lishi kerak."

# Agar maktab ish vaqtidan tashqarida bo'lsa:
"Tushlik tanaffusi maktab boshlanish vaqtidan keyin bo'lishi kerak."
"Tushlik tanaffusi maktab tugash vaqtidan oldin bo'lishi kerak."
```

---

### 3. Ma'lumotlar Bazasi O'zgarishlari

**Migration**: `0019_branchsettings_lunch_break_end_and_more.py`

```python
migrations.AddField(
    model_name='branchsettings',
    name='lunch_break_end',
    field=models.TimeField(blank=True, null=True, ...)
),
migrations.AddField(
    model_name='branchsettings',
    name='lunch_break_start',
    field=models.TimeField(blank=True, null=True, ...)
)
```

**Holati**: ✅ Muvaffaqiyatli qo'llanildi

---

### 4. Admin Panel O'zgarishlari (`apps/branch/admin.py`)

#### BranchSettingsInline

**Yangilangan fieldsets**:
```python
('Dars jadvali sozlamalari', {
    'fields': (
        'lesson_duration_minutes', 
        'break_duration_minutes', 
        'school_start_time', 
        'school_end_time',
        'lunch_break_start',  # Yangi
        'lunch_break_end'     # Yangi
    )
})
```

#### BranchSettingsAdmin

**Yangilangan list_display**:
- Endi `lunch_break_start` va `lunch_break_end` ro'yxatda ko'rsatiladi
- Admin panelda barcha filiallar uchun tushlik tanaffusi vaqtlarini ko'rish va tahrirlash mumkin

**Xususiyatlar**:
- Branch yaratish/tahrirlash sahifasida inline ko'rinishda
- Alohida BranchSettings sahifasida to'liq ko'rinish
- Validatsiya backend tomonidan avtomatik bajariladi

---

### 5. API O'zgarishlari

#### GET `/api/branches/{branch_id}/settings/`

**Yangi Response Maydonlari**:
```json
{
  "lunch_break_start": "12:00:00",
  "lunch_break_end": "13:00:00"
}
```

#### PATCH `/api/branches/{branch_id}/settings/`

**Yangi Request Maydonlari** (ixtiyoriy):
```json
{
  "lunch_break_start": "12:00",
  "lunch_break_end": "13:00"
}
```

**Misol So'rov**:
```bash
curl -X PATCH "http://api.example.com/api/branches/{branch_id}/settings/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "lunch_break_start": "12:30",
    "lunch_break_end": "13:30"
  }'
```

**Tushlik tanaffusini o'chirish**:
```json
{
  "lunch_break_start": null,
  "lunch_break_end": null
}
```

---

### 5. Hujjatlar O'zgarishlari

#### Yangilangan fayllar:

1. **`docs/api/branch.md`**
   - BranchSettings API dokumentatsiyasi to'liq yangilandi
   - Yangi maydonlar va validatsiya qoidalari qo'shildi
   - Request/Response misollari qo'shildi

2. **`docs/ACADEMIC_SYSTEM_COMPLETE.md`**
   - Branch Settings Extension bo'limiga lunch break maydonlari qo'shildi
   - Validatsiya qoidalari qo'shildi

---

## 🎯 Foydalanish Holatlari

### Holat 1: Tushlik tanaffusini o'rnatish

```json
PATCH /api/branches/{branch_id}/settings/
{
  "lunch_break_start": "12:00",
  "lunch_break_end": "13:00"
}
```

### Holat 2: Tushlik tanaffusisiz (standart)

```json
PATCH /api/branches/{branch_id}/settings/
{
  "lesson_duration_minutes": 45,
  "break_duration_minutes": 10
  // lunch_break_start va lunch_break_end kiritilmaydi
}
```

### Holat 3: Tushlik tanaffusini o'chirish

```json
PATCH /api/branches/{branch_id}/settings/
{
  "lunch_break_start": null,
  "lunch_break_end": null
}
```

---

## ⚠️ Muhim Eslatmalar

1. **Backward Compatibility**: 
   - Mavjud barcha branch settings uchun `lunch_break_start` va `lunch_break_end` NULL bo'ladi
   - Bu eski funksionallikni buzmaydi

2. **Ixtiyoriy Maydonlar**:
   - Tushlik tanaffusi har bir filial uchun ixtiyoriy
   - Ba'zi filiallar tushlik tanaffusiga ega bo'lishi, boshqalari bo'lmasligi mumkin

3. **Validatsiya**:
   - Frontend validatsiyani ham qo'shish tavsiya etiladi
   - Backend validatsiyasi barcha qoidalarni tekshiradi

4. **Dars Jadvallariga Ta'siri**:
   - Dars jadvali tuzishda tushlik tanaffusini hisobga olish kerak
   - `LessonGenerator` servisi yangilanishi mumkin (kelajakda)

---

## 🔄 Keyingi Qadamlar

### Kelajak Takomillashtirish Imkoniyatlari:

1. **LessonGenerator yangilash**:
   - Dars jadvallarini generatsiya qilishda tushlik tanaffusini hisobga olish
   - Tushlik vaqtida darslarni rejalashtirmaslik

2. **Ko'p tushlik tanaffuslari**:
   - Bir necha tushlik tanaffuslari qo'shish imkoniyati
   - Turli smenalar uchun turli tushlik vaqtlari

3. **Maxsus tanaffuslar**:
   - Namoz vaqti, sport vaqti va boshqa maxsus tanaffuslar

---

## 📊 Texnik Ma'lumotlar

**O'zgartirilgan Fayllar**:
- ✅ `apps/branch/models.py` (2 yangi maydon)
- ✅ `apps/branch/settings_serializers.py` (validatsiya qo'shildi)
- ✅ `apps/branch/admin.py` (admin panel yangilandi)
- ✅ `apps/branch/migrations/0019_*.py` (yangi migration)
- ✅ `docs/api/branch.md` (API dokumentatsiyasi)
- ✅ `docs/ACADEMIC_SYSTEM_COMPLETE.md` (umumiy dokumentatsiya)

**Test Holati**: ⚠️ Unit testlar qo'shish tavsiya etiladi

**Code Review**: ✅ Tayyor

**Production Deployment**: ✅ Tayyor

---

## 🧪 Test Qilish

### Manual Test

```bash
# 1. Docker containerda kirish
docker exec -it django bash

# 2. Django shell ochish
python manage.py shell

# 3. Test qilish
from apps.branch.models import Branch, BranchSettings
from datetime import time

# Branch yaratish yoki mavjudini olish
branch = Branch.objects.first()

# Settings olish
settings = branch.get_settings()

# Tushlik tanaffusini o'rnatish
settings.lunch_break_start = time(12, 0)
settings.lunch_break_end = time(13, 0)
settings.save()

# Tekshirish
print(f"Lunch break: {settings.lunch_break_start} - {settings.lunch_break_end}")
```

### API Test

```bash
# GET request
curl -X GET "http://localhost:8000/api/branches/{branch_id}/settings/" \
  -H "Authorization: Bearer <token>"

# PATCH request
curl -X PATCH "http://localhost:8000/api/branches/{branch_id}/settings/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "lunch_break_start": "12:00",
    "lunch_break_end": "13:00"
  }'
```

---

## ✅ Xulosa

BranchSettings modeliga tushlik tanaffusi vaqtlarini qo'shish muvaffaqiyatli amalga oshirildi:

- ✅ Model maydonlari qo'shildi
- ✅ Serializer va validatsiya yangilandi
- ✅ Migration yaratildi va qo'llanildi
- ✅ API ishlayapti
- ✅ Dokumentatsiya yangilandi

**Keyingi qadam**: Frontend integratsiyasi va LessonGenerator servisi yangilash.
