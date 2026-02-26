# O'quvchilarni Excel orqali Import qilish API

## Umumiy Ma'lumot

Bu API Excel fayl orqali bir necha o'quvchini bir vaqtda import qilish imkonini beradi. Boshqa platformadan export qilingan o'quvchilar ma'lumotlarini import qilish uchun mo'ljallangan.

**Import jarayoni async (asinxron) tarzda ishlaydi:**
1. Fayl yuklanganda task yaratiladi va task_id qaytariladi
2. Frontend task_id orqali import statusini va natijasini so'raydi
3. Import tugagach, to'liq natija qaytariladi

## Endpoints

### 1. Import boshlash

```
POST /api/school/students/import/
```

### 2. Import statusini tekshirish

```
GET /api/school/students/import-status/{task_id}/
```

## Ruxsatlar (Permissions)

- **super_admin** - barcha filiallarda import qilishi mumkin
- **branch_admin** - faqat o'z filialida import qilishi mumkin
- Boshqa rollar import qila olmaydi

## Request Format

**Content-Type:** `multipart/form-data`

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | File | Ha | Excel fayl (.xlsx yoki .xls formatida, max 10MB) |
| branch_id | UUID | Ha | Qaysi filialga import qilish kerak |
| dry_run | Boolean | Yo'q | `true` - faqat validatsiya, `false` - haqiqiy import (default: false) |

## Excel Fayl Strukturasi

Excel faylda quyidagi ustunlar bo'lishi kerak (birinchi qator - header):

| # | Ustun | Tavsif | Misol | Majburiy |
|---|-------|--------|-------|----------|
| 0 | Shartnoma Raqam | Shartnoma raqami (ishlatilmaydi) | 12345 | Yo'q |
| 1 | FIO | O'quvchi to'liq ismi (Familiya Ism Otasining_ismi) | Valiyev Ali Karimovich | **Ha** |
| 2 | Balans | Hisob balansi | 0 yoki -50000 | Yo'q |
| 3 | Sinf | Sinf nomi (avtomatik yaratiladi agar yo'q bo'lsa) | 9-B | Yo'q |
| 4 | Guruh | Guruh nomi (ishlatilmaydi) | - | Yo'q |
| 5 | Telefon Raqam | O'quvchi telefon raqami | +998911492681 | **Ha** |
| 6 | Sinf Rahbari | Sinf rahbar (ishlatilmaydi) | Javohirbek Bahromov | Yo'q |
| 7 | Jinsi | O'quvchi jinsi | male yoki female | Yo'q |
| 8 | Tug'ilgan kuni | Tug'ilgan sana | 23/05/2010 yoki 2010-05-23 | Yo'q |
| 9 | Manzil | To'liq manzil | Uchkoprik tumani, Kenagaz MFY | Yo'q |

**Muhim eslatmalar:**
- **Column 1 (FIO)**: Familiya, Ism va Otasining ismi bo'sh joy bilan ajratilgan bo'lishi kerak
- **Column 5 (Telefon)**: Har qanday formatda bo'lishi mumkin, avtomatik tozalanadi va +998 qo'shiladi
- **Column 3 (Sinf)**: Agar sinf sistemada mavjud bo'lmasa, avtomatik yaratiladi va o'quvchi shu sinfga biriktiriladi
- **Column 2 (Balans)**: Boshlang'ich balans (so'm). Agar musbat qiymat kiritilsa, **Transaction yaratiladi** va StudentBalance avtomatik yangilanadi
  - **Transaction type**: `INCOME` (kirim)
  - **Status**: `COMPLETED` (bajarilgan)
  - **Description**: "Import: Boshlang'ich balans - [Student FIO]"
  - **CashRegister**: Asosiy kassa (avtomatik yaratiladi agar yo'q bo'lsa)
  - **Race-safe**: `select_for_update()` va atomic `F()` expressions ishlatiladi

## Response Format

### POST /api/school/students/import/ - Task yaratish

Import boshlanganda task yaratiladi va task_id qaytariladi:

```json
{
  "task_id": "e0511c5f-8ab5-4aa8-8396-1a7fee305223",
  "status": "processing",
  "message": "Import jarayoni boshlandi. Natijalarni keyinroq tekshirishingiz mumkin."
}
```

### GET /api/school/students/import-status/{task_id}/ - Status tekshirish

**PENDING - Navbatda kutmoqda:**

```json
{
  "task_id": "e0511c5f-8ab5-4aa8-8396-1a7fee305223",
  "status": "PENDING",
  "message": "Task navbatda kutmoqda..."
}
```

**STARTED - Import jarayoni davom etmoqda:**

```json
{
  "task_id": "e0511c5f-8ab5-4aa8-8396-1a7fee305223",
  "status": "STARTED",
  "message": "Import jarayoni davom etmoqda..."
}
```

**SUCCESS - Import tugadi:**

