# Classes API — Sinflar Boshqaruvi

Sinflar moduli maktabda sinflarni, o'quvchilarni sinfga biriktirish va sinf ma'lumotlarini boshqarish uchun API-lar taqdim etadi.

## Model Struktura

### Class Model

Sinflar quyidagi maydonlarga ega:

- `id` (UUID) — Sinf ID
- `branch` (UUID) — Filial ID (ForeignKey)
- `academic_year` (UUID) — Akademik yil ID (ForeignKey)
- `name` (String) — Sinf nomi (masalan: "1-A", "5-B")
- `grade_level` (Integer, 1-11) — Sinf darajasi
- `section` (String, optional) — Bo'lim (A, B, C, ...)
- `class_teacher` (UUID, optional) — Sinf o'qituvchisi (BranchMembership ID, role=teacher)
- `max_students` (Integer) — Maksimal o'quvchilar soni
- `room` (UUID, optional) — Xona ID (ForeignKey to Room)
- `is_active` (Boolean) — Faol sinf
- `current_students_count` (Integer, read-only) — Joriy o'quvchilar soni
- `can_add_student` (Boolean, read-only) — Sinfga yana o'quvchi qo'shish mumkinmi?
- Audit trail: `created_at`, `updated_at`, `created_by`, `updated_by`

### ClassStudent Model

Sinf o'quvchilari quyidagi maydonlarga ega:

- `id` (UUID) — O'quvchi-sinf biriktirish ID
- `class_obj` (UUID) — Sinf ID (ForeignKey)
- `membership` (UUID) — O'quvchi BranchMembership ID (role=student)
- `enrollment_date` (Date) — Qo'shilgan sana (auto)
- `is_active` (Boolean) — Faol
- `notes` (Text, optional) — Izohlar
- Audit trail: `created_at`, `updated_at`, `created_by`, `updated_by`

## Authentication

Barcha endpointlar JWT token talab qiladi:
```
Authorization: Bearer <access_token>
```

## Permissions

- `branch_admin` — Barcha operatsiyalar
- `super_admin` — Barcha operatsiyalar
- `teacher` — Ko'rish va o'z sinflarini boshqarish

### Branch Konteksti (muvofiqlashtirish)

Backend branch kontekstini quyidagi tartibda aniqlaydi:

1) URL yo'lidagi `branch_id` (agar mavjud bo'lsa)
2) Header: `X-Branch-Id`
3) Query param: `branch_id`
4) JWT claim: `br` (fallback)

Sinflar o'quvchilari kabi ba'zi endpointlarda URL faqat `class_id` beradi. Bunday holatda backend avtomatik ravishda `class_id` orqali sinfning `branch_id` sini aniqlab, ruxsatni tekshiradi. Shuning uchun odatda `X-Branch-Id` yuborish shart emas.

## Endpoints

### 1. Sinflar Ro'yxati

**GET** `/api/v1/school/branches/{branch_id}/classes/`

Filialdagi barcha sinflarni qaytaradi.

**Query Parameters:**
- `page` (Number, optional) — Sahifa raqami (default: 1)
- `page_size` (Number, optional) — Sahifa hajmi (default: 20, max: 100)
- `search` (String, optional) — Qidiruv (nomi, sinf rahbari ismi, familiyasi)
- `ordering` (String, optional) — Tartiblash (masalan: `name`, `-name`, `grade_level`, `-grade_level`)
- `academic_year_id` (UUID, optional) — Akademik yil bo'yicha filter
- `grade_level` (Integer, optional) — Sinf darajasi bo'yicha filter
- `is_active` (Boolean, optional) — Faol sinflar bo'yicha filter

