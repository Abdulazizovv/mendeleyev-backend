# Subjects API — Fanlar Boshqaruvi

Fanlar moduli maktabda fanlarni, sinfga fan biriktirish va o'qituvchi tayinlash uchun API-lar taqdim etadi.

## Model Struktura

### Subject Model

Fanlar quyidagi maydonlarga ega:

- `id` (UUID) — Fan ID
- `branch` (UUID) — Filial ID (ForeignKey)
- `name` (String) — Fan nomi (masalan: "Matematika", "Fizika")
- `code` (String, optional) — Fan kodi (masalan: "MATH", "PHYS")
- `description` (Text, optional) — Fan tavsifi
- `color` (String, optional) — Fan rang kodi (HEX, `#RRGGBB`). Jadvalda fan rangini ko'rsatish uchun ishlatiladi.
- `is_active` (Boolean) — Faol fan
- Audit trail: `created_at`, `updated_at`, `created_by`, `updated_by`

### ClassSubject Model

Sinf-fan biriktirish quyidagi maydonlarga ega:

- `id` (UUID) — Sinf-fan biriktirish ID
- `class_obj` (UUID) — Sinf ID (ForeignKey)
- `subject` (UUID) — Fan ID (ForeignKey)
- `teacher` (UUID, optional) — O'qituvchi BranchMembership ID (role=teacher)
- `hours_per_week` (Integer) — Haftada dars soatlari
- `quarter` (UUID, optional) — Chorak ID (ForeignKey)
- `is_active` (Boolean) — Faol
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

## Endpoints

### 1. Fanlar Ro'yxati

**GET** `/api/v1/school/branches/{branch_id}/subjects/`

Filialdagi barcha fanlarni qaytaradi.

**Query Parameters:**
- `page` (Number, optional) — Sahifa raqami (default: 1)
- `page_size` (Number, optional) — Sahifa hajmi (default: 20, max: 100)
- `search` (String, optional) — Qidiruv (nomi, kodi)
- `ordering` (String, optional) — Tartiblash (masalan: `name`, `-name`, `code`, `-code`)
- `is_active` (Boolean, optional) — Faol fanlar bo'yicha filter

**Response 200:** (Paginatsiya qilingan natija)
```json
{
  "count": 10,
  "next": "/api/v1/school/branches/{branch_id}/subjects/?page=2&page_size=20",
  "previous": null,
  "results": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "branch": "456e7890-e89b-12d3-a456-426614174001",
      "branch_name": "Alpha School",
      "name": "Matematika",
      "code": "MATH",
      "description": "Matematika fani",
      "color": "#2D9CDB",
      "is_active": true,
      "created_at": "2024-09-01T10:00:00Z",
      "updated_at": "2024-09-01T10:00:00Z"
    }
  ]
}
```

### 2. Fan Yaratish

**POST** `/api/v1/school/branches/{branch_id}/subjects/`

Yangi fan yaratadi.

**Request Body:**
```json
{
  "branch": "456e7890-e89b-12d3-a456-426614174001",
  "name": "Matematika",
  "code": "MATH",
  "description": "Matematika fani",
  "color": "#2D9CDB",
  "is_active": true
}
```

**Validation Rules:**
- `branch` so'rov bodysida talab qilinadi va URL dagi `{branch_id}` bilan mos bo'lishi kerak
- `name` tanlangan filialda unique bo'lishi kerak
- `code` ixtiyoriy, lekin unique bo'lishi tavsiya etiladi

