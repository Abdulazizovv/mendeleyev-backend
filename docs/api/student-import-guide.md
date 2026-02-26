# O'quvchilarni Excel orqali Import qilish - Qo'llanma

## Kirish

Ushbu qo'llanma o'quvchilarni Excel fayl orqali import qilish API sini ishlatish bo'yicha to'liq ma'lumot beradi. Bu funksiya boshqa platformadan export qilingan o'quvchilar ma'lumotlarini tizimga yuklash uchun mo'ljallangan.

## Tizim Talablari

1. **Backend:**
   - Django 5.2.6+
   - Django REST Framework 3.15.2+
   - openpyxl 3.1.5+ (Excel fayllarni o'qish uchun)

2. **Ruxsatlar:**
   - `super_admin` - barcha filiallarda import qilishi mumkin
   - `branch_admin` - faqat o'z filialida import qilishi mumkin

## Excel Fayl Tayyorlash

### 1. Fayl Formati

- **Fayl turi:** `.xlsx` yoki `.xls`
- **Maksimal hajm:** 10 MB
- **Birinchi qator:** Header (ustun nomlari)
- **Ikkinchi qatordan boshlab:** O'quvchilar ma'lumotlari

### 2. Ustunlar Tartibi

Excel faylda quyidagi ustunlar **to'g'ri tartibda** bo'lishi kerak:

| № | Ustun Nomi | Majburiy | Misol | Izoh |
|---|-----------|----------|-------|------|
| A | Shartnoma Raqam FIO | Ha | Ali Karim o'g'li Valiyev | To'liq ism (ism, otasining ismi, familiya) |
| B | Balans | Yo'q | 0 | Hisob balansi (son) |
| C | Smil | Yo'q | - | Ishlatilmaydi |
| D | Guruh | Yo'q | 5-A | Guruh/sinf nomi |
| E | Telefon Raqam | Ha | +998901234567 | O'quvchi telefon raqami (unique) |
| F | Sinf Rahbari | Yo'q | Javohirbek Bahromov | Ishlatilmaydi |
| G | Jinsi | Yo'q | male | male/female/erkak/ayol |
| H | Tug'ilgan sanai | Yo'q | 2010-05-15 | YYYY-MM-DD yoki DD.MM.YYYY |
| I | Manzil | Yo'q | Toshkent shahri | To'liq manzil |
| J | Shartnoma sanasi | Yo'q | - | Ishlatilmaydi |
| K | Shartnoma tugasi | Yo'q | - | Ishlatilmaydi |
| L | Passport | Yo'q | AB1234567 | Passport yoki ID raqami |
| M | Aboniment | Yo'q | - | Ishlatilmaydi |
| N | 1-Yaqinl Turi | Yo'q | ota | Birinchi yaqin turi |
| O | 1-Yaqini FIO | Yo'q | Karim Olim o'g'li Valiyev | Birinchi yaqin to'liq ismi |
| P | 1-Yaqini Telefon | Yo'q | +998901234568 | Birinchi yaqin telefoni |
| Q | 2-Yaqini Turi | Yo'q | ona | Ikkinchi yaqin turi |
| R | 2-Yaqini FIO | Yo'q | Nodira Aziz qizi Valiyeva | Ikkinchi yaqin to'liq ismi |
| S | 2-Yaqini Telefon | Yo'q | +998901234569 | Ikkinchi yaqin telefoni |

### 3. Yaqinlik Turlari

Quyidagi qiymatlar qo'llab-quvvatlanadi:

| Excel'da | Sistemada | O'zbek tilida |
|----------|-----------|---------------|
| ota, otasi, dada, father | father | Otasi |
| ona, onasi, oyi, mother | mother | Onasi |
| aka, ukasi, akasi, brother | brother | Akasi/Ukasi |
| opa, singil, opasi, sister | sister | Opasi/Singili |
| bobo, bobosi, grandfather | grandfather | Bobosi |
| buvi, buvisi, grandmother | grandmother | Buvisi |
| amaki, tog'a, uncle | uncle | Amakisi/Tog'asi |
| xola, amma, aunt | aunt | Xolasi/Ammasi |
| vasiy, guardian | guardian | Vasiy |
| Boshqalar | guardian | Vasiy (default) |

### 4. Misol Excel Fayl

```
| Shartnoma Raqam FIO | Balans | Smil | Guruh | Telefon Raqam | ... |
|---------------------|--------|------|-------|---------------|-----|
| Ali Karim o'g'li Valiyev | 0 | - | 5-A | +998901234567 | ... |
| Vali Aziz o'g'li Aliyev | 0 | - | 6-B | +998901234568 | ... |
```

## API Ishlatish

### 1. Endpoint

```
POST /api/school/students/import/
```

### 2. Headers

```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: multipart/form-data
```

### 3. Request Body

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | File | Ha | Excel fayl |
| branch_id | UUID | Ha | Filial ID |
| dry_run | Boolean | Yo'q | Faqat validatsiya (default: false) |

### 4. cURL Misol

```bash
# Haqiqiy import
curl -X POST https://api.example.com/api/school/students/import/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@students.xlsx" \
  -F "branch_id=550e8400-e29b-41d4-a716-446655440000"

# Dry run (faqat tekshirish)
curl -X POST https://api.example.com/api/school/students/import/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@students.xlsx" \
  -F "branch_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "dry_run=true"
```

### 5. Python Misol

```python
import requests

url = "https://api.example.com/api/school/students/import/"
headers = {"Authorization": "Bearer YOUR_TOKEN"}
files = {"file": open("students.xlsx", "rb")}
data = {
    "branch_id": "550e8400-e29b-41d4-a716-446655440000",
    "dry_run": False  # True - faqat validatsiya
}

response = requests.post(url, headers=headers, files=files, data=data)
print(response.json())
```

### 6. JavaScript Misol

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('branch_id', branchId);
formData.append('dry_run', false);

fetch('/api/school/students/import/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN'
  },
  body: formData
})
.then(response => response.json())
.then(data => {
  console.log(`Jami: ${data.total}, Muvaffaqiyatli: ${data.success}`);
})
.catch(error => console.error('Xatolik:', error));
```

## Response

### Muvaffaqiyatli Import

```json
{
  "total": 100,
  "success": 95,
  "failed": 3,
  "skipped": 2,
  "errors": [
    {
      "row": 5,
      "error": "Telefon raqam +998901234567 allaqachon mavjud",
      "student": "Ali Valiyev"
    }
  ],
  "students": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Ali Karim o'g'li Valiyev",
      "phone": "+998901234567",
      "status": "created"
    }
  ]
}
```

### Dry Run Rejimi

```json
{
  "total": 100,
  "success": 97,
  "failed": 0,
  "skipped": 3,
  "errors": [
    {
      "row": 5,
      "error": "Telefon raqam +998901234567 allaqachon mavjud",
      "student": "Ali Valiyev"
    }
  ],
  "students": [
    {
      "row": 2,
      "name": "Ali Karim o'g'li Valiyev",
      "phone": "+998901234567",
      "status": "ready"
    }
  ]
}
```

## Xatolarni Hal qilish

### 1. Telefon raqam allaqachon mavjud

**Xatolik:**
```
"Telefon raqam +998901234567 allaqachon mavjud"
```

**Yechim:**
- Excel faylda dublikat telefon raqamlarni o'chirib tashlang
- Yoki mavjud o'quvchini update qilish API sidan foydalaning

### 2. Excel fayl formati noto'g'ri

**Xatolik:**
```
"Faqat Excel fayllar qabul qilinadi (.xlsx yoki .xls)"
```

**Yechim:**
- Faylni `.xlsx` yoki `.xls` formatida saqlang
- CSV faylni Excel formatiga o'tkazing

### 3. Filial topilmadi

**Xatolik:**
```
"Filial topilmadi"
```

**Yechim:**
- To'g'ri `branch_id` ni kiriting
- Filial mavjudligini tekshiring

### 4. Ruxsat yo'q

**Xatolik:**
```
"Sizda o'quvchilarni import qilish huquqi yo'q"
```

**Yechim:**
- `super_admin` yoki `branch_admin` roli bilan login qiling
- Admin dan ruxsat so'rang

## Eng Yaxshi Amaliyotlar

### 1. Dry Run Rejimidan Foydalaning

Import qilishdan oldin, doim `dry_run=true` bilan tekshiring:

```bash
curl ... -F "dry_run=true"
```

### 2. Kichik Batch'larda Import qiling

Katta Excel fayllarni (1000+ qator) kichik batch'larga bo'lib import qiling:
- Birinchi 100 ta o'quvchi
- Keyin keyingi 100 ta va h.k.

### 3. Telefon Raqamlarni Tekshiring

Import qilishdan oldin:
- Telefon raqamlar to'g'ri formatda ekanligini tekshiring
- Dublikatlar yo'qligini tekshiring
- Bo'sh telefon raqamlar yo'qligini tekshiring

### 4. Yaqinlar Ma'lumotlarini To'ldiring

Yaqinlar majburiy emas, lekin:
- Kamida bitta yaqin (ota yoki ona) bo'lishi tavsiya etiladi
- Yaqinlar telefon raqamlari ham unique bo'lishi kerak

### 5. Import Natijasini Saqlang

Import natijasini log file yoki database ga saqlang:

```python
results = response.json()

