# Maktab Moduli To'liq Rejasi

## Maqsad
Maktablar uchun to'liq funksional modul yaratish: akademik yil, choraklar, sinflar, fanlar, dars jadvali, davomat, baholash, moliya.

## Umumiy struktura

```
school/
├── academic/          # Akademik yil va choraklar
├── classes/           # Sinflar
├── subjects/          # Fanlar
├── schedule/          # Dars jadvali
├── attendance/        # Davomat
├── grades/            # Baholash
├── finance/           # Moliya (abonement, to'lovlar, chegirmalar)
└── rooms/             # Bino va xonalar
```

## 1. Academic Module (Akademik yil va choraklar)

### Model: AcademicYear
- `id`, `branch` (ForeignKey to Branch)
- `name` - Akademik yil nomi (masalan: "2024-2025")
- `start_date` - Boshlanish sanasi
- `end_date` - Tugash sanasi
- `is_active` - Joriy akademik yil
- `created_by`, `updated_by`, timestamps, soft delete

### Model: Quarter
- `id`, `academic_year` (ForeignKey to AcademicYear)
- `name` - Chorak nomi (1-chorak, 2-chorak, ...)
- `number` - Chorak raqami (1, 2, 3, 4)
- `start_date` - Boshlanish sanasi
- `end_date` - Tugash sanasi
- `is_active` - Joriy chorak
- `created_by`, `updated_by`, timestamps, soft delete

### API Endpoints:
- `GET /api/school/academic/years/` - Akademik yillar ro'yxati
- `POST /api/school/academic/years/` - Yangi akademik yil yaratish
- `GET /api/school/academic/years/{id}/` - Akademik yil detallari
- `PATCH /api/school/academic/years/{id}/` - Akademik yilni yangilash
- `DELETE /api/school/academic/years/{id}/` - Akademik yilni o'chirish
- `GET /api/school/academic/years/{id}/quarters/` - Choraklar ro'yxati
- `POST /api/school/academic/years/{id}/quarters/` - Yangi chorak yaratish
- `GET /api/school/academic/current/` - Joriy akademik yil va chorak

## 2. Classes Module (Sinflar)

### Model: Class
- `id`, `branch` (ForeignKey to Branch)
- `academic_year` (ForeignKey to AcademicYear)
- `name` - Sinf nomi (masalan: "1-A", "5-B")
- `grade_level` - Sinf darajasi (1-11)
- `section` - Bo'lim (A, B, C, ...)
- `class_teacher` (ForeignKey to BranchMembership, role=teacher)
- `max_students` - Maksimal o'quvchilar soni
- `current_students_count` - Joriy o'quvchilar soni
- `room` (ForeignKey to Room, optional)
- `is_active` - Faol sinf
- `created_by`, `updated_by`, timestamps, soft delete

### API Endpoints:
- `GET /api/school/classes/` - Sinflar ro'yxati
- `POST /api/school/classes/` - Yangi sinf yaratish
- `GET /api/school/classes/{id}/` - Sinf detallari
- `PATCH /api/school/classes/{id}/` - Sinfni yangilash
- `DELETE /api/school/classes/{id}/` - Sinfni o'chirish
- `GET /api/school/classes/{id}/students/` - Sinf o'quvchilari
- `POST /api/school/classes/{id}/students/` - O'quvchi qo'shish
- `DELETE /api/school/classes/{id}/students/{student_id}/` - O'quvchini olib tashlash

## 3. Subjects Module (Fanlar)

### Model: Subject
- `id`, `branch` (ForeignKey to Branch)
- `name` - Fan nomi (masalan: "Matematika", "Fizika")
- `code` - Fan kodi (masalan: "MATH", "PHYS")
- `description` - Fan tavsifi
- `is_active` - Faol fan
- `created_by`, `updated_by`, timestamps, soft delete

### Model: ClassSubject
- `id`, `class` (ForeignKey to Class)
- `subject` (ForeignKey to Subject)
- `teacher` (ForeignKey to BranchMembership, role=teacher)
- `hours_per_week` - Haftada dars soatlari
- `quarter` (ForeignKey to Quarter, optional) - Qaysi chorakda o'qitiladi
- `is_active` - Faol
- `created_by`, `updated_by`, timestamps, soft delete

### API Endpoints:
- `GET /api/school/subjects/` - Fanlar ro'yxati
- `POST /api/school/subjects/` - Yangi fan yaratish
- `GET /api/school/subjects/{id}/` - Fan detallari
- `PATCH /api/school/subjects/{id}/` - Fanni yangilash
- `DELETE /api/school/subjects/{id}/` - Fanni o'chirish
- `GET /api/school/classes/{class_id}/subjects/` - Sinf fanlari
- `POST /api/school/classes/{class_id}/subjects/` - Sinfga fan qo'shish
- `DELETE /api/school/classes/{class_id}/subjects/{id}/` - Sinfdan fanni olib tashlash

## 4. Schedule Module (Dars jadvali)