**Response 201:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "branch": "456e7890-e89b-12d3-a456-426614174001",
  "branch_name": "Alpha School",
  "name": "Matematika",
  "code": "MATH",
  "description": "Matematika fani",
  "color": "#2D9CDB",
  "is_active": true,
  "created_at": "2024-09-01T10:00:00Z",
  "updated_at": "2024-09-01T10:00:00Z"
}
```

**Error 400:**
```json
{
  "name": ["Fan nomi allaqachon mavjud."]
}
```

### 3. Fan Detallari

**GET** `/api/v1/school/branches/{branch_id}/subjects/{id}/`

Fan to'liq ma'lumotlarini va qo'shimcha statistikani qaytaradi.

**Response 200 (kengaytirilgan):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "branch": "456e7890-e89b-12d3-a456-426614174001",
  "branch_name": "Alpha School",
  "name": "Matematika",
  "code": "MATH",
  "description": "Matematika fani",
  "color": "#2D9CDB",
  "is_active": true,
  "total_classes": 5,
  "active_classes": 4,
  "teachers": [
    {
      "id": "c1a2...",
      "phone_number": "+998901234500",
      "full_name": "Akmal Rustamov"
    }
  ],
  "class_subjects": [
    {
      "id": "789e0123-e89b-12d3-a456-426614174008",
      "class_id": "321e4567-e89b-12d3-a456-426614174010",
      "class_name": "5-A",
      "hours_per_week": 4,
      "is_active": true,
      "teacher": {
        "id": "c1a2...",
        "full_name": "Akmal Rustamov",
        "phone_number": "+998901234500"
      },
      "quarter": {
        "id": "9b8c...",
        "name": "1-chorak",
        "number": 1
      }
    }
  ],
  "created_at": "2024-09-01T10:00:00Z",
  "updated_at": "2024-09-01T10:00:00Z"
}
```

**Qo'shimcha maydonlar izohi:**
- `total_classes`: Fan biriktirilgan sinflar umumiy soni (soft-delete hisobga olinmaydi)
- `active_classes`: Faol (`is_active=true`) biriktirilgan sinflar soni
- `teachers`: Ushbu fanga biriktirilgan o'qituvchilar (unikal)
- `class_subjects`: Har bir sinf-fan biriktirish obyekti detallari

### 4. Fanni Yangilash

**PATCH** `/api/v1/school/branches/{branch_id}/subjects/{id}/`

Fan ma'lumotlarini yangilaydi.

**Request Body (misol):**
```json
{
  "name": "Matematika (Yangi)",
  "description": "Yangilangan tavsif",
  "color": "#F2994A"
}
```