**Response 200:** (Paginatsiya qilingan natija)
```json
{
  "count": 42,
  "next": "/api/v1/school/branches/{branch_id}/classes/?page=2&page_size=20",
  "previous": null,
  "results": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "branch": "456e7890-e89b-12d3-a456-426614174001",
      "branch_name": "Alpha School",
      "academic_year": "789e0123-e89b-12d3-a456-426614174002",
      "academic_year_name": "2024-2025",
      "name": "1-A",
      "grade_level": 1,
      "section": "A",
      "class_teacher": "012e3456-e89b-12d3-a456-426614174003",
      "class_teacher_name": "John Doe",
      "max_students": 30,
      "current_students_count": 25,
      "can_add_student": true,
      "room": "345e6789-e89b-12d3-a456-426614174004",
      "is_active": true,
      "created_at": "2024-09-01T10:00:00Z",
      "updated_at": "2024-09-01T10:00:00Z"
    }
  ]
}
```

### 2. Sinf Yaratish

**POST** `/api/v1/school/branches/{branch_id}/classes/`

Yangi sinf yaratadi.

**Request Body:**
```json
{
  "branch": "456e7890-e89b-12d3-a456-426614174001",
  "academic_year": "789e0123-e89b-12d3-a456-426614174002",
  "name": "1-A",
  "grade_level": 1,
  "section": "A",
  "class_teacher": "012e3456-e89b-12d3-a456-426614174003",
  "max_students": 30,
  "is_active": true
}
```

**Validation Rules:**
- `branch` so'rov bodysida talab qilinadi va URL dagi `{branch_id}` bilan mos bo'lishi kerak
- `academic_year` tanlangan filialga tegishli bo'lishi kerak
- `class_teacher` tanlangan filialga tegishli va `role=teacher` bo'lishi kerak
- `grade_level` 1-11 orasida bo'lishi kerak
- `max_students` 1 dan katta bo'lishi kerak

