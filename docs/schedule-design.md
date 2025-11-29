# Dars Jadvali (Schedule) Moduli Dizayni

## Umumiy Ma'lumot

Dars jadvali moduli sinflar, o'qituvchilar va xonalar uchun haftalik dars jadvalini boshqarish uchun mo'ljallangan.

## Model Struktura

### Schedule
Dars jadvali yozuvi.

**Maydonlar:**
- `id` (UUID) - Jadval yozuvi ID
- `class_obj` (ForeignKey to Class) - Sinf
- `class_subject` (ForeignKey to ClassSubject) - Sinf fani
- `teacher` (ForeignKey to BranchMembership) - O'qituvchi
- `room` (ForeignKey to Room, optional) - Xona
- `day_of_week` (Integer, 1-7) - Haftaning kuni (1=Dushanba, 7=Yakshanba)
- `start_time` (Time) - Dars boshlanish vaqti
- `end_time` (Time) - Dars tugash vaqti
- `lesson_number` (Integer, 1-8) - Dars raqami
- `is_active` (Boolean) - Faol
- `notes` (Text, optional) - Qo'shimcha eslatmalar
- `created_by`, `updated_by` - Audit trail
- `created_at`, `updated_at` - Vaqt

**Meta:**
- `unique_together`: [('class_obj', 'day_of_week', 'lesson_number')]
- `indexes`: 
  - [('class_obj', 'day_of_week')]
  - [('teacher', 'day_of_week', 'start_time')]
  - [('room', 'day_of_week', 'start_time')]

**Validation:**
- `start_time < end_time`
- `day_of_week` 1-7 orasida
- `lesson_number` 1-8 orasida
- O'qituvchi bir vaqtda ikki darsda bo'lishi mumkin emas (konflikt tekshiruvi)
- Xona bir vaqtda ikki darsda bo'lishi mumkin emas (konflikt tekshiruvi)

## API Endpoints

### 1. Dars jadvali ro'yxati va yaratish

**GET** `/api/v1/school/schedules/`
- Dars jadvali ro'yxati
- Query params: 
  - `class_id` - Sinf bo'yicha
  - `teacher_id` - O'qituvchi bo'yicha
  - `room_id` - Xona bo'yicha
  - `day_of_week` - Haftaning kuni bo'yicha
  - `is_active` - Faol jadvallar

**POST** `/api/v1/school/schedules/`
- Dars jadvali yaratish
- Body: `class_obj_id`, `class_subject_id`, `teacher_id`, `room_id`, `day_of_week`, `start_time`, `end_time`, `lesson_number`, `is_active`, `notes`
- Validation: Konflikt tekshiruvi

### 2. Dars jadvali detail

**GET** `/api/v1/school/schedules/<uuid:schedule_id>/`
- Dars jadvali ma'lumotlari

**PATCH** `/api/v1/school/schedules/<uuid:schedule_id>/`
- Dars jadvali yangilash
- Validation: Konflikt tekshiruvi

**DELETE** `/api/v1/school/schedules/<uuid:schedule_id>/`
- Dars jadvali o'chirish

### 3. Sinf jadvali

**GET** `/api/v1/school/schedules/classes/<uuid:class_id>/`
- Sinf jadvali (haftaning barcha kunlari)
- Response format:
  ```json
  {
    "class_id": "uuid",
    "class_name": "1-A",
    "schedule": {
      "1": [  // Dushanba
        {
          "id": "uuid",
          "lesson_number": 1,
          "start_time": "08:00",
          "end_time": "08:45",
          "subject": "Matematika",
          "teacher": "Ali Valiyev",
          "room": "101"
        }
      ],
      "2": [],  // Seshanba
      ...
    }
  }
  ```

### 4. O'qituvchi jadvali

**GET** `/api/v1/school/schedules/teachers/<uuid:teacher_id>/`
- O'qituvchi jadvali (haftaning barcha kunlari)

### 5. Xona jadvali

**GET** `/api/v1/school/schedules/rooms/<uuid:room_id>/`
- Xona jadvali (haftaning barcha kunlari)

### 6. Konflikt tekshiruvi

**POST** `/api/v1/school/schedules/check-conflicts/`
- Jadval yaratishdan oldin konflikt tekshiruvi
- Body: `teacher_id`, `room_id`, `day_of_week`, `start_time`, `end_time`
- Response:
  ```json
  {
    "has_conflicts": true,
    "teacher_conflict": {
      "schedule_id": "uuid",
      "class_name": "1-A",
      "subject": "Matematika"
    },
    "room_conflict": {
      "schedule_id": "uuid",
      "class_name": "2-B",
      "subject": "Fizika"
    }
  }
  ```

## Permissions

- `branch_admin` - Barcha operatsiyalar
- `super_admin` - Barcha operatsiyalar
- `teacher` - O'z jadvalini ko'rish
- `student` - O'z sinfi jadvalini ko'rish

## Filtering va Search

- `class_id` - Sinf bo'yicha
- `teacher_id` - O'qituvchi bo'yicha
- `room_id` - Xona bo'yicha
- `day_of_week` - Haftaning kuni bo'yicha
- `is_active` - Faol jadvallar

## Integratsiya

- **Class** - Sinflar bilan bog'langan
- **ClassSubject** - Sinf fanlari bilan bog'langan
- **Room** - Xonalar bilan bog'langan
- **Attendance** - Davomat bilan integratsiya (darslar jadvaldan olinadi)

## Keyingi Qadamlar

1. Model yaratish
2. Konflikt tekshiruvi logikasi
3. Serializers yaratish
4. Views yaratish
5. Admin panel sozlash
6. Testlar yozish