```json
{
  "task_id": "e0511c5f-8ab5-4aa8-8396-1a7fee305223",
  "status": "SUCCESS",
  "result": {
    "total": 322,
    "success": 315,
    "failed": 4,
    "skipped": 3,
    "dry_run": false,
    "errors": [
      {
        "row": 44,
        "error": "Telefon raqam noto'g'ri: '-'",
        "student": "Ali Valiyev"
      },
      {
        "row": 61,
        "error": "Telefon raqam noto'g'ri: '-'",
        "student": "Vali Aliyev"
      }
    ],
    "students": []
  }
}
```

**SUCCESS - Dry run (validatsiya) tugadi:**

```json
{
  "task_id": "17f7f69f-c0a8-43db-aba2-81acb281014a",
  "status": "SUCCESS",
  "result": {
    "total": 322,
    "success": 315,
    "failed": 0,
    "skipped": 7,
    "dry_run": true,
    "errors": [
      {
        "row": 2,
        "error": "O'quvchi +998911492681 allaqachon bu filialda ro'yxatdan o'tgan (ID: KD-25-0001)",
        "student": "Baxtiyor Joraqoziyev"
      }
    ],
    "students": []
  }
}
```

**Dry run vs Haqiqiy import farqi:**
- `dry_run: true` → `success` - yaratilishi mumkin bo'lganlar (obyektlar yaratilmagan)
- `dry_run: false` → `success` - haqiqatan yaratilganlar (obyektlar yaratilgan)
- `skipped` - ikkalasida ham allaqachon mavjud bo'lganlar

**FAILURE - Xatolik yuz berdi:**

```json
{
  "task_id": "e0511c5f-8ab5-4aa8-8396-1a7fee305223",
  "status": "FAILURE",
  "error": "Excel faylni o'qishda xatolik: ..."
}
```

## Xatolar

### 400 Bad Request

```json
{
  "file": ["Faqat Excel fayllar qabul qilinadi (.xlsx yoki .xls)"]
}
```

```json
{
  "file": ["Fayl hajmi 10MB dan oshmasligi kerak"]
}
```

```json
{
  "branch_id": ["Filial topilmadi"]
}
```

### 403 Forbidden

```json
{
  "detail": "Sizda o'quvchilarni import qilish huquqi yo'q. Faqat super_admin va branch_admin import qilishi mumkin."
}
```

```json
{
  "detail": "Siz faqat o'z filialingizda o'quvchilarni import qilishingiz mumkin."
}
```

### 401 Unauthorized

```json
{
  "detail": "Authentication credentials were not provided."
}
```

## Misol So'rovlar

### 1. Import boshlash

**cURL**

```bash
# Import boshlash
curl -X POST https://api.example.com/api/school/students/import/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@students.xlsx" \
  -F "branch_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "dry_run=false"

# Response:
# {
#   "task_id": "e0511c5f-8ab5-4aa8-8396-1a7fee305223",
#   "status": "processing",
#   "message": "Import jarayoni boshlandi..."
# }
```

**Python (requests)**

```python
import requests
import time

# 1. Import boshlash
url = "https://api.example.com/api/school/students/import/"
headers = {"Authorization": "Bearer YOUR_ACCESS_TOKEN"}
files = {"file": open("students.xlsx", "rb")}
data = {
    "branch_id": "550e8400-e29b-41d4-a716-446655440000",
    "dry_run": False
}

response = requests.post(url, headers=headers, files=files, data=data)
result = response.json()
task_id = result['task_id']
print(f"Task ID: {task_id}")

# 2. Status tekshirish (polling)
status_url = f"https://api.example.com/api/school/students/import-status/{task_id}/"

while True:
    status_response = requests.get(status_url, headers=headers)
    status_data = status_response.json()
    
    if status_data['status'] == 'SUCCESS':
        print("Import tugadi!")
        print(f"Jami: {status_data['result']['total']}")
        print(f"Muvaffaqiyatli: {status_data['result']['success']}")
        print(f"Xatolik: {status_data['result']['failed']}")
        print(f"O'tkazib yuborilgan: {status_data['result']['skipped']}")
        break
    elif status_data['status'] == 'FAILURE':
        print(f"Xatolik: {status_data['error']}")
        break
    else:
        print(f"Status: {status_data['status']}")
        time.sleep(2)  # 2 soniya kutish
```

**JavaScript (axios)**

```javascript
// 1. Import boshlash
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('branch_id', '550e8400-e29b-41d4-a716-446655440000');
formData.append('dry_run', false);

axios.post('https://api.example.com/api/school/students/import/', formData, {
  headers: {
    'Authorization': 'Bearer YOUR_ACCESS_TOKEN',
    'Content-Type': 'multipart/form-data'
  }
})
.then(response => {
  const taskId = response.data.task_id;
  console.log('Task ID:', taskId);
  
  // 2. Status tekshirish (polling)
  const checkStatus = setInterval(() => {
    axios.get(`https://api.example.com/api/school/students/import-status/${taskId}/`, {
      headers: {'Authorization': 'Bearer YOUR_ACCESS_TOKEN'}
    })
    .then(statusResponse => {
      const data = statusResponse.data;
      
      if (data.status === 'SUCCESS') {
        clearInterval(checkStatus);
        console.log('Import tugadi!');
        console.log('Jami:', data.result.total);
        console.log('Muvaffaqiyatli:', data.result.success);
        console.log('Xatolik:', data.result.failed);
        console.log('O\'tkazib yuborilgan:', data.result.skipped);
        
        // UI ni yangilash
        updateUI(data.result);
      } else if (data.status === 'FAILURE') {
        clearInterval(checkStatus);
        console.error('Xatolik:', data.error);
      } else {
        console.log('Status:', data.status);
      }
    });
  }, 2000); // Har 2 soniyada tekshirish
})
.catch(error => {
  console.error('Xatolik:', error.response.data);
});
```

### 2. Status tekshirish

**cURL**

```bash
curl -X GET https://api.example.com/api/school/students/import-status/e0511c5f-8ab5-4aa8-8396-1a7fee305223/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Import Jarayoni