### Model: Schedule
- `id`, `branch` (ForeignKey to Branch)
- `class` (ForeignKey to Class)
- `subject` (ForeignKey to Subject)
- `teacher` (ForeignKey to BranchMembership, role=teacher)
- `day_of_week` - Hafta kuni (1=Monday, 7=Sunday)
- `period` - Dars vaqti (1, 2, 3, ...)
- `room` (ForeignKey to Room, optional)
- `academic_year` (ForeignKey to AcademicYear)
- `quarter` (ForeignKey to Quarter, optional)
- `start_time` - Dars boshlanish vaqti
- `end_time` - Dars tugash vaqti
- `is_active` - Faol
- `created_by`, `updated_by`, timestamps, soft delete

### API Endpoints:
- `GET /api/school/schedule/` - Dars jadvali ro'yxati
- `POST /api/school/schedule/` - Yangi dars qo'shish
- `GET /api/school/schedule/{id}/` - Dars detallari
- `PATCH /api/school/schedule/{id}/` - Darsni yangilash
- `DELETE /api/school/schedule/{id}/` - Darsni o'chirish
- `GET /api/school/schedule/class/{class_id}/` - Sinf dars jadvali
- `GET /api/school/schedule/teacher/{teacher_id}/` - O'qituvchi dars jadvali
- `GET /api/school/schedule/room/{room_id}/` - Xona dars jadvali

## 5. Attendance Module (Davomat)

### Model: Attendance
- `id`, `branch` (ForeignKey to Branch)
- `student` (ForeignKey to BranchMembership, role=student)
- `class` (ForeignKey to Class)
- `subject` (ForeignKey to Subject, optional)
- `date` - Sana
- `status` - Holati: `present`, `absent`, `late`, `excused`
- `quarter` (ForeignKey to Quarter)
- `notes` - Izohlar
- `marked_by` (ForeignKey to User) - Kim belgilagan
- `created_by`, `updated_by`, timestamps, soft delete

### API Endpoints:
- `GET /api/school/attendance/` - Davomat ro'yxati
- `POST /api/school/attendance/` - Davomat belgilash
- `GET /api/school/attendance/{id}/` - Davomat detallari
- `PATCH /api/school/attendance/{id}/` - Davomatni yangilash
- `DELETE /api/school/attendance/{id}/` - Davomatni o'chirish
- `GET /api/school/attendance/class/{class_id}/` - Sinf davomati
- `GET /api/school/attendance/student/{student_id}/` - O'quvchi davomati
- `POST /api/school/attendance/bulk/` - Ko'p o'quvchi uchun davomat belgilash

## 6. Grades Module (Baholash)

### Model: Grade
- `id`, `branch` (ForeignKey to Branch)
- `student` (ForeignKey to BranchMembership, role=student)
- `subject` (ForeignKey to Subject)
- `class` (ForeignKey to Class)
- `quarter` (ForeignKey to Quarter)
- `grade_type` - Baho turi: `homework`, `quiz`, `midterm`, `final`, `project`
- `grade_value` - Baho qiymati (1-5 yoki 0-100)
- `max_grade` - Maksimal baho (default: 5 yoki 100)
- `date` - Baho berilgan sana
- `teacher` (ForeignKey to BranchMembership, role=teacher)
- `notes` - Izohlar
- `created_by`, `updated_by`, timestamps, soft delete

### Model: GradeSummary
- `id`, `student` (ForeignKey to BranchMembership)
- `subject` (ForeignKey to Subject)
- `class` (ForeignKey to Class)
- `quarter` (ForeignKey to Quarter)
- `average_grade` - O'rtacha baho
- `total_points` - Jami ball
- `max_points` - Maksimal ball
- `percentage` - Foiz
- `created_by`, `updated_by`, timestamps

### API Endpoints:
- `GET /api/school/grades/` - Baholar ro'yxati
- `POST /api/school/grades/` - Yangi baho qo'shish
- `GET /api/school/grades/{id}/` - Baho detallari
- `PATCH /api/school/grades/{id}/` - Bahoni yangilash
- `DELETE /api/school/grades/{id}/` - Bahoni o'chirish
- `GET /api/school/grades/student/{student_id}/` - O'quvchi baholari
- `GET /api/school/grades/class/{class_id}/subject/{subject_id}/` - Sinf va fan bo'yicha baholar
- `GET /api/school/grades/summary/student/{student_id}/quarter/{quarter_id}/` - O'quvchi baho xulosa

## 7. Finance Module (Moliya)

### Model: SubscriptionPlan
- `id`, `branch` (ForeignKey to Branch)
- `name` - Abonement nomi (masalan: "1-4 sinflar", "5-9 sinflar")
- `grade_levels` - Qaysi sinflar uchun (JSON: [1,2,3,4])
- `monthly_fee` - Oylik to'lov (so'm, butun son)
- `description` - Tavsif
- `is_active` - Faol
- `created_by`, `updated_by`, timestamps, soft delete

