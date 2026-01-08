# Dars Jadvali (Schedule) Moduli Dizayni

## Umumiy Ma'lumot

Dars jadvali moduli sinflar, o'qituvchilar va xonalar uchun haftalik dars jadvalini boshqarish uchun mo'ljallangan.

**Yangi arxitektura (2026):**
- Timetable Template har bir **chorak** uchun yaratiladi (academic_year emas)
- Choraklar akademik yil yaratilishi bilan avtomatik yaratiladi
- JWT tokendan branch_id olinadi (URL'da branch_id kerak emas)

## Choraklar Tizimi

### Avtomatik Chorak Yaratish
Akademik yil yaratilganda avtomatik 4 ta chorak yaratiladi:

- **1-chorak**: 2-sentyabr - 4-noyabr
- **2-chorak**: 10-noyabr - 27-dekabr
- **3-chorak**: 5-yanvar - 20-mart
- **4-chorak**: 28-mart - 31-may

### Chorak API Endpoints

**GET** `/api/v1/school/academic/branches/<uuid:branch_id>/quarters/current/`
- Joriy aktiv chorakni qaytaradi
- Agar `is_active=True` chorak yo'q bo'lsa, bugungi sanaga mos chorakni topadi
- Response:
  ```json
  {
    "id": "uuid",
    "academic_year": "uuid",
    "name": "1-chorak",
    "number": 1,
    "start_date": "2025-09-02",
    "end_date": "2025-11-04",
    "is_active": true,
    "created_at": "2025-09-01T10:00:00Z",
    "updated_at": "2025-09-01T10:00:00Z"
  }
  ```

**GET** `/api/v1/school/academic/academic-years/<uuid:academic_year_id>/quarters/`
- Akademik yilning barcha choraklarini qaytaradi

## Timetable Template API

### 1. Joriy Chorak Uchun Template Olish/Yaratish (Yangi!)

**GET/POST** `/api/v1/schedule/timetables/current/`

**Branch ID:** JWT tokendan olinadi (`br` claim)

**GET** - Joriy aktiv chorak uchun template qaytaradi:
- Permissions: `branch_admin`, `super_admin`, `teacher` (read-only)
- Agar template mavjud bo'lmasa: 404 error + chorak ma'lumotlari

Response (200):
```json
{
  "id": "uuid",
  "branch": "uuid",
  "branch_name": "Markaziy filial",
  "academic_year": "uuid",
  "academic_year_name": "2025-2026",
  "name": "1-chorak - 2025-2026",
  "description": "Avtomatik yaratilgan jadval - 1-chorak",
  "is_active": true,
  "effective_from": "2025-09-02",
  "effective_until": "2025-11-04",
  "slots_count": 120,
  "created_at": "2025-09-01T10:00:00Z",
  "updated_at": "2025-09-01T10:00:00Z"
}
```

Response (404 - template yo'q):
```json
{
  "error": "Joriy chorak uchun aktiv template topilmadi.",
  "quarter": {
    "id": "uuid",
    "name": "1-chorak",
    "number": 1,
    "start_date": "2025-09-02",
    "end_date": "2025-11-04"
  }
}
```

**POST** - Joriy chorak uchun yangi template yaratadi:
- Permissions: `branch_admin`, `super_admin`
- Agar template mavjud bo'lsa: mavjud templateni qaytaradi (200)
- Agar yo'q bo'lsa: yangi yaratadi (201)
- Template nomi avtomatik: `"{chorak.name} - {academic_year.name}"`
- `effective_from` = `quarter.start_date`
- `effective_until` = `quarter.end_date`
- `is_active` = `True`

Response (201 - yangi yaratildi):
```json
{
  "id": "uuid",
  "branch": "uuid",
  "branch_name": "Markaziy filial",
  "academic_year": "uuid",
  "academic_year_name": "2025-2026",
  "name": "1-chorak - 2025-2026",
  "description": "Avtomatik yaratilgan jadval - 1-chorak",
  "is_active": true,
  "effective_from": "2025-09-02",
  "effective_until": "2025-11-04",
  "slots_count": 0,
  "created_at": "2025-09-01T12:30:00Z",
  "updated_at": "2025-09-01T12:30:00Z"
}
```

**Error Responses:**
- `400`: JWT tokendan branch_id topilmadi
- `403`: Faqat adminlar POST qilishi mumkin
- `404`: Aktiv akademik yil yoki chorak topilmadi

### 2. Template Ro'yxati va Yaratish (Eski API)

**GET** `/api/v1/schedule/branches/<uuid:branch_id>/timetables/`
- Timetable templatelar ro'yxati
- Query params: `academic_year`, `is_active`, `search`

**POST** `/api/v1/schedule/branches/<uuid:branch_id>/timetables/`
- Yangi template yaratish (manual)

### 3. Template Detail

**GET/PATCH/DELETE** `/api/v1/schedule/branches/<uuid:branch_id>/timetables/<uuid:template_id>/`

## Model Struktura

### TimetableTemplate
Chorak uchun dars jadvali shabloni.

**Maydonlar:**
- `id` (UUID)
- `branch` (ForeignKey to Branch)
- `academic_year` (ForeignKey to AcademicYear)
- `name` (String, max 255)
- `description` (Text, optional)
- `is_active` (Boolean) - Faqat bitta aktiv template chorak uchun
- `effective_from` (Date) - Chorak boshlanish sanasi
- `effective_until` (Date, optional) - Chorak tugash sanasi

**Constraints:**
- Unique: [`branch`, `academic_year`, `is_active`] WHERE `is_active=True` AND `deleted_at IS NULL`

### TimetableSlot
Haftalik slot (dars vaqti).

**Maydonlar:**
- `timetable` (ForeignKey to TimetableTemplate)
- `class_obj` (ForeignKey to Class)
- `class_subject` (ForeignKey to ClassSubject)
- `day_of_week` (Choice: monday-sunday)
- `lesson_number` (Integer, 1-15)
- `start_time` (Time)
- `end_time` (Time)
- `room` (ForeignKey to Room, optional)

**Validation:**
- `start_time < end_time`
- `class_subject` must belong to `class_obj`
- `room` must belong to same branch
- **Konflikt tekshiruvi:**
  - O'qituvchi bir vaqtda ikki darsda bo'lolmaydi
  - Xona bir vaqtda ikki sinfda ishlatilolmaydi

### LessonInstance
Aniq sanada bo'ladigan real dars.

**Maydonlar:**
- `class_subject` (ForeignKey to ClassSubject)
- `date` (Date)
- `lesson_number` (Integer, 1-15)
- `start_time` (Time)
- `end_time` (Time)
- `room` (ForeignKey to Room, optional)
- `topic` (ForeignKey to LessonTopic, optional)
- `homework` (Text, optional)
- `teacher_notes` (Text, optional)
- `status` (Choice: planned, in_progress, completed, canceled)
- `is_auto_generated` (Boolean)
- `timetable_slot` (ForeignKey to TimetableSlot, optional)

## Slot API Endpoints

### Slot Ro'yxati va Yaratish

**GET** `/api/v1/schedule/branches/<uuid:branch_id>/timetables/<uuid:template_id>/slots/`
- Query params: `day_of_week`, `lesson_number`, `class_obj`, `room`

**POST** `/api/v1/schedule/branches/<uuid:branch_id>/timetables/<uuid:template_id>/slots/`
- Request body: `class_obj`, `class_subject`, `day_of_week`, `lesson_number`, `start_time`, `end_time`, `room`, `check_conflicts`

**POST** `/api/v1/schedule/branches/<uuid:branch_id>/timetables/<uuid:template_id>/slots/bulk-create/`
- Bulk slot yaratish
- Request: `{ "slots": [...], "check_conflicts": true }`

### Konflikt Tekshiruvi

**POST** `/api/v1/schedule/branches/<uuid:branch_id>/timetables/<uuid:template_id>/check-conflicts/`
- Slot yaratishdan oldin konfliktlarni tekshirish

## Lesson Instance API

### Darslar Ro'yxati

**GET** `/api/v1/schedule/branches/<uuid:branch_id>/lessons/`
- Query params: `date`, `class_subject`, `status`, `lesson_number`
- O'qituvchilar faqat o'z darslarini ko'radi

### Haftalik Jadval

**GET** `/api/v1/schedule/branches/<uuid:branch_id>/schedule/weekly/`
- Query params: `class_id` (required), `week_start` (required, Monday YYYY-MM-DD)
- Bir sinf uchun bir haftaning barcha darslarini qaytaradi

### Darslarni Generatsiya Qilish

**POST** `/api/v1/schedule/branches/<uuid:branch_id>/lessons/generate/`
- Request body:
  ```json
  {
    "timetable_id": "uuid",
    "start_date": "2025-09-02",
    "end_date": "2025-11-04",
    "skip_existing": true
  }
  ```
- Slotlardan aniq sanalar uchun darslar yaratadi
- Bayram va dam olish kunlarini o'tkazib yuboradi

## Permissions

- **branch_admin, super_admin**: Barcha operatsiyalar
- **teacher**: 
  - O'z darslarini ko'rish, mavzu va uy vazifa qo'shish
  - Templates'ni faqat o'qish
- **student, parent**: 
  - Sinf jadvalini ko'rish
  - Faqat o'qish

## Integratsiya

- **AcademicYear** - Akademik yillar
- **Quarter** - Choraklar (avtomatik yaratiladi)
- **Class** - Sinflar
- **ClassSubject** - Sinf fanlari
- **Room** - Xonalar
- **Attendance** - Davomat (darslardan foydalanadi)