1. **Excel faylni yuklash** - File MultiPartParser orqali qabul qilinadi
2. **Validatsiya** - Fayl formati va hajmi tekshiriladi
3. **Task yaratish** - Celery task queue'ga qo'shiladi va task_id qaytariladi
4. **Async import** - Background'da import jarayoni boshlanadi:
   - Excel fayl parse qilinadi
   - Har bir o'quvchi uchun:
     - User yaratiladi/tekshiriladi
     - BranchMembership yaratiladi (role=student)
     - StudentProfile yaratiladi
     - Sinf mavjudligi tekshiriladi/yaratiladi
     - O'quvchi sinfga biriktiriladi (ClassStudent)
5. **Polling** - Frontend har 2-3 soniyada status tekshiradi
6. **Natija** - Import tugagach to'liq natija qaytariladi

## Response Fields

### Import boshlash response

| Field | Type | Description |
|-------|------|-------------|
| task_id | String | Task identifikatori (UUID) |
| status | String | `processing` - jarayon boshlandi |
| message | String | Foydalanuvchi uchun xabar |

### Status tekshirish response

| Field | Type | Description |
|-------|------|-------------|
| task_id | String | Task identifikatori |
| status | String | `PENDING`, `STARTED`, `SUCCESS`, `FAILURE` |
| message | String | Status xabari (PENDING/STARTED uchun) |
| result | Object | Import natijasi (SUCCESS uchun) |
| error | String | Xatolik matni (FAILURE uchun) |

### Result object (SUCCESS holatida)

| Field | Type | Description |
|-------|------|-------------|
| total | Integer | Excel fayldagi jami o'quvchilar soni |
| success | Integer | **dry_run=true**: yaratilishi mumkin / **dry_run=false**: yaratilganlar |
| failed | Integer | Xatolik yuz bergan o'quvchilar |
| skipped | Integer | O'tkazib yuborilgan o'quvchilar (allaqachon mavjud) |
| dry_run | Boolean | `true` - validatsiya rejimi, `false` - haqiqiy import |
| errors | Array | Xatoliklar ro'yxati (har biri row, error, student) |
| students | Array | Import qilingan o'quvchilar (bo'sh massiv) |

**Muhim:** `dry_run=true` bo'lganda `success` maydonida yaratilishi mumkin bo'lgan o'quvchilar soni ko'rsatiladi (lekin haqiqatda yaratilmaydi). `dry_run=false` bo'lganda esa haqiqatan yaratilgan o'quvchilar soni qaytariladi.

## Muhim Eslatmalar

1. **Async jarayon** - Import background'da bajariladi, frontend polling orqali statusni tekshiradi
2. **Telefon raqamlar** - Har qanday formatda bo'lishi mumkin, avtomatik tozalanadi:
   - `999971000081` (12 raqam) → `+99871000081`
   - `99971000081` (11 raqam) → `+99871000081`
   - `998901234567` → `+998901234567`
3. **Atomic transaction** - Har bir o'quvchi alohida transaksiyada yaratiladi (biri xato bo'lsa, boshqalari davom etadi)
4. **Auto-generated personal_number** - Har bir o'quvchi uchun avtomatik shaxsiy raqam yaratiladi
5. **Sinf avtomatik yaratish** - Agar sinf mavjud bo'lmasa, avtomatik yaratiladi va o'quvchi shu sinfga biriktiriladi
6. **Duplicate tekshirish** - Bir xil telefon raqamli o'quvchi allaqachon mavjud bo'lsa, skip qilinadi
7. **Polling interval** - Frontend har 2-3 soniyada status tekshirishi tavsiya etiladi
8. **Task timeout** - Task max 5 minut ichida bajarilishi kerak (300 soniya)

## Kelajakdagi Takomillashlar

- [x] Import jarayoni uchun background task (Celery) ✅
- [x] Sinf avtomatik yaratish va o'quvchini sinfga biriktirish ✅
- [x] Task status polling API ✅
- [ ] Import tarixi va log saqlash
- [ ] Excel template yuklab olish endpoint
- [ ] Duplicate detection strategiyasi (telefon, ism-familiya va h.k.)
- [ ] Batch import (chunk qilib import qilish)
- [ ] Email/Telegram orqali import natijasini yuborish
- [ ] WebSocket orqali real-time status update
