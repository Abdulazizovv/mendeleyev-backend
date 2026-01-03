# Academic System API - Frontend Developer Guide

**Version:** 1.0.0  
**Last Updated:** January 3, 2026  
**Base URL:** `/api/v1/school/branches/{branch_id}/`

**Note:** Barcha endpointlarda `{branch_id}` ni o'zingizning filial UUID bilan almashtiring.

---

## Table of Contents

1. [Authentication](#authentication)
2. [Schedule API](#schedule-api)
3. [Attendance API](#attendance-api)
4. [Grades API](#grades-api)
5. [Homework API](#homework-api)
6. [Common Patterns](#common-patterns)
7. [Error Handling](#error-handling)

---

## Authentication

Barcha API endpointlar JWT token autentifikatsiyasini talab qiladi.

### Headers
```http
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

**Note:** `X-Branch-Id` header talab qilinmaydi, chunki `branch_id` URL'ning o'zida ko'rsatilgan.

### Branch Isolation
Har bir request URL'dagi `{branch_id}` parametri orqali branch-scoped bo'ladi. Siz faqat o'z filialingiz ma'lumotlarini ko'rasiz.

---

## Schedule API

### 1. Timetable Templates (Jadval Shablonlari)

#### List Templates
```http
GET /api/v1/school/branches/{branch_id}/timetables/
```

**Query Parameters:**
- `search` (string, optional) - Nom yoki tavsif bo'yicha qidirish
- `is_active` (boolean, optional) - Faqat faol shablonlar
- `academic_year` (UUID, optional) - Akademik yil bo'yicha filtr
- `ordering` (string, optional) - Tartiblash (`-effective_from`, `name`, etc.)

**Response:** `200 OK`
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "branch": "branch-uuid",
      "branch_name": "Chilonzor filiali",
      "academic_year": "year-uuid",
      "academic_year_name": "2025-2026",
      "name": "Kuz semestri jadvali",
      "description": "2025-2026 o'quv yili kuz semestri uchun dars jadvali",
      "is_active": true,
      "effective_from": "2025-09-01",
      "effective_until": "2026-01-15",
      "slots_count": 45,
      "created_at": "2025-08-15T10:30:00Z",
      "updated_at": "2025-08-20T14:20:00Z"
    }
  ]
}
```

#### Create Template
```http
POST /api/v1/school/branches/{branch_id}/timetables/
```

**Request Body:**
```json
{
  "branch": "branch-uuid",
  "academic_year": "year-uuid",
  "name": "Bahor semestri jadvali",
  "description": "2026 yil bahor semestri uchun",
  "is_active": false,
  "effective_from": "2026-01-20",
  "effective_until": "2026-06-30"
}
```

**Response:** `201 Created`
```json
{
  "id": "new-uuid",
  "branch": "branch-uuid",
  "branch_name": "Chilonzor filiali",
  "academic_year": "year-uuid",
  "academic_year_name": "2025-2026",
  "name": "Bahor semestri jadvali",
  "description": "2026 yil bahor semestri uchun",
  "is_active": false,
  "effective_from": "2026-01-20",
  "effective_until": "2026-06-30",
  "slots_count": 0,
  "created_at": "2026-01-03T09:00:00Z",
  "updated_at": "2026-01-03T09:00:00Z"
}
```

**Validations:**
- Bir akademik yil uchun faqat bitta faol shablon bo'lishi mumkin
- `effective_from` akademik yil boshlanish sanasidan oldin bo'lmasligi kerak
- `effective_until` akademik yil tugash sanasidan keyin bo'lmasligi kerak

#### Get Template Details
```http
GET /api/v1/school/branches/{branch_id}/timetables/{template_id}/
```

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "branch": "branch-uuid",
  "branch_name": "Chilonzor filiali",
  "academic_year": "year-uuid",
  "academic_year_name": "2025-2026",
  "name": "Kuz semestri jadvali",
  "description": "2025-2026 o'quv yili kuz semestri uchun dars jadvali",
  "is_active": true,
  "effective_from": "2025-09-01",
  "effective_until": "2026-01-15",
  "slots_count": 45,
  "created_at": "2025-08-15T10:30:00Z",
  "updated_at": "2025-08-20T14:20:00Z"
}
```

#### Update Template
```http
PATCH /api/v1/school/branches/{branch_id}/timetables/{template_id}/
```

**Request Body:**
```json
{
  "description": "Yangilangan tavsif",
  "is_active": true
}
```

**Response:** `200 OK` - Updated template object

#### Delete Template
```http
DELETE /api/v1/school/branches/{branch_id}/timetables/{template_id}/
```

**Response:** `204 No Content`

---

### 2. Timetable Slots (Jadval Slotlari)

#### List Slots
```http
GET /api/v1/school/branches/{branch_id}/timetables/{template_id}/slots/
```

**Query Parameters:**
- `class_subject` (UUID, optional) - Sinf-fan ID
- `day_of_week` (string, optional) - `monday`, `tuesday`, `wednesday`, `thursday`, `friday`, `saturday`, `sunday`
- `lesson_number` (integer, optional) - Dars raqami (1-15)
- `room` (UUID, optional) - Xona ID

**Response:** `200 OK`
```json
{
  "count": 5,
  "results": [
    {
      "id": "slot-uuid",
      "timetable": "template-uuid",
      "timetable_name": "Kuz semestri jadvali",
      "class_obj": "class-uuid",
      "class_name": "5-A sinf",
      "class_subject": "class-subject-uuid",
      "subject_name": "Matematika",
      "teacher_name": "Karimov Javohir",
      "day_of_week": "monday",
      "day_of_week_display": "Dushanba",
      "lesson_number": 1,
      "start_time": "08:00:00",
      "end_time": "08:45:00",
      "room": "room-uuid",
      "room_name": "101-xona",
      "created_at": "2025-08-15T11:00:00Z",
      "updated_at": "2025-08-15T11:00:00Z"
    }
  ]
}
```

#### Create Slot
```http
POST /api/v1/school/branches/{branch_id}/timetables/{template_id}/slots/
```

**Request Body:**
```json
{
  "class_obj": "class-uuid",
  "class_subject": "class-subject-uuid",
  "day_of_week": "monday",
  "lesson_number": 2,
  "start_time": "08:50:00",
  "end_time": "09:35:00",
  "room": "room-uuid"
}
```

**Response:** `201 Created` - Created slot object

**Validations:**
- O'qituvchi bir vaqtda ikki joyda dars o'ta olmaydi (conflict detection)
- Xona bir vaqtda ikki sinf uchun band bo'lishi mumkin emas
- `start_time` < `end_time` bo'lishi kerak
- Bitta template, sinf, kun va dars raqami uchun faqat bitta slot

#### Bulk Create Slots
```http
POST /api/v1/school/branches/{branch_id}/timetables/{template_id}/slots/bulk-create/
```

**Request Body:**
```json
{
  "slots": [
    {
      "class_obj": "class-uuid",
      "class_subject": "class-subject-uuid",
      "day_of_week": "monday",
      "lesson_number": 1,
      "start_time": "08:00:00",
      "end_time": "08:45:00",
      "room": "room-uuid"
    },
    {
      "class_obj": "class-uuid",
      "class_subject": "another-subject-uuid",
      "day_of_week": "monday",
      "lesson_number": 2,
      "start_time": "08:50:00",
      "end_time": "09:35:00",
      "room": "room-uuid"
    }
  ]
}
```

**Response:** `201 Created`
```json
{
  "message": "2 ta slot muvaffaqiyatli yaratildi",
  "created_count": 2,
  "slots": [/* created slot objects */]
}
```

#### Get Slot Details
```http
GET /api/v1/school/branches/{branch_id}/timetables/{template_id}/slots/{slot_id}/
```

**Response:** `200 OK` - Slot object

#### Update Slot
```http
PATCH /api/v1/school/branches/{branch_id}/timetables/{template_id}/slots/{slot_id}/
```

**Request Body:**
```json
{
  "start_time": "09:00:00",
  "end_time": "09:45:00",
  "room": "another-room-uuid"
}
```

**Response:** `200 OK` - Updated slot object

#### Delete Slot
```http
DELETE /api/v1/school/branches/{branch_id}/timetables/{template_id}/slots/{slot_id}/
```

**Response:** `204 No Content`

---

### 3. Lesson Topics (Dars Mavzulari)

#### List Topics
```http
GET /api/v1/school/branches/{branch_id}/lesson-topics/
```

**Query Parameters:**
- `subject` (UUID, required) - Fan ID
- `quarter` (UUID, optional) - Chorak ID
- `search` (string, optional) - Mavzu nomi bo'yicha qidirish

**Response:** `200 OK`
```json
{
  "count": 3,
  "results": [
    {
      "id": "topic-uuid",
      "subject": "subject-uuid",
      "subject_name": "Matematika",
      "quarter": "quarter-uuid",
      "quarter_name": "1-chorak",
      "title": "Natural sonlar",
      "description": "Natural sonlar to'plami va ularning xossalari",
      "position": 1,
      "duration_minutes": 45,
      "created_at": "2025-08-20T10:00:00Z",
      "updated_at": "2025-08-20T10:00:00Z"
    }
  ]
}
```

#### Create Topic
```http
POST /api/v1/school/branches/{branch_id}/lesson-topics/
```

**Request Body:**
```json
{
  "subject": "subject-uuid",
  "quarter": "quarter-uuid",
  "title": "Kasr sonlar",
  "description": "Kasr sonlar bilan amallar",
  "position": 2,
  "duration_minutes": 90
}
```

**Response:** `201 Created` - Created topic object

**Validations:**
- Bir fan va chorak uchun `position` unique bo'lishi kerak

---

### 4. Lesson Instances (Darslar)

#### List Lessons
```http
GET /api/v1/school/branches/{branch_id}/lessons/
```

**Query Parameters:**
- `class_subject` (UUID, optional) - Sinf-fan ID
- `date` (date, optional) - Aniq sana (YYYY-MM-DD)
- `date_from` (date, optional) - Boshlanish sanasi
- `date_to` (date, optional) - Tugash sanasi
- `status` (string, optional) - `planned`, `completed`, `canceled`, `in_progress`
- `is_auto_generated` (boolean, optional) - Avtomatik yaratilganmi
- `topic` (UUID, optional) - Mavzu ID
- `search` (string, optional) - Qidirish

**Response:** `200 OK`
```json
{
  "count": 10,
  "results": [
    {
      "id": "lesson-uuid",
      "class_subject": "class-subject-uuid",
      "class_name": "5-A sinf",
      "subject_name": "Matematika",
      "teacher_name": "Karimov Javohir",
      "date": "2026-01-03",
      "lesson_number": 1,
      "start_time": "08:00:00",
      "end_time": "08:45:00",
      "room": "room-uuid",
      "room_name": "101-xona",
      "topic": "topic-uuid",
      "topic_title": "Natural sonlar",
      "homework": "1-mashq, sahifa 25",
      "teacher_notes": "O'quvchilar mavzuni yaxshi tushunishdi",
      "status": "completed",
      "status_display": "Tugallangan",
      "is_auto_generated": true,
      "timetable_slot": "slot-uuid",
      "created_at": "2025-12-20T10:00:00Z",
      "updated_at": "2026-01-03T09:00:00Z"
    }
  ]
}
```

#### Create Lesson
```http
POST /api/v1/school/branches/{branch_id}/lessons/
```

**Request Body:**
```json
{
  "class_subject": "class-subject-uuid",
  "date": "2026-01-10",
  "lesson_number": 3,
  "start_time": "10:00:00",
  "end_time": "10:45:00",
  "room": "room-uuid",
  "topic": "topic-uuid",
  "homework": "2-mashq, sahifa 30",
  "teacher_notes": "Qo'shimcha mashqlar kerak",
  "status": "planned"
}
```

**Response:** `201 Created` - Created lesson object

**Validations:**
- Bir sinf-fan, sana va dars raqami uchun faqat bitta dars
- `start_time` < `end_time` bo'lishi kerak

#### Get Lesson Details
```http
GET /api/v1/school/branches/{branch_id}/lessons/{lesson_id}/
```

**Response:** `200 OK` - Lesson object

#### Update Lesson
```http
PATCH /api/v1/school/branches/{branch_id}/lessons/{lesson_id}/
```

**Request Body:**
```json
{
  "status": "completed",
  "topic": "topic-uuid",
  "homework": "3-mashq, sahifa 35",
  "teacher_notes": "Barcha o'quvchilar ishtirok etdi"
}
```

**Response:** `200 OK` - Updated lesson object

#### Generate Lessons
```http
POST /api/v1/school/branches/{branch_id}/lessons/generate/
```

**Request Body:**
```json
{
  "template_id": "template-uuid",
  "start_date": "2026-01-06",
  "end_date": "2026-01-12",
  "skip_holidays": true
}
```

**Response:** `200 OK`
```json
{
  "message": "Darslar muvaffaqiyatli yaratildi",
  "created_count": 45,
  "skipped_count": 5,
  "existing_count": 0
}
```

**Note:** Bu endpoint jadval shablonidan belgilangan sana oralig'ida darslarni avtomatik yaratadi.

---

## Attendance API

### 1. Lesson Attendance (Dars Davomati)

#### List Attendance
```http
GET /api/v1/school/branches/{branch_id}/attendance/
```

**Query Parameters:**
- `class_subject` (UUID, optional) - Sinf-fan ID
- `date` (date, optional) - Aniq sana
- `date_from` (date, optional) - Boshlanish sanasi
- `date_to` (date, optional) - Tugash sanasi
- `is_locked` (boolean, optional) - Bloklangan davomatlar
- `lesson` (UUID, optional) - Dars ID

**Response:** `200 OK`
```json
{
  "count": 5,
  "results": [
    {
      "id": "attendance-uuid",
      "lesson": "lesson-uuid",
      "lesson_details": {
        "date": "2026-01-03",
        "lesson_number": 1,
        "class_name": "5-A sinf",
        "subject_name": "Matematika"
      },
      "class_subject": "class-subject-uuid",
      "class_name": "5-A sinf",
      "subject_name": "Matematika",
      "teacher_name": "Karimov Javohir",
      "date": "2026-01-03",
      "lesson_number": 1,
      "is_locked": false,
      "locked_at": null,
      "locked_by": null,
      "notes": "",
      "present_count": 18,
      "absent_count": 2,
      "late_count": 1,
      "total_students": 21,
      "records_count": 21,
      "created_at": "2026-01-03T08:00:00Z",
      "updated_at": "2026-01-03T08:30:00Z"
    }
  ]
}
```

#### Create Attendance
```http
POST /api/v1/school/branches/{branch_id}/attendance/
```

**Request Body:**
```json
{
  "lesson": "lesson-uuid",
  "class_subject": "class-subject-uuid",
  "date": "2026-01-03",
  "lesson_number": 1,
  "notes": "Barcha o'quvchilar keldi"
}
```

**Response:** `201 Created` - Created attendance object

**Validations:**
- Bir sinf-fan, sana va dars raqami uchun faqat bitta davomat

#### Get Attendance Details
```http
GET /api/v1/school/branches/{branch_id}/attendance/{attendance_id}/
```

**Response:** `200 OK` - Attendance object with records

#### Update Attendance
```http
PATCH /api/v1/school/branches/{branch_id}/attendance/{attendance_id}/
```

**Request Body:**
```json
{
  "notes": "Yangilangan eslatma"
}
```

**Response:** `200 OK` - Updated attendance object

**Note:** Bloklangan davomatni yangilab bo'lmaydi.

#### Lock Attendance
```http
POST /api/v1/school/branches/{branch_id}/attendance/lock-unlock/
```

**Request Body:**
```json
{
  "attendance_ids": ["attendance-uuid"],
  "action": "lock"
}
```

**Response:** `200 OK`
```json
{
  "message": "Davomat bloklandi",
  "is_locked": true,
  "locked_at": "2026-01-03T15:00:00Z"
}
```

**Note:** Bloklangan davomatni o'zgartirish mumkin emas (o'quvchi yozuvlari ham).

#### Unlock Attendance
```http
POST /api/v1/school/branches/{branch_id}/attendance/lock-unlock/
```

**Request Body:**
```json
{
  "attendance_ids": ["attendance-uuid"],
  "action": "unlock"
}
```

**Response:** `200 OK`
```json
{
  "message": "Davomat bloki olib tashlandi",
  "is_locked": false,
  "locked_at": null
}
```

---

### 2. Student Attendance Records (O'quvchi Davomat Yozuvlari)

#### List Records
```http
GET /api/v1/school/branches/{branch_id}/attendance/{attendance_id}/records/
```

**Query Parameters:**
- `student` (UUID, optional) - O'quvchi ID
- `status` (string, optional) - `present`, `absent`, `late`, `excused`, `sick`

**Response:** `200 OK`
```json
{
  "count": 21,
  "results": [
    {
      "id": "record-uuid",
      "attendance": "attendance-uuid",
      "attendance_date": "2026-01-03",
      "student": "student-uuid",
      "student_name": "Aliyev Sardor",
      "student_personal_number": "TAS-2024-0001",
      "status": "present",
      "status_display": "Keldi",
      "notes": "",
      "marked_at": "2026-01-03T08:05:00Z",
      "created_at": "2026-01-03T08:05:00Z",
      "updated_at": "2026-01-03T08:05:00Z"
    }
  ]
}
```

#### Create Record
```http
POST /api/v1/school/branches/{branch_id}/attendance/{attendance_id}/records/
```

**Request Body:**
```json
{
  "student": "student-uuid",
  "status": "late",
  "notes": "10 daqiqa kechikdi"
}
```

**Response:** `201 Created` - Created record object

**Validations:**
- Bir davomat uchun bir o'quvchidan faqat bitta yozuv
- Bloklangan davomatga yozuv qo'shib bo'lmaydi

#### Update Record
```http
PATCH /api/v1/school/branches/{branch_id}/attendance/{attendance_id}/records/{record_id}/
```

**Request Body:**
```json
{
  "status": "excused",
  "notes": "Sababli kelmadi"
}
```

**Response:** `200 OK` - Updated record object

**Note:** Bloklangan davomatning yozuvini yangilab bo'lmaydi.

---

### 3. Attendance Statistics (Davomat Statistikasi)

#### List Statistics
```http
GET /api/v1/school/branches/{branch_id}/attendance/statistics/student/
```

**Query Parameters:**
- `student` (UUID, optional) - O'quvchi ID
- `class_subject` (UUID, optional) - Sinf-fan ID
- `start_date` (date, optional) - Boshlanish sanasi
- `end_date` (date, optional) - Tugash sanasi

**Response:** `200 OK`
```json
{
  "count": 5,
  "results": [
    {
      "id": "stats-uuid",
      "student": "student-uuid",
      "student_name": "Aliyev Sardor",
      "class_subject": "class-subject-uuid",
      "class_name": "5-A sinf",
      "subject_name": "Matematika",
      "start_date": "2025-09-01",
      "end_date": "2025-12-31",
      "total_lessons": 60,
      "present_count": 55,
      "absent_count": 3,
      "late_count": 2,
      "excused_count": 0,
      "sick_count": 0,
      "attendance_rate": 91.67,
      "last_calculated": "2026-01-03T10:00:00Z",
      "created_at": "2025-09-01T09:00:00Z",
      "updated_at": "2026-01-03T10:00:00Z"
    }
  ]
}
```

**Note:** Statistikalar avtomatik hisoblanmaydi. Hisoblab olish uchun recalculate endpoint'dan foydalaning.

#### Recalculate Statistics
```http
POST /api/v1/school/branches/{branch_id}/attendance/statistics/student/
```

**Request Body:**
```json
{
  "student": "student-uuid",
  "class_subject": "class-subject-uuid",
  "start_date": "2025-09-01",
  "end_date": "2026-01-03"
}
```

**Response:** `200 OK`
```json
{
  "message": "Statistika qayta hisoblandi",
  "statistics": {/* statistics object */}
}
```

---

## Grades API

### 1. Assessment Types (Nazorat Turlari)

#### List Assessment Types
```http
GET /api/v1/school/branches/{branch_id}/assessment-types/
```

**Query Parameters:**
- `is_active` (boolean, optional) - Faqat faol turlar
- `search` (string, optional) - Nom yoki kod bo'yicha qidirish

**Response:** `200 OK`
```json
{
  "count": 4,
  "results": [
    {
      "id": "type-uuid",
      "branch": "branch-uuid",
      "branch_name": "Chilonzor filiali",
      "name": "Og'zaki nazorat",
      "code": "oral",
      "description": "Og'zaki savol-javob",
      "default_max_score": 5.0,
      "default_weight": 1.0,
      "color": "#3498db",
      "is_active": true,
      "created_at": "2025-08-15T09:00:00Z",
      "updated_at": "2025-08-15T09:00:00Z"
    }
  ]
}
```

#### Create Assessment Type
```http
POST /api/v1/school/branches/{branch_id}/assessment-types/
```

**Request Body:**
```json
{
  "branch": "branch-uuid",
  "name": "Test",
  "code": "test",
  "description": "Yozma test",
  "default_max_score": 20.0,
  "default_weight": 2.0,
  "color": "#e74c3c",
  "is_active": true
}
```

**Response:** `201 Created` - Created type object

**Validations:**
- Bir filial uchun `code` unique bo'lishi kerak

---

### 2. Assessments (Nazoratlar)

#### List Assessments
```http
GET /api/v1/school/branches/{branch_id}/assessments/
```

**Query Parameters:**
- `class_subject` (UUID, optional) - Sinf-fan ID
- `quarter` (UUID, optional) - Chorak ID
- `assessment_type` (UUID, optional) - Nazorat turi ID
- `date_from` (date, optional) - Boshlanish sanasi
- `date_to` (date, optional) - Tugash sanasi
- `is_locked` (boolean, optional) - Bloklangan nazoratlar
- `search` (string, optional) - Qidirish

**Response:** `200 OK`
```json
{
  "count": 5,
  "results": [
    {
      "id": "assessment-uuid",
      "class_subject": "class-subject-uuid",
      "class_name": "5-A sinf",
      "subject_name": "Matematika",
      "teacher_name": "Karimov Javohir",
      "assessment_type": "type-uuid",
      "assessment_type_name": "Nazorat ishi",
      "lesson": "lesson-uuid",
      "quarter": "quarter-uuid",
      "quarter_name": "1-chorak",
      "title": "1-chorak yakuniy nazorat ishi",
      "description": "Natural sonlar mavzusi bo'yicha",
      "date": "2025-12-20",
      "max_score": 20.0,
      "weight": 3.0,
      "is_locked": true,
      "locked_at": "2025-12-21T10:00:00Z",
      "notes": "",
      "average_score": 16.5,
      "grades_count": 20,
      "completion_rate": 95.24,
      "created_at": "2025-12-15T10:00:00Z",
      "updated_at": "2025-12-21T10:00:00Z"
    }
  ]
}
```

#### Create Assessment
```http
POST /api/v1/school/branches/{branch_id}/assessments/
```

**Request Body:**
```json
{
  "class_subject": "class-subject-uuid",
  "assessment_type": "type-uuid",
  "lesson": "lesson-uuid",
  "quarter": "quarter-uuid",
  "title": "2-chorak oraliq nazorat",
  "description": "Kasr sonlar bo'yicha",
  "date": "2026-02-15",
  "max_score": 20.0,
  "weight": 2.0,
  "notes": "O'quvchilar yaxshi tayyorlangan"
}
```

**Response:** `201 Created` - Created assessment object

**Validations:**
- Chorak sinf akademik yiliga tegishli bo'lishi kerak
- Nazorat turi filialga tegishli bo'lishi kerak

#### Get Assessment Details
```http
GET /api/v1/school/branches/{branch_id}/assessments/{assessment_id}/
```

**Response:** `200 OK` - Assessment object with grades

#### Update Assessment
```http
PATCH /api/v1/school/branches/{branch_id}/assessments/{assessment_id}/
```

**Request Body:**
```json
{
  "title": "Yangilangan sarlavha",
  "description": "Yangilangan tavsif"
}
```

**Response:** `200 OK` - Updated assessment object

**Note:** Bloklangan nazoratni yangilab bo'lmaydi.

#### Lock Assessment
```http
POST /api/v1/school/branches/{branch_id}/grades/lock-unlock/
```

**Request Body:**
```json
{
  "assessment_ids": ["assessment-uuid"],
  "action": "lock"
}
```

**Response:** `200 OK`
```json
{
  "message": "Nazorat bloklandi",
  "is_locked": true,
  "locked_at": "2026-01-03T15:00:00Z"
}
```

**Note:** Bloklangan nazoratning baholarini o'zgartirish mumkin emas.

#### Unlock Assessment
```http
POST /api/v1/school/branches/{branch_id}/grades/lock-unlock/
```

**Request Body:**
```json
{
  "assessment_ids": ["assessment-uuid"],
  "action": "unlock"
}
```

**Response:** `200 OK`
```json
{
  "message": "Nazorat bloki olib tashlandi",
  "is_locked": false,
  "locked_at": null
}
```

---

### 3. Grades (Baholar)

#### List Grades
```http
GET /api/v1/school/branches/{branch_id}/grades/
```

**Query Parameters:**
- `assessment` (UUID, optional) - Nazorat ID
- `student` (UUID, optional) - O'quvchi ID
- `class_subject` (UUID, optional) - Sinf-fan ID
- `quarter` (UUID, optional) - Chorak ID

**Response:** `200 OK`
```json
{
  "count": 20,
  "results": [
    {
      "id": "grade-uuid",
      "assessment": "assessment-uuid",
      "assessment_title": "1-chorak yakuniy nazorat ishi",
      "assessment_max_score": 20.0,
      "student": "student-uuid",
      "student_name": "Aliyev Sardor",
      "student_personal_number": "TAS-2024-0001",
      "score": 18.0,
      "calculated_score": 4.5,
      "final_score": 4.5,
      "override_reason": null,
      "notes": "Zo'r ishladi",
      "graded_at": "2025-12-20T14:30:00Z",
      "created_at": "2025-12-20T14:30:00Z",
      "updated_at": "2025-12-20T14:30:00Z"
    }
  ]
}
```

#### Create Grade
```http
POST /api/v1/school/branches/{branch_id}/grades/
```

**Request Body:**
```json
{
  "assessment": "assessment-uuid",
  "student": "student-uuid",
  "score": 17.5,
  "notes": "Yaxshi natija"
}
```

**Response:** `201 Created`
```json
{
  "id": "grade-uuid",
  "assessment": "assessment-uuid",
  "assessment_title": "2-chorak oraliq nazorat",
  "assessment_max_score": 20.0,
  "student": "student-uuid",
  "student_name": "Aliyev Sardor",
  "score": 17.5,
  "calculated_score": 4.4,
  "final_score": 4.4,
  "override_reason": null,
  "notes": "Yaxshi natija",
  "graded_at": "2026-01-03T11:00:00Z"
}
```

**Validations:**
- Bir nazorat uchun bir o'quvchidan faqat bitta baho
- Bloklangan nazoratga baho qo'shib bo'lmaydi
- `score` <= `assessment.max_score` bo'lishi kerak

**Note:** `calculated_score` va `final_score` avtomatik hisoblanadi (5-ballik tizimga konvertatsiya).

#### Update Grade
```http
PATCH /api/v1/school/branches/{branch_id}/grades/{grade_id}/
```

**Request Body:**
```json
{
  "score": 19.0,
  "notes": "Yangilangan natija"
}
```

**Response:** `200 OK` - Updated grade object

**Note:** Bloklangan nazoratning bahosini yangilab bo'lmaydi.

#### Override Final Score
```http
POST /api/v1/school/branches/{branch_id}/grades/{grade_id}/override/
```

**Request Body:**
```json
{
  "final_score": 5.0,
  "override_reason": "O'qituvchi qaror bo'yicha 5 qo'yildi"
}
```

**Response:** `200 OK`
```json
{
  "message": "Final baho o'zgartirildi",
  "grade": {/* grade object */}
}
```

**Note:** Grade modelida override uchun maxsus endpoint bo'lishi mumkin emas. Bu funksiyani grade update orqali amalga oshiring.

---

### 4. Quarter Grades (Chorak Baholari)

#### List Quarter Grades
```http
GET /api/v1/school/branches/{branch_id}/quarter-grades/
```

**Query Parameters:**
- `student` (UUID, optional) - O'quvchi ID
- `class_subject` (UUID, optional) - Sinf-fan ID
- `quarter` (UUID, optional) - Chorak ID
- `is_locked` (boolean, optional) - Bloklangan chorak baholari

**Response:** `200 OK`
```json
{
  "count": 8,
  "results": [
    {
      "id": "quarter-grade-uuid",
      "student": "student-uuid",
      "student_name": "Aliyev Sardor",
      "class_subject": "class-subject-uuid",
      "class_name": "5-A sinf",
      "subject_name": "Matematika",
      "quarter": "quarter-uuid",
      "quarter_name": "1-chorak",
      "calculated_grade": 4.5,
      "final_grade": 5.0,
      "override_reason": "O'qituvchi qaror bo'yicha",
      "is_locked": true,
      "locked_at": "2025-12-25T12:00:00Z",
      "last_calculated": "2025-12-24T18:00:00Z",
      "assessments_count": 8,
      "average_score": 4.5,
      "created_at": "2025-12-01T10:00:00Z",
      "updated_at": "2025-12-25T12:00:00Z"
    }
  ]
}
```

#### Get Quarter Grade Details
```http
GET /api/v1/school/branches/{branch_id}/quarter-grades/{quarter_grade_id}/
```

**Response:** `200 OK` - Quarter grade object with breakdown

#### Recalculate Quarter Grade
```http
POST /api/v1/school/branches/{branch_id}/quarter-grades/calculate/
```

**Request Body:**
```json
{
  "student": "student-uuid",
  "class_subject": "class-subject-uuid",
  "quarter": "quarter-uuid"
}
```

**Response:** `200 OK`
```json
{
  "message": "Chorak bahosi qayta hisoblandi",
  "quarter_grade": {/* updated quarter grade */}
}
```

**Note:** Bu endpoint barcha nazorat baholaridan weighted average hisoblab, chorak bahosini yangilaydi.

---

## Homework API

### 1. Homework (Uy Vazifalar)

#### List Homework
```http
GET /api/v1/school/homework/
```

**Query Parameters:**
- `class_subject` (UUID, optional) - Sinf-fan ID
- `status` (string, optional) - `active`, `closed`, `archived`
- `assigned_date_from` (date, optional) - Berilgan sana (boshlanish)
- `assigned_date_to` (date, optional) - Berilgan sana (tugash)
- `due_date_from` (date, optional) - Topshirish muddati (boshlanish)
- `due_date_to` (date, optional) - Topshirish muddati (tugash)
- `search` (string, optional) - Sarlavha yoki tavsif bo'yicha qidirish

**Response:** `200 OK`
```json
{
  "count": 5,
  "results": [
    {
      "id": "homework-uuid",
      "class_subject": "class-subject-uuid",
      "class_name": "5-A sinf",
      "subject_name": "Matematika",
      "teacher_name": "Karimov Javohir",
      "lesson": "lesson-uuid",
      "assessment": "assessment-uuid",
      "title": "Natural sonlar mavzusi bo'yicha mashqlar",
      "description": "Darslikdan 1-5 mashqlarni bajaring. Har bir masalaning yechimini to'liq yozing.",
      "assigned_date": "2026-01-03",
      "due_date": "2026-01-10",
      "allow_late_submission": true,
      "max_score": 20.0,
      "attachments": {
        "files": [
          {
            "name": "mashqlar.pdf",
            "url": "/media/homework/mashqlar.pdf",
            "size": 245678
          }
        ]
      },
      "status": "active",
      "status_display": "Faol",
      "notes": "",
      "submissions_count": 12,
      "total_students": 21,
      "completion_rate": 57.14,
      "is_overdue": false,
      "created_at": "2026-01-03T09:00:00Z",
      "updated_at": "2026-01-03T09:00:00Z"
    }
  ]
}
```

#### Create Homework
```http
POST /api/v1/school/homework/
```

**Request Body:**
```json
{
  "class_subject": "class-subject-uuid",
  "lesson": "lesson-uuid",
  "assessment": "assessment-uuid",
  "title": "Kasr sonlar bo'yicha mashqlar",
  "description": "Darslikdan 10-15 mashqlarni bajaring",
  "assigned_date": "2026-01-03",
  "due_date": "2026-01-10",
  "allow_late_submission": true,
  "max_score": 20.0,
  "attachments": {
    "files": [
      {
        "name": "qoshimcha_mashqlar.pdf",
        "url": "/media/homework/qoshimcha_mashqlar.pdf"
      }
    ]
  },
  "notes": "Qo'shimcha masalalar ixtiyoriy"
}
```

**Response:** `201 Created` - Created homework object

**Validations:**
- `due_date` >= `assigned_date` bo'lishi kerak

#### Get Homework Details
```http
GET /api/v1/school/homework/{homework_id}/
```

**Response:** `200 OK` - Homework object with submissions

#### Update Homework
```http
PATCH /api/v1/school/homework/{homework_id}/
```

**Request Body:**
```json
{
  "due_date": "2026-01-12",
  "description": "Yangilangan tavsif"
}
```

**Response:** `200 OK` - Updated homework object

#### Close Homework
```http
POST /api/v1/school/homework/{homework_id}/close/
```

**Response:** `200 OK`
```json
{
  "message": "Uy vazifa yopildi",
  "status": "closed"
}
```

**Note:** Yopilgan uy vazifaga yangi topshiriq qo'shib bo'lmaydi.

#### Reopen Homework
```http
POST /api/v1/school/homework/{homework_id}/reopen/
```

**Response:** `200 OK`
```json
{
  "message": "Uy vazifa qayta ochildi",
  "status": "active"
}
```

---

### 2. Homework Submissions (Topshiriqlar)

#### List Submissions
```http
GET /api/v1/school/submissions/
```

**Query Parameters:**
- `homework` (UUID, optional) - Uy vazifa ID
- `student` (UUID, optional) - O'quvchi ID
- `status` (string, optional) - `not_submitted`, `submitted`, `late`, `graded`, `returned`
- `is_late` (boolean, optional) - Kechikkan topshiriqlar

**Response:** `200 OK`
```json
{
  "count": 21,
  "results": [
    {
      "id": "submission-uuid",
      "homework": "homework-uuid",
      "homework_title": "Natural sonlar mavzusi bo'yicha mashqlar",
      "student": "student-uuid",
      "student_name": "Aliyev Sardor",
      "student_personal_number": "TAS-2024-0001",
      "submission_text": "Barcha mashqlarni bajardim. Yechimlar quyida...",
      "attachments": {
        "files": [
          {
            "name": "yechim.pdf",
            "url": "/media/submissions/yechim.pdf",
            "size": 123456
          }
        ]
      },
      "status": "graded",
      "status_display": "Baholangan",
      "is_late": false,
      "submitted_at": "2026-01-09T20:00:00Z",
      "score": 18.0,
      "teacher_feedback": "Zo'r ishlading! Barcha yechimlar to'g'ri.",
      "graded_at": "2026-01-10T10:00:00Z",
      "created_at": "2026-01-09T20:00:00Z",
      "updated_at": "2026-01-10T10:00:00Z"
    }
  ]
}
```

#### Create Submission
```http
POST /api/v1/school/submissions/
```

**Request Body:**
```json
{
  "homework": "homework-uuid",
  "student": "student-uuid",
  "submission_text": "Mashqlarni bajardim",
  "attachments": {
    "files": [
      {
        "name": "mening_yechimim.pdf",
        "url": "/media/submissions/mening_yechimim.pdf"
      }
    ]
  }
}
```

**Response:** `201 Created`
```json
{
  "id": "submission-uuid",
  "homework": "homework-uuid",
  "student": "student-uuid",
  "submission_text": "Mashqlarni bajardim",
  "attachments": {/* attachments */},
  "status": "submitted",
  "is_late": false,
  "submitted_at": "2026-01-09T20:00:00Z"
}
```

**Validations:**
- Bir uy vazifa uchun bir o'quvchidan faqat bitta topshiriq
- Yopilgan uy vazifaga topshirib bo'lmaydi
- Agar `allow_late_submission=false` bo'lsa, muddatdan keyin topshirib bo'lmaydi

**Note:** `is_late` va `status` avtomatik o'rnatiladi.

#### Update Submission
```http
PATCH /api/v1/school/submissions/{submission_id}/
```

**Request Body:**
```json
{
  "submission_text": "Yangilangan yechim",
  "attachments": {/* new attachments */}
}
```

**Response:** `200 OK` - Updated submission object

**Note:** Baholangan topshiriqni o'quvchi yangilay olmaydi.

#### Grade Submission
```http
POST /api/v1/school/submissions/{submission_id}/grade/
```

**Request Body:**
```json
{
  "score": 19.0,
  "teacher_feedback": "Zo'r natija! Kichik xatolik bor."
}
```

**Response:** `200 OK`
```json
{
  "message": "Topshiriq baholandi",
  "submission": {/* updated submission */}
}
```

#### Return Submission
```http
POST /api/v1/school/submissions/{submission_id}/return/
```

**Request Body:**
```json
{
  "teacher_feedback": "Qayta ko'rib chiqing, 3-mashq noto'g'ri"
}
```

**Response:** `200 OK`
```json
{
  "message": "Topshiriq qaytarildi",
  "submission": {/* submission with status=returned */}
}
```

---

## Common Patterns

### Pagination

Barcha list endpointlar pagination qo'llab-quvvatlaydi:

```json
{
  "count": 100,
  "next": "http://api.example.com/endpoint/?page=2",
  "previous": null,
  "results": [/* array of objects */]
}
```

Query parameters:
- `page` (integer) - Sahifa raqami (default: 1)
- `page_size` (integer) - Har sahifada nechta element (default: 20, max: 100)

**Example:**
```http
GET /api/v1/school/branches/{branch_id}/lessons/?page=2&page_size=50
```

### Filtering

Ko'plab endpointlar filter parametrlarini qo'llab-quvvatlaydi:

```http
GET /api/v1/school/branches/{branch_id}/grades/?assessment=uuid&student=uuid
GET /api/v1/school/branches/{branch_id}/attendance/?date_from=2026-01-01&date_to=2026-01-31
```

### Searching

Search parametri nom, tavsif va boshqa matn maydonlari bo'yicha qidiradi:

```http
GET /api/v1/school/branches/{branch_id}/timetables/?search=bahor
GET /api/v1/school/homework/?search=matematika
```

### Ordering

Ko'pgina list endpointlar tartiblashni qo'llab-quvvatlaydi:

```http
GET /api/v1/school/branches/{branch_id}/lessons/?ordering=-date
GET /api/v1/school/branches/{branch_id}/grades/?ordering=student__user_branch__user__first_name
```

- `-` prefiksi: kamayish tartibida (descending)
- Prefiksiz: o'sish tartibida (ascending)

### Soft Delete

Barcha delete operatsiyalar soft delete (mantiqiy o'chirish) bo'lib, ma'lumotlar bazadan o'chirilmaydi, faqat `deleted_at` maydoni o'rnatiladi. O'chirilgan obyektlar API'da ko'rinmaydi.

---

## Error Handling

### HTTP Status Codes

- `200 OK` - Muvaffaqiyatli so'rov
- `201 Created` - Yangi obyekt yaratildi
- `204 No Content` - Muvaffaqiyatli o'chirildi
- `400 Bad Request` - Noto'g'ri so'rov (validatsiya xatoliklari)
- `401 Unauthorized` - Autentifikatsiya talab qilinadi
- `403 Forbidden` - Ruxsat yo'q
- `404 Not Found` - Obyekt topilmadi
- `409 Conflict` - Konflikt (masalan, unique constraint)
- `500 Internal Server Error` - Server xatosi

### Error Response Format

```json
{
  "detail": "Xato haqida tavsif"
}
```

yoki validatsiya xatoliklari uchun:

```json
{
  "field_name": [
    "Xato haqida tavsif 1",
    "Xato haqida tavsif 2"
  ],
  "another_field": [
    "Boshqa xato"
  ]
}
```

### Common Errors

#### 400 Bad Request - Validatsiya Xatoligi
```json
{
  "due_date": [
    "Topshirish muddati berilgan sanadan keyin bo'lishi kerak."
  ]
}
```

#### 401 Unauthorized
```json
{
  "detail": "Autentifikatsiya ma'lumotlari berilmagan."
}
```

#### 403 Forbidden
```json
{
  "detail": "Siz ushbu amalni bajarish uchun ruxsatga ega emassiz."
}
```

#### 404 Not Found
```json
{
  "detail": "Topilmadi."
}
```

#### 409 Conflict
```json
{
  "non_field_errors": [
    "Bu sinf-fan, sana va dars raqami uchun dars allaqachon mavjud."
  ]
}
```

---

## Field Types Reference

### Date & Time Fields

- `date` - Sana (YYYY-MM-DD format): `"2026-01-03"`
- `time` - Vaqt (HH:MM:SS format): `"08:00:00"`
- `datetime` - Sana va vaqt (ISO 8601 format): `"2026-01-03T09:00:00Z"`

### Status Fields

**Lesson Status:**
- `planned` - Rejalashtirilgan
- `completed` - Tugallangan
- `canceled` - Bekor qilingan
- `in_progress` - Davom etmoqda

**Attendance Status:**
- `present` - Keldi
- `absent` - Kelmadi
- `late` - Kechikdi
- `excused` - Sababli
- `sick` - Kasal

**Homework Status:**
- `active` - Faol
- `closed` - Yopilgan
- `archived` - Arxivlangan

**Submission Status:**
- `not_submitted` - Topshirilmagan
- `submitted` - Topshirilgan
- `late` - Kechikkan
- `graded` - Baholangan
- `returned` - Qaytarilgan

### Day of Week Values

- `monday` - Dushanba
- `tuesday` - Seshanba
- `wednesday` - Chorshanba
- `thursday` - Payshanba
- `friday` - Juma
- `saturday` - Shanba
- `sunday` - Yakshanba

---

## JavaScript Examples

### Fetch Template

```javascript
// GET request
async function getTemplates() {
  try {
    const response = await fetch(`/api/v1/school/branches/${branchId}/timetables/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('Templates:', data.results);
    return data;
  } catch (error) {
    console.error('Error fetching templates:', error);
  }
}

// POST request
async function createLesson(lessonData) {
  try {
    const response = await fetch(`/api/v1/school/branches/${branchId}/lessons/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(lessonData)
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      console.error('Validation errors:', errorData);
      throw new Error('Dars yaratishda xatolik');
    }
    
    const data = await response.json();
    console.log('Created lesson:', data);
    return data;
  } catch (error) {
    console.error('Error creating lesson:', error);
  }
}

// PATCH request
async function updateAttendance(attendanceId, updates) {
  try {
    const response = await fetch(
      `/api/v1/school/branches/${branchId}/attendance/${attendanceId}/`,
      {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updates)
      }
    );
    
    if (!response.ok) {
      throw new Error('Davomatni yangilashda xatolik');
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error updating attendance:', error);
  }
}

// Custom action
async function lockAttendance(attendanceId) {
  try {
    const response = await fetch(
      `/api/v1/school/branches/${branchId}/attendance/lock-unlock/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          attendance_ids: [attendanceId],
          action: 'lock'
        })
      }
    );
    
    if (!response.ok) {
      throw new Error('Davomatni bloklashda xatolik');
    }
    
    const data = await response.json();
    console.log(data.message); // "Davomat bloklandi"
    return data;
  } catch (error) {
    console.error('Error locking attendance:', error);
  }
}
```

---

## Best Practices

### 1. Always Include Authentication
Har doim `Authorization` header'ida JWT token yuboring.

### 2. Branch ID in URL
Barcha endpointlar URL'da `{branch_id}` parametrini talab qiladi. O'z filial UUID'ingizni kiriting.

### 3. Handle Errors Properly
Har bir so'rovda error handling qo'shing va foydalanuvchiga tushunarli xatolik xabarlarini ko'rsating.

### 4. Use Pagination
Katta ma'lumotlar to'plami bilan ishlashda pagination parametrlaridan foydalaning.

### 5. Cache Static Data
Assessment types, subjects kabi kam o'zgaradigan ma'lumotlarni cache qiling.

### 6. Validate Before Submit
Backend validatsiyaga ishonish bilan birga, frontend'da ham asosiy validatsiyalarni amalga oshiring (muddatlar, required fieldlar, etc.)

### 7. Check Lock Status
Davomatlar, nazoratlar va chorak baholarini yangilashdan oldin `is_locked` statusini tekshiring.

### 8. Use Filters Efficiently
Server'ga ortiqcha yukni kamaytirish uchun filtrlardan samarali foydalaning.

---

## Support & Questions

Agar API haqida savollaringiz bo'lsa yoki muammoga duch kelsangiz:

1. Avval bu hujjatni to'liq o'qib chiqing
2. Error response'ni diqqat bilan tekshiring
3. Browser DevTools'da network tab'ni tekshiring
4. Backend development team bilan bog'laning

**Contact:** backend-team@example.com

---

**Last Updated:** January 3, 2026  
**API Version:** 1.0.0  
**Documentation Status:** Production Ready ✅