### Model: StudentSubscription
- `id`, `branch` (ForeignKey to Branch)
- `student` (ForeignKey to BranchMembership, role=student)
- `subscription_plan` (ForeignKey to SubscriptionPlan)
- `start_date` - Boshlanish sanasi
- `end_date` - Tugash sanasi
- `monthly_fee` - Oylik to'lov (snapshot)
- `is_active` - Faol
- `created_by`, `updated_by`, timestamps, soft delete

### Model: Payment
- `id`, `branch` (ForeignKey to Branch)
- `student_subscription` (ForeignKey to StudentSubscription)
- `amount` - To'lov summasi (so'm, butun son)
- `payment_date` - To'lov sanasi
- `payment_method` - To'lov usuli: `cash`, `card`, `transfer`
- `status` - Holati: `pending`, `completed`, `failed`, `refunded`
- `notes` - Izohlar
- `created_by`, `updated_by`, timestamps, soft delete

### Model: Discount
- `id`, `branch` (ForeignKey to Branch)
- `name` - Chegirma nomi
- `discount_type` - Chegirma turi: `percentage`, `fixed`
- `discount_value` - Chegirma qiymati (foiz yoki so'm)
- `applicable_to` - Qaysi abonementlarga: `all`, `specific` (JSON)
- `start_date` - Boshlanish sanasi
- `end_date` - Tugash sanasi
- `is_active` - Faol
- `created_by`, `updated_by`, timestamps, soft delete

### API Endpoints:
- `GET /api/school/finance/subscription-plans/` - Abonement rejalari
- `POST /api/school/finance/subscription-plans/` - Yangi reja yaratish
- `GET /api/school/finance/subscriptions/` - O'quvchi abonementlari
- `POST /api/school/finance/subscriptions/` - Yangi abonement yaratish
- `GET /api/school/finance/payments/` - To'lovlar ro'yxati
- `POST /api/school/finance/payments/` - Yangi to'lov qo'shish
- `GET /api/school/finance/discounts/` - Chegirmalar ro'yxati
- `POST /api/school/finance/discounts/` - Yangi chegirma yaratish

## 8. Rooms Module (Bino va xonalar)

### Model: Building
- `id`, `branch` (ForeignKey to Branch)
- `name` - Bino nomi (masalan: "Asosiy bino", "Yangi bino")
- `address` - Manzil
- `floors` - Qavatlar soni
- `description` - Tavsif
- `is_active` - Faol
- `created_by`, `updated_by`, timestamps, soft delete

### Model: Room
- `id`, `branch` (ForeignKey to Branch)
- `building` (ForeignKey to Building)
- `name` - Xona nomi (masalan: "101", "Laboratoriya")
- `room_type` - Xona turi: `classroom`, `lab`, `library`, `gym`, `office`
- `floor` - Qavat
- `capacity` - Sig'imi (o'quvchilar soni)
- `equipment` - Jihozlar (JSON)
- `is_active` - Faol
- `created_by`, `updated_by`, timestamps, soft delete

### API Endpoints:
- `GET /api/school/rooms/buildings/` - Binolar ro'yxati
- `POST /api/school/rooms/buildings/` - Yangi bino yaratish
- `GET /api/school/rooms/` - Xonalar ro'yxati
- `POST /api/school/rooms/` - Yangi xona yaratish

## Implementation Plan

### Bosqich 1: Asosiy struktura (1 hafta)
1. `school/` package yaratish
2. Har bir modul uchun `apps/` directory
3. Asosiy modellar yaratish
4. Migratsiyalar

### Bosqich 2: Academic Module (3 kun)
1. AcademicYear model
2. Quarter model
3. API endpoints
4. Testlar

### Bosqich 3: Classes va Subjects (4 kun)
1. Class model
2. Subject model
3. ClassSubject model
4. API endpoints
5. Testlar

### Bosqich 4: Schedule Module (4 kun)
1. Schedule model
2. API endpoints
3. Jadval validatsiyasi
4. Testlar

### Bosqich 5: Attendance Module (3 kun)
1. Attendance model
2. API endpoints
3. Bulk operations
4. Testlar

### Bosqich 6: Grades Module (5 kun)
1. Grade model
2. GradeSummary model
3. API endpoints
4. Hisoblash logikasi
5. Testlar

### Bosqich 7: Finance Module (5 kun)
1. SubscriptionPlan model
2. StudentSubscription model
3. Payment model
4. Discount model
5. API endpoints
6. Testlar

### Bosqich 8: Rooms Module (2 kun)
1. Building model
2. Room model
3. API endpoints
4. Testlar

### Bosqich 9: Integration va Test (3 kun)
1. Barcha modullarni integratsiya qilish
2. Integration testlar
3. Performance testlar
4. Hujjatlashtirish

## Keyingi qadamlar
1. Super Admin API-larini implementatsiya qilish
2. Maktab modulini bosqichma-bosqich implementatsiya qilish
3. Testlar va hujjatlashtirish