**Response 201:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "branch": "456e7890-e89b-12d3-a456-426614174001",
  "branch_name": "Alpha School",
  "academic_year": "789e0123-e89b-12d3-a456-426614174002",
  "academic_year_name": "2024-2025",
  "name": "1-A",
  "grade_level": 1,
  "section": "A",
  "class_teacher": "012e3456-e89b-12d3-a456-426614174003",
  "class_teacher_name": "John Doe",
  "max_students": 30,
  "current_students_count": 0,
  "can_add_student": true,
  "is_active": true,
  "created_at": "2024-09-01T10:00:00Z",
  "updated_at": "2024-09-01T10:00:00Z"
}
```

**Error 400:**
```json
{
  "academic_year": ["Akademik yil tanlangan filialga tegishli emas."],
  "class_teacher": ["Tanlangan a'zolik o'qituvchi roliga ega emas."]
}
```

### 3. Sinf Detallari

**GET** `/api/v1/school/branches/{branch_id}/classes/{id}/`

Sinf to'liq ma'lumotlarini qaytaradi.

**Response 200:** (Sinflar ro'yxati bilan bir xil format)

### 4. Sinfni Yangilash

**PATCH** `/api/v1/school/branches/{branch_id}/classes/{id}/`

Sinf ma'lumotlarini yangilaydi.

**Request Body:** (faqat yangilash kerak bo'lgan maydonlar)
```json
{
  "name": "1-B",
  "max_students": 35,
  "is_active": false
}
```

**Response 200:** (Yangilangan sinf ma'lumotlari)

### 5. Sinfni O'chirish

**DELETE** `/api/v1/school/branches/{branch_id}/classes/{id}/`

Sinfni soft-delete qiladi. O'chirilganda bog'liq obyektlar ham soft-delete qilinadi:

- Ushbu sinfdagi barcha `ClassStudent` yozuvlari
- Ushbu sinfga biriktirilgan barcha `ClassSubject` yozuvlari

**Response 204:** No Content

**Soft Delete va Unique Constraints:**
- O'chirilgan sinflar ro'yxatlarda va detallarda ko'rinmaydi
- Sinf soft-delete qilinganda, bog'liq `ClassStudent` va `ClassSubject` yozuvlari ham ko'rinmaydi
- **O'chirilgan sinf bilan bir xil nomdagi yangi sinf yaratish mumkin** — unique constraint faqat faol (`deleted_at is null`) yozuvlarga qo'llanadi
- Misol: "1-A" sinfni yaratib, o'chirib, yana "1-A" yaratish mumkin (ular turli ID bilan yangi yozuvlar bo'ladi)

### 6. Sinf O'quvchilari Ro'yxati

**GET** `/api/v1/school/classes/{class_id}/students/`

Sinfdagi barcha o'quvchilarni qaytaradi.

**Query Parameters:**
- `page` (Number, optional) — Sahifa raqami (default: 1)
- `page_size` (Number, optional) — Sahifa hajmi (default: 20, max: 100)
- `search` (String, optional) — Qidiruv (ism, telefon)
- `ordering` (String, optional) — Tartiblash (masalan: `created_at`, `-created_at`)
- `is_active` (Boolean, optional) — Faol o'quvchilar bo'yicha filter

**Response 200:** (Paginatsiya qilingan natija)
```json
{
  "count": 25,
  "next": "/api/v1/school/classes/{class_id}/students/?page=2&page_size=20",
  "previous": null,
  "results": [
    {
      "id": "234e5678-e89b-12d3-a456-426614174005",
      "class_obj": "123e4567-e89b-12d3-a456-426614174000",
      "membership": "567e8901-e89b-12d3-a456-426614174006",
      "membership_id": "567e8901-e89b-12d3-a456-426614174006",
      "student_id": "890e1234-e89b-12d3-a456-426614174007",
      "student_user_id": "890e1234-e89b-12d3-a456-426614174007",
      "student_name": "Jane Smith",
      "student_phone": "+998901234568",
      "student_balance": 0,
      "enrollment_date": "2024-09-01",
      "is_active": true,
      "notes": "",
      "created_at": "2024-09-01T10:00:00Z",
      "updated_at": "2024-09-01T10:00:00Z"
    }
  ]
}
```

### 7. O'quvchi Qo'shish

**POST** `/api/v1/school/classes/{class_id}/students/`

O'quvchini sinfga qo'shadi.

**Request Body:**
```json
{
  "membership": "567e8901-e89b-12d3-a456-426614174006",
  "is_active": true,
  "notes": "Yangi o'quvchi"
}
```

**Validation Rules:**
- `membership` o'quvchi roliga ega bo'lishi kerak (`role=student`)
- `membership` sinf bilan bir xil filialga tegishli bo'lishi kerak
- Sinf to'ldi bo'lmasligi kerak (`current_students_count < max_students`)
- O'quvchi allaqachon sinfga qo'shilgan bo'lmasligi kerak

**Response 201:**
```json
{
  "id": "234e5678-e89b-12d3-a456-426614174005",
  "class_obj": "123e4567-e89b-12d3-a456-426614174000",
  "membership": "567e8901-e89b-12d3-a456-426614174006",
  "membership_id": "567e8901-e89b-12d3-a456-426614174006",
  "student_id": "890e1234-e89b-12d3-a456-426614174007",
  "student_name": "Jane Smith",
  "student_phone": "+998901234568",
  "student_balance": 0,
  "enrollment_date": "2024-09-01",
  "is_active": true,
  "notes": "Yangi o'quvchi",
  "created_at": "2024-09-01T10:00:00Z",
  "updated_at": "2024-09-01T10:00:00Z"
}
```

**Error 400:**
```json
{
  "membership": ["Sinf to'ldi. Maksimal o'quvchilar soni: 30"]
}
```

### 8. O'quvchi Detallari

**GET** `/api/v1/school/classes/{class_id}/students/{student_id}/`

O'quvchi-sinf biriktirish detallarini qaytaradi.

**Muhim (best practice):** `{student_id}` — bu `membership_id`. Detail endpoint uchun har doim ro'yxatdagi `membership_id` ni ishlating.

Qo'shimcha maydon: `student_user_id` foydalanuvchi ID (o'quvchi) bo'lib, ro'yxatda ma'lumot uchun qaytariladi. Detail uchun ishlatilmaydi.

Detail endpoint uchun doimo ro'yxatdagi `membership_id` ni ishlating.

**Eslatma:** Barcha response larda `student_balance` maydoni mavjud — o'quvchining joriy balansi (so'm, butun son). Bu moliyaviy operatsiyalarni kuzatish uchun foydali.

**Response 200:** (O'quvchi ma'lumotlari)

### 9. O'quvchini Yangilash

**PATCH** `/api/v1/school/classes/{class_id}/students/{student_id}/`

O'quvchi-sinf biriktirish ma'lumotlarini yangilaydi.

**Request Body:**
```json
{
  "is_active": false,
  "notes": "O'quvchi sinfdan chiqdi"
}
```

**Response 200:** (Yangilangan ma'lumotlar)

### 10. O'quvchini Olib Tashlash

**DELETE** `/api/v1/school/classes/{class_id}/students/{student_id}/`

O'quvchini sinfdan olib tashlaydi (soft-delete).

**Response 204:** No Content

### 11. Mavjud O'quvchilar (Sinfga qo'shish uchun)

### 12. O'quvchini Transfer Qilish

**POST** `/api/v1/school/classes/{class_id}/students/{student_id}/transfer/`

Berilgan sinfdagi o'quvchini (membership_id) boshqa sinfga ko'chiradi. Transfer faqat bir filial ichida amalga oshiriladi: eski biriktirish soft-delete qilinadi va yangi sinfga yangi biriktirish yaratiladi.

Query params: yo'q.

Body:
```json
{
  "target_class_id": "789e1234-e89b-12d3-a456-426614174009",
  "enrollment_date": "2024-09-15",
  "notes": "Transfer: parallel sinfga"
}
```

Cheklovlar:
- `target_class_id` bir xil filialga tegishli bo'lishi kerak.
- `target_class_id` joriy sinfdan farq qilishi kerak.
- O'quvchi maqsadli sinfga allaqachon biriktirilgan bo'lmasligi kerak.

**Response 201:** (Yangi sinfga biriktirish)
```json
{
  "id": "234e5678-e89b-12d3-a456-426614174099",
  "class_obj": "789e1234-e89b-12d3-a456-426614174009",
  "membership": "567e8901-e89b-12d3-a456-426614174006",
  "membership_id": "567e8901-e89b-12d3-a456-426614174006",
  "student_id": "890e1234-e89b-12d3-a456-426614174007",
  "student_name": "Jane Smith",
  "student_phone": "+998901234568",
  "student_balance": 0,
  "enrollment_date": "2024-09-15",
  "is_active": true,
  "notes": "Transfer: parallel sinfga",
  "created_at": "2024-09-15T10:00:00Z",
  "updated_at": "2024-09-15T10:00:00Z"
}
```

Xatoliklar (400):
- `{"target_class_id": "Target class must be in the same branch"}`
- `{"target_class_id": "Target class must be different"}`
- `{"target_class_id": "Student already enrolled in target class"}`

**GET** `/api/v1/school/branches/{branch_id}/classes/{class_id}/available-students/`

Berilgan filial va sinf uchun hali sinfga kiritilmagan o'quvchilar ro'yxati (filialdagi `student` roli bo'lgan a'zoliklar ichidan).

**Query Parameters:**
- `page` — Sahifa raqami (default: 1)
- `page_size` — Sahifa hajmi (default: 20, max: 100)
- `search` — Qidiruv (`user__first_name`, `user__last_name`, `user__phone_number`, `title`)
- `ordering` — Tartiblash (`user__first_name`, `user__last_name`, `created_at`, prefiks `-` kamayish uchun)

**Response 200:** (Paginatsiya qilingan natija)
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "567e8901-e89b-12d3-a456-426614174006",
      "user_phone": "+998900000012",
      "user_name": "Ali Bek",
      "branch": "456e7890-e89b-12d3-a456-426614174001",
      "branch_name": "Alpha School",
      "role": "student",
      "title": "",
      "salary_type": "monthly",
      "balance": 0,
      "created_at": "2024-09-01T10:00:00Z",
      "updated_at": "2024-09-01T10:00:00Z"
    }
  ]
}
```