**Response 200:** (Yangilangan fan ma'lumotlari)

### 5. Fanni O'chirish

**DELETE** `/api/v1/school/branches/{branch_id}/subjects/{id}/`

Fanni soft-delete qiladi (ma'lumotlar bazada qoladi, `deleted_at` belgilanadi, ro'yxatlarda ko'rinmaydi).

**Response 204:** No Content

**Soft Delete Xulq-atvori:**
- Keyinchalik tiklash uchun admin panelda yoki alohida endpoint orqali `restore` chaqirsa bo'ladi (hozircha umumiy endpoint yo'q).
- Hard delete uchun faqat ichki maqsadlarda `hard_delete()` ishlatiladi.
- Fan soft delete qilinganda unga biriktirilgan barcha `ClassSubject` yozuvlari ham avtomatik soft delete qilinadi (`deleted_at` belgilanadi) va o'qituvchi / o'quvchi dashboard fan ro'yxatlarida ko'rinmaydi.

### 6. Sinf Fanlari Ro'yxati

**GET** `/api/v1/school/classes/{class_id}/subjects/`

Sinfdagi barcha fanlarni qaytaradi.

**Query Parameters:**
- `page` (Number, optional) — Sahifa raqami (default: 1)
- `page_size` (Number, optional) — Sahifa hajmi (default: 20, max: 100)
- `search` (String, optional) — Qidiruv (fan nomi, o'qituvchi ismi)
- `ordering` (String, optional) — Tartiblash (masalan: `subject__name`, `-subject__name`)
- `is_active` (Boolean, optional) — Faol fanlar bo'yicha filter

**Response 200:** (Paginatsiya qilingan natija)
```json
{
  "count": 8,
  "next": "/api/v1/school/classes/{class_id}/subjects/?page=2&page_size=20",
  "previous": null,
  "results": [
    {
      "id": "234e5678-e89b-12d3-a456-426614174005",
      "class_obj": "123e4567-e89b-12d3-a456-426614174000",
      "class_name": "1-A",
      "subject": "345e6789-e89b-12d3-a456-426614174006",
      "subject_name": "Matematika",
      "subject_code": "MATH",
      "teacher": "567e8901-e89b-12d3-a456-426614174007",
      "teacher_name": "John Doe",
      "hours_per_week": 4,
      "quarter": "789e0123-e89b-12d3-a456-426614174008",
      "quarter_name": "1-chorak",
      "is_active": true,
      "created_at": "2024-09-01T10:00:00Z",
      "updated_at": "2024-09-01T10:00:00Z"
    }
  ]
}
```

### 7. Sinfga Fan Qo'shish

**POST** `/api/v1/school/classes/{class_id}/subjects/`

Sinfga fan qo'shadi va o'qituvchi tayinlaydi.

**Request Body:**
```json
{
  "subject": "345e6789-e89b-12d3-a456-426614174006",
  "teacher": "567e8901-e89b-12d3-a456-426614174007",
  "hours_per_week": 4,
  "quarter": "789e0123-e89b-12d3-a456-426614174008",
  "is_active": true
}
```

**Validation Rules:**
- `subject` sinf bilan bir xil filialga tegishli bo'lishi kerak
- `teacher` sinf bilan bir xil filialga tegishli va `role=teacher` bo'lishi kerak
- `quarter` sinf bilan bir xil akademik yilga tegishli bo'lishi kerak (agar belgilansa)
- Fan allaqachon sinfga qo'shilgan bo'lmasligi kerak
- `hours_per_week` 1 dan katta bo'lishi kerak

**Response 201:**
```json
{
  "id": "234e5678-e89b-12d3-a456-426614174005",
  "class_obj": "123e4567-e89b-12d3-a456-426614174000",
  "class_name": "1-A",
  "subject": "345e6789-e89b-12d3-a456-426614174006",
  "subject_name": "Matematika",
  "subject_code": "MATH",
  "teacher": "567e8901-e89b-12d3-a456-426614174007",
  "teacher_name": "John Doe",
  "hours_per_week": 4,
  "quarter": "789e0123-e89b-12d3-a456-426614174008",
  "quarter_name": "1-chorak",
  "is_active": true,
  "created_at": "2024-09-01T10:00:00Z",
  "updated_at": "2024-09-01T10:00:00Z"
}
```

**Error 400:**
```json
{
  "subject": ["Bu fan allaqachon sinfga qo'shilgan."],
  "teacher": ["Tanlangan a'zolik o'qituvchi roliga ega emas."],
  "quarter": ["Chorak sinf bilan bir xil akademik yilga tegishli bo'lishi kerak."]
}
```

### 8. Sinf Fani Detallari

**GET** `/api/v1/school/classes/{class_id}/subjects/{id}/`

Sinf-fan biriktirish detallarini qaytaradi.

**Response 200:** (Sinf fanlari ro'yxati bilan bir xil format)

### 9. Sinf Fani Yangilash

**PATCH** `/api/v1/school/classes/{class_id}/subjects/{id}/`

Sinf-fan biriktirish ma'lumotlarini yangilaydi (masalan, o'qituvchi o'zgartirish).

**Request Body:**
```json
{
  "teacher": "890e1234-e89b-12d3-a456-426614174009",
  "hours_per_week": 5,
  "is_active": false
}
```

**Response 200:** (Yangilangan ma'lumotlar)

### 10. Sinfdan Fanni Olib Tashlash

**DELETE** `/api/v1/school/classes/{class_id}/subjects/{id}/`

Sinfdan fanni olib tashlaydi (soft-delete).

**Response 204:** No Content

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

### Fan yaratish va sinfga qo'shish

```javascript
// 1. Fan yaratish
const createSubject = async () => {
  const response = await fetch('/api/v1/school/branches/{branch_id}/subjects/', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer <token>',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      name: 'Matematika',
      code: 'MATH',
      description: 'Matematika fani',
      color: '#2D9CDB',
      is_active: true
    })
  });
  const subjectData = await response.json();
  return subjectData;
};

// 2. Sinfga fan qo'shish
const addSubjectToClass = async (classId, subjectId, teacherId, quarterId) => {
  const response = await fetch(`/api/v1/school/classes/${classId}/subjects/`, {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer <token>',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      subject: subjectId,
      teacher: teacherId,
      hours_per_week: 4,
      quarter: quarterId,
      is_active: true
    })
  });
  const classSubjectData = await response.json();
  return classSubjectData;
};
```

### Sinf fanlarini olish

```javascript
const getClassSubjects = async (classId) => {
  const response = await fetch(`/api/v1/school/classes/${classId}/subjects/`, {
    method: 'GET',
    headers: {
      'Authorization': 'Bearer <token>'
    }
  });
  const subjects = await response.json();
  return subjects;
};
```

### O'qituvchini o'zgartirish

```javascript
const updateClassSubjectTeacher = async (classId, classSubjectId, newTeacherId) => {
  const response = await fetch(`/api/v1/school/classes/${classId}/subjects/${classSubjectId}/`, {
    method: 'PATCH',
    headers: {
      'Authorization': 'Bearer <token>',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      teacher: newTeacherId
    })
  });
  const updatedData = await response.json();
  return updatedData;
};

## Rang Tanlash Qoidalari

- `color` faqat HEX formatda qabul qilinadi: `#RRGGBB`
- Misol: `#FF5733`, `#2D9CDB`, `#27AE60`
- Bo'sh qoldirilsa, UI default rangdan foydalansa bo'ladi.
- Rang jadvalni vizual farqlash uchun; branch ichida takrorlansa ham ruxsat (agar unikal talab qilinsa, backendda qo'shimcha constraint qo'shish mumkin).
```

## Dashboard API

O'qituvchi va o'quvchilar uchun alohida dashboard API-lar mavjud:

- **O'qituvchi**: `/api/v1/school/dashboard/teacher/subjects/` — O'qituvchining fanlari
- **O'quvchi**: `/api/v1/school/dashboard/student/subjects/` — O'quvchining fanlari

Batafsil ma'lumot uchun [Dashboard API](dashboard.md) hujjatiga qarang.

## Avtomatik Yaratiladigan Modellar

Quyidagi modellar signallar orqali avtomatik yaratiladi:

1. **StudentBalance** - `StudentProfile` yaratilganda avtomatik yaratiladi
   - Default balance: 0 so'm
   - Signal: `apps.school.finance.signals.create_student_balance`

## Eslatmalar

1. **Soft Delete**: Fan yoki sinf-fan biriktirish o'chirilganda, ular `deleted_at` maydoni bilan belgilanadi va faol ro'yxatlarda ko'rinmaydi.

2. **Unique Constraints**: 
   - Har bir filial uchun fan nomi unique
   - Har bir sinf uchun fan bir marta qo'shilishi mumkin
  - Soft-delete qilingan fan nomi qayta ishlatilsa bo'ladi (agar unique constraint buzilmasa). Agar constraint tufayli xato bo'lsa, avval eski fan tiklanishi yoki nom o'zgartirilishi kerak.

3. **Relationships**:
   - Fan filialga bog'liq
   - Sinf-fan biriktirish sinf, fan, o'qituvchi va chorakka bog'liq
  - Soft-delete qilingan fan bilan bog'liq `ClassSubject` lar ham avtomatik yashirinmaydi; ular timetable logikangizda filtrlanishi kerak.
   - O'qituvchi ixtiyoriy (keyinchalik tayinlash mumkin)

4. **Validation**:
   - Fan va sinf bir xil filialga tegishli bo'lishi kerak
   - O'qituvchi va sinf bir xil filialga tegishli bo'lishi kerak
   - Chorak va sinf bir xil akademik yilga tegishli bo'lishi kerak

5. **Permissions**:
   - Admin endpointlar: `branch_admin`, `super_admin`, `teacher` (CRUD)
   - Dashboard endpointlar: `teacher` yoki `student` (faqat o'z ma'lumotlari)