# Log file ga yozish
with open('import_log.txt', 'a') as f:
    f.write(f"Import date: {datetime.now()}\n")
    f.write(f"Total: {results['total']}, Success: {results['success']}\n")
    f.write(f"Failed: {results['failed']}, Skipped: {results['skipped']}\n")
    f.write("\n")
```

## FAQ

**Q: Excel fayldagi bo'sh qatorlar import qilinadimi?**
A: Yo'q, bo'sh qatorlar avtomatik o'tkazib yuboriladi.

**Q: Yaqinlar bo'lmasa ham import qilinadi?**
A: Ha, yaqinlar majburiy emas. Yaqinlar ma'lumotlari bo'lmasa, faqat o'quvchi yaratiladi.

**Q: Import qilingan o'quvchilarni qanday topish mumkin?**
A: Barcha import qilingan o'quvchilarning `additional_fields` maydonida `imported_from_excel: true` belgisi bor.

**Q: Import paytida xatolik yuz bersa nima bo'ladi?**
A: Barcha operatsiyalar bitta transaksiyada bajariladi. Agar birorta xatolik yuz bersa, hech narsa saqlanmaydi.

**Q: Bir xil telefon raqam bilan import qilish mumkinmi?**
A: Yo'q, har bir telefon raqam sistemada faqat bir marta bo'lishi mumkin. Agar telefon allaqachon mavjud bo'lsa, o'quvchi `skipped` ga qo'shiladi.

**Q: Import jarayoni qancha vaqt oladi?**
A: 100 ta o'quvchi uchun taxminan 10-15 soniya. Katta fayllar uchun koproq vaqt ketishi mumkin.

## Qo'llab-quvvatlash

Agar muammo yuz bersa:
1. [API Documentation](student-import.md) ni o'qing
2. Error log'larni tekshiring
3. Backend developer bilan bog'laning
4. GitHub issue yarating

## Yangiliklar

### Version 1.0.0 (2025-01-01)
- ✅ Asosiy import funksiyasi
- ✅ Dry run rejimi
- ✅ Yaqinlarni import qilish
- ✅ Excel parsing
- ✅ Validatsiya

### Kelajakdagi Rejalar
- [ ] Background task (Celery) integratsiyasi
- [ ] Import tarixi va log saqlash
- [ ] Excel template yuklab olish
- [ ] Guruhlarni avtomatik yaratish
- [ ] Batch import (chunk qilib)
- [ ] Email orqali natijani yuborish
