# Davomat (Attendance) Moduli Dizayni

## Umumiy Ma'lumot

Davomat moduli o'quvchilarning darslarga qatnashishini kuzatish va boshqarish uchun mo'ljallangan.

## Model Struktura

### LessonAttendance
Har bir dars uchun davomat yozuvi.

**Maydonlar:**
- `id` (UUID) - Davomat yozuvi ID
- `class_subject` (ForeignKey to ClassSubject) - Sinf fani
- `lesson_date` (Date) - Dars sanasi
- `lesson_number` (Integer, 1-8) - Dars raqami (1-dars, 2-dars, ...)
- `teacher` (ForeignKey to BranchMembership) - Dars o'tkazgan o'qituvchi
- `topic` (String, optional) - Dars mavzusi
- `notes` (Text, optional) - Qo'shimcha eslatmalar
- `created_by`, `updated_by` - Audit trail
- `created_at`, `updated_at` - Vaqt

**Meta:**
- `unique_together`: [('class_subject', 'lesson_date', 'lesson_number')]
- `indexes`: [('class_subject', 'lesson_date'), ('lesson_date')]

### StudentAttendanceRecord
Har bir o'quvchining har bir dars uchun davomat yozuvi.

**Maydonlar:**
- `id` (UUID) - Davomat yozuvi ID
- `lesson_attendance` (ForeignKey to LessonAttendance) - Dars davomati
- `student_profile` (ForeignKey to StudentProfile) - O'quvchi
- `status` (CharField, choices) - Davomat holati:
  - `present` - Kelgan
  - `absent` - Kelmagan
  - `late` - Kechikkan
  - `excused` - Sababli kelmagan
  - `sick` - Kasal
- `arrival_time` (Time, optional) - Kelish vaqti (kechikkan bo'lsa)
- `reason` (Text, optional) - Sabab (kelmagan yoki kechikkan bo'lsa)
- `notes` (Text, optional) - Qo'shimcha eslatmalar
- `created_by`, `updated_by` - Audit trail
- `created_at`, `updated_at` - Vaqt

**Meta:**
- `unique_together`: [('lesson_attendance', 'student_profile')]
- `indexes`: [('student_profile', 'lesson_attendance'), ('status')]

## API Endpoints

### 1. Dars davomati yaratish va ro'yxat

**POST** `/api/v1/school/attendance/lessons/`
- Dars davomati yaratish
- Body: `class_subject_id`, `lesson_date`, `lesson_number`, `teacher_id`, `topic`, `notes`

**GET** `/api/v1/school/attendance/lessons/`
- Dars davomati ro'yxati
- Query params: `class_subject_id`, `lesson_date`, `teacher_id`, `start_date`, `end_date`

### 2. Dars davomati detail

**GET** `/api/v1/school/attendance/lessons/<uuid:lesson_id>/`
- Dars davomati ma'lumotlari

**PATCH** `/api/v1/school/attendance/lessons/<uuid:lesson_id>/`
- Dars davomati yangilash

**DELETE** `/api/v1/school/attendance/lessons/<uuid:lesson_id>/`
- Dars davomati o'chirish

### 3. O'quvchi davomati yozish (mass update)

**POST** `/api/v1/school/attendance/lessons/<uuid:lesson_id>/records/`
- Bir dars uchun barcha o'quvchilarning davomatini yuborish
- Body: `records` (array)
  ```json
  {
    "records": [
      {
        "student_profile_id": "uuid",
        "status": "present",
        "arrival_time": "09:15",
        "reason": null
      },
      {
        "student_profile_id": "uuid",
        "status": "absent",
        "reason": "Kasallik"
      }
    ]
  }
  ```

### 4. O'quvchi davomati yozuvi

**GET** `/api/v1/school/attendance/records/<uuid:record_id>/`
- O'quvchi davomati yozuvi detail

**PATCH** `/api/v1/school/attendance/records/<uuid:record_id>/`
- O'quvchi davomati yozuvi yangilash

### 5. O'quvchi davomati statistikasi

**GET** `/api/v1/school/attendance/students/<uuid:student_id>/statistics/`
- O'quvchi davomati statistikasi
- Query params: `start_date`, `end_date`, `class_subject_id`
- Response:
  ```json
  {
    "total_lessons": 100,
    "present": 85,
    "absent": 10,
    "late": 3,
    "excused": 2,
    "attendance_rate": 85.0
  }
  ```

### 6. Sinf davomati statistikasi

**GET** `/api/v1/school/attendance/classes/<uuid:class_id>/statistics/`
- Sinf davomati statistikasi
- Query params: `start_date`, `end_date`, `class_subject_id`

## Permissions

- `branch_admin` - Barcha operatsiyalar
- `super_admin` - Barcha operatsiyalar
- `teacher` - O'z sinflari uchun davomat yozish va ko'rish
- `student` - Faqat o'z davomatini ko'rish

## Filtering va Search

- `class_subject_id` - Sinf fani bo'yicha
- `lesson_date` - Dars sanasi bo'yicha
- `start_date`, `end_date` - Sana oralig'i
- `teacher_id` - O'qituvchi bo'yicha
- `student_profile_id` - O'quvchi bo'yicha
- `status` - Davomat holati bo'yicha

## Integratsiya

- **ClassSubject** - Darslar sinf fanlari bilan bog'langan
- **StudentProfile** - O'quvchilar bilan bog'langan
- **Schedule** (kelajakda) - Dars jadvali bilan integratsiya

## Keyingi Qadamlar

1. Model yaratish
2. Serializers yaratish
3. Views yaratish
4. Admin panel sozlash
5. Testlar yozish