## Error Responses

### 400 Bad Request
```json
{
  "field_name": ["Xato xabari"]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

## Misollar

### Sinf yaratish va o'quvchi qo'shish

```javascript
// 1. Sinf yaratish
const createClass = async () => {
  const response = await fetch('/api/v1/school/branches/{branch_id}/classes/', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer <token>',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      academic_year: '789e0123-e89b-12d3-a456-426614174002',
      name: '1-A',
      grade_level: 1,
      section: 'A',
      class_teacher: '012e3456-e89b-12d3-a456-426614174003',
      max_students: 30,
      is_active: true
    })
  });
  const classData = await response.json();
  return classData;
};

// 2. O'quvchini sinfga qo'shish
const addStudent = async (classId, membershipId) => {
  const response = await fetch(`/api/v1/school/classes/${classId}/students/`, {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer <token>',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      membership: membershipId,
      is_active: true,
      notes: 'Yangi o\'quvchi'
    })
  });
  const studentData = await response.json();
  return studentData;
};
```

### Sinf o'quvchilarini olish

```javascript
const getClassStudents = async (classId) => {
  const response = await fetch(`/api/v1/school/classes/${classId}/students/`, {
    method: 'GET',
    headers: {
      'Authorization': 'Bearer <token>'
    }
  });
  const students = await response.json();
  return students;
};
```

## Dashboard API

O'qituvchi va o'quvchilar uchun alohida dashboard API-lar mavjud:

- **O'qituvchi**: `/api/v1/school/dashboard/teacher/classes/` — O'qituvchining sinflari
- **O'quvchi**: `/api/v1/school/dashboard/student/class/` — O'quvchining sinfi

Batafsil ma'lumot uchun [Dashboard API](dashboard.md) hujjatiga qarang.

## Avtomatik Yaratiladigan Modellar

Quyidagi modellar signallar orqali avtomatik yaratiladi:

1. **StudentBalance** - `StudentProfile` yaratilganda avtomatik yaratiladi
   - Default balance: 0 so'm
   - Signal: `apps.school.finance.signals.create_student_balance`

## Eslatmalar

1. **Soft Delete**: Sinf yoki o'quvchi o'chirilganda, ular `deleted_at` maydoni bilan belgilanadi va faol ro'yxatlarda ko'rinmaydi.

2. **Unique Constraints**: 
   - Har bir filial va akademik yil uchun sinf nomi unique
   - Har bir sinf uchun o'quvchi bir marta qo'shilishi mumkin

3. **Relationships**:
   - Sinf akademik yilga bog'liq
   - Sinf o'qituvchiga bog'liq (ixtiyoriy)
   - Sinf xonaga bog'liq (ixtiyoriy)
   - O'quvchi BranchMembership orqali sinfga biriktiriladi

4. **Computed Fields**:
   - `current_students_count` — faol o'quvchilar soni
   - `can_add_student` — sinfga yana o'quvchi qo'shish mumkinmi?

5. **Permissions**:
   - Admin endpointlar: `branch_admin`, `super_admin`, `teacher` (CRUD)
   - Dashboard endpointlar: `teacher` yoki `student` (faqat o'z ma'lumotlari)

6. **Avtomatik Yaratiladigan Modellar**:
   - `StudentBalance` - `StudentProfile` yaratilganda avtomatik yaratiladi (signal orqali)

