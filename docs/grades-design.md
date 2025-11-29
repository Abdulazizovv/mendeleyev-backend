# Baholash (Grades) Moduli Dizayni

## Umumiy Ma'lumot

Baholash moduli o'quvchilarning fanlar bo'yicha baholarini kiritish, saqlash va hisobotlar tayyorlash uchun mo'ljallangan.

## Model Struktura

### Grade
O'quvchi bahosi.

**Maydonlar:**
- `id` (UUID) - Baho ID
- `student_profile` (ForeignKey to StudentProfile) - O'quvchi
- `class_subject` (ForeignKey to ClassSubject) - Sinf fani
- `quarter` (ForeignKey to Quarter) - Chorak
- `grade_type` (CharField, choices) - Baho turi:
  - `homework` - Uy vazifasi
  - `classwork` - Dars ishi
  - `quiz` - Test
  - `midterm` - O'rta nazorat
  - `final` - Yakuniy nazorat
  - `project` - Loyiha
  - `participation` - Ishtirok
- `value` (Integer) - Baho qiymati (1-5 yoki 0-100)
- `max_value` (Integer, default=5) - Maksimal baho (5 yoki 100)
- `weight` (Decimal, default=1.0) - Baho og'irligi (o'rtacha hisoblashda)
- `date` (Date) - Baho berilgan sana
- `teacher` (ForeignKey to BranchMembership) - Baho bergan o'qituvchi
- `notes` (Text, optional) - Qo'shimcha eslatmalar
- `created_by`, `updated_by` - Audit trail
- `created_at`, `updated_at` - Vaqt

**Meta:**
- `indexes`: 
  - [('student_profile', 'class_subject', 'quarter')]
  - [('class_subject', 'quarter', 'date')]
  - [('grade_type', 'date')]

### GradeStatistics
O'quvchi baholari statistikasi (cached).

**Maydonlar:**
- `id` (UUID) - Statistika ID
- `student_profile` (ForeignKey to StudentProfile) - O'quvchi
- `class_subject` (ForeignKey to ClassSubject) - Sinf fani
- `quarter` (ForeignKey to Quarter) - Chorak
- `average_grade` (Decimal) - O'rtacha baho
- `total_grades` (Integer) - Jami baholar soni
- `homework_count` (Integer) - Uy vazifalari soni
- `classwork_count` (Integer) - Dars ishlari soni
- `quiz_count` (Integer) - Testlar soni
- `last_updated` (DateTime) - Oxirgi yangilanish vaqti

**Meta:**
- `unique_together`: [('student_profile', 'class_subject', 'quarter')]
- `indexes`: [('student_profile', 'quarter')]

## API Endpoints

### 1. Baho yaratish va ro'yxat

**POST** `/api/v1/school/grades/`
- Baho yaratish
- Body: `student_profile_id`, `class_subject_id`, `quarter_id`, `grade_type`, `value`, `max_value`, `weight`, `date`, `notes`

**GET** `/api/v1/school/grades/`
- Baholar ro'yxati
- Query params: 
  - `student_profile_id` - O'quvchi bo'yicha
  - `class_subject_id` - Sinf fani bo'yicha
  - `quarter_id` - Chorak bo'yicha
  - `grade_type` - Baho turi bo'yicha
  - `start_date`, `end_date` - Sana oralig'i

### 2. Baho detail

**GET** `/api/v1/school/grades/<uuid:grade_id>/`
- Baho ma'lumotlari

**PATCH** `/api/v1/school/grades/<uuid:grade_id>/`
- Baho yangilash

**DELETE** `/api/v1/school/grades/<uuid:grade_id>/`
- Baho o'chirish

### 3. Mass baho kiritish

**POST** `/api/v1/school/grades/bulk/`
- Bir nechta o'quvchiga bir vaqtda baho berish
- Body:
  ```json
  {
    "class_subject_id": "uuid",
    "quarter_id": "uuid",
    "grade_type": "quiz",
    "date": "2024-12-19",
    "max_value": 5,
    "grades": [
      {
        "student_profile_id": "uuid",
        "value": 5,
        "notes": "A'lo"
      },
      {
        "student_profile_id": "uuid",
        "value": 4,
        "notes": "Yaxshi"
      }
    ]
  }
  ```

### 4. O'quvchi baholari statistikasi

**GET** `/api/v1/school/grades/students/<uuid:student_id>/statistics/`
- O'quvchi baholari statistikasi
- Query params: `quarter_id`, `class_subject_id`
- Response:
  ```json
  {
    "student_id": "uuid",
    "quarter_id": "uuid",
    "statistics": [
      {
        "class_subject_id": "uuid",
        "subject_name": "Matematika",
        "average_grade": 4.5,
        "total_grades": 10,
        "homework_count": 5,
        "classwork_count": 3,
        "quiz_count": 2,
        "grade_breakdown": {
          "5": 6,
          "4": 3,
          "3": 1
        }
      }
    ],
    "overall_average": 4.3
  }
  ```

### 5. Sinf baholari statistikasi

**GET** `/api/v1/school/grades/classes/<uuid:class_id>/statistics/`
- Sinf baholari statistikasi
- Query params: `quarter_id`, `class_subject_id`

### 6. Chorak baholari

**GET** `/api/v1/school/grades/quarters/<uuid:quarter_id>/`
- Chorak baholari ro'yxati
- Query params: `class_subject_id`, `student_profile_id`

## Permissions

- `branch_admin` - Barcha operatsiyalar
- `super_admin` - Barcha operatsiyalar
- `teacher` - O'z sinflari uchun baho kiritish va ko'rish
- `student` - Faqat o'z baholarini ko'rish
- `parent` - Faqat o'z farzandining baholarini ko'rish

## Filtering va Search

- `student_profile_id` - O'quvchi bo'yicha
- `class_subject_id` - Sinf fani bo'yicha
- `quarter_id` - Chorak bo'yicha
- `grade_type` - Baho turi bo'yicha
- `start_date`, `end_date` - Sana oralig'i
- `teacher_id` - O'qituvchi bo'yicha

## Integratsiya

- **StudentProfile** - O'quvchilar bilan bog'langan
- **ClassSubject** - Sinf fanlari bilan bog'langan
- **Quarter** - Choraklar bilan bog'langan
- **Finance** - Baholar asosida stipendiya/chegirma qoidalari (kelajakda)

## Baho Hisoblash

### O'rtacha Baho
```
average = Σ(grade_value * weight) / Σ(weight)
```

### Chorak Bahosi
Chorakdagi barcha baholarning o'rtacha qiymati.

### Yakuniy Baho
Yakuniy baho = (1-chorak * 0.25) + (2-chorak * 0.25) + (3-chorak * 0.25) + (4-chorak * 0.25)

## Keyingi Qadamlar

1. Model yaratish
2. Baho hisoblash logikasi
3. Serializers yaratish
4. Views yaratish
5. Admin panel sozlash
6. Testlar yozish
7. Statistika cache mekanizmi

