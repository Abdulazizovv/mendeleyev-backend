# Academic API — Akademik Yil va Choraklar Boshqaruvi

Academic moduli maktabda akademik yillar va choraklarni boshqarish uchun API-lar taqdim etadi.

## Model Struktura

### AcademicYear Model

Akademik yillar quyidagi maydonlarga ega:

- `id` (UUID) — Akademik yil ID
- `branch` (UUID) — Filial ID (ForeignKey)
- `name` (String) — Akademik yil nomi (masalan: "2024-2025")
- `start_date` (Date) — Boshlanish sanasi
- `end_date` (Date) — Tugash sanasi
- `is_active` (Boolean) — Joriy akademik yil
- `quarters` (Array, read-only) — Choraklar ro'yxati
- Audit trail: `created_at`, `updated_at`, `created_by`, `updated_by`

### Quarter Model

Choraklar quyidagi maydonlarga ega:

- `id` (UUID) — Chorak ID
- `academic_year` (UUID) — Akademik yil ID (ForeignKey)
- `name` (String) — Chorak nomi (masalan: "1-chorak", "2-chorak")
- `number` (Integer, 1-4) — Chorak raqami
- `start_date` (Date) — Boshlanish sanasi
- `end_date` (Date) — Tugash sanasi
- `is_active` (Boolean) — Joriy chorak
- Audit trail: `created_at`, `updated_at`, `created_by`, `updated_by`

## Authentication

Barcha endpointlar JWT token talab qiladi:
```
Authorization: Bearer <access_token>
```

## Permissions

- `branch_admin` — Barcha operatsiyalar
- `super_admin` — Barcha operatsiyalar
- `teacher` — Ko'rish
- `student` — Ko'rish
- `parent` — Ko'rish

## Endpoints

### 1. Akademik Yillar Ro'yxati

**GET** `/api/v1/school/branches/{branch_id}/academic-years/`

Filialdagi barcha akademik yillarni qaytaradi.

**Response 200:**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "branch": "456e7890-e89b-12d3-a456-426614174001",
    "branch_name": "Alpha School",
    "name": "2024-2025",
    "start_date": "2024-09-01",
    "end_date": "2025-06-30",
    "is_active": true,
    "quarters": [
      {
        "id": "789e0123-e89b-12d3-a456-426614174002",
        "name": "1-chorak",
        "number": 1,
        "start_date": "2024-09-01",
        "end_date": "2024-11-30",
        "is_active": true
      }
    ],
    "created_at": "2024-09-01T10:00:00Z",
    "updated_at": "2024-09-01T10:00:00Z"
  }
]
```

### 2. Akademik Yil Yaratish

**POST** `/api/v1/school/branches/{branch_id}/academic-years/`

Yangi akademik yil yaratadi.

**Request Body:**
```json
{
  "name": "2024-2025",
  "start_date": "2024-09-01",
  "end_date": "2025-06-30",
  "is_active": true
}
```

**Validation Rules:**
- `name` tanlangan filialda unique bo'lishi kerak
- `end_date` `start_date` dan keyin bo'lishi kerak
- Agar `is_active=true` bo'lsa, boshqa akademik yillar `is_active=false` ga o'zgaradi

**Response 201:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "branch": "456e7890-e89b-12d3-a456-426614174001",
  "branch_name": "Alpha School",
  "name": "2024-2025",
  "start_date": "2024-09-01",
  "end_date": "2025-06-30",
  "is_active": true,
  "quarters": [],
  "created_at": "2024-09-01T10:00:00Z",
  "updated_at": "2024-09-01T10:00:00Z"
}
```

**Error 400:**
```json
{
  "end_date": ["Tugash sanasi boshlanish sanasidan keyin bo'lishi kerak."]
}
```

### 3. Akademik Yil Detallari

**GET** `/api/v1/school/branches/{branch_id}/academic-years/{id}/`

Akademik yil to'liq ma'lumotlarini qaytaradi.

**Response 200:** (Akademik yillar ro'yxati bilan bir xil format)

### 4. Akademik Yilni Yangilash

**PATCH** `/api/v1/school/branches/{branch_id}/academic-years/{id}/`

Akademik yil ma'lumotlarini yangilaydi.

**Request Body:**
```json
{
  "name": "2024-2025 (Yangi)",
  "is_active": false
}
```

**Response 200:** (Yangilangan akademik yil ma'lumotlari)

### 5. Akademik Yilni O'chirish

**DELETE** `/api/v1/school/branches/{branch_id}/academic-years/{id}/`

Akademik yilni soft-delete qiladi (choraklar saqlanadi).

**Response 204:** No Content

### 6. Joriy Akademik Yil

**GET** `/api/v1/school/branches/{branch_id}/academic-years/current/`

Filialning joriy akademik yilini qaytaradi.

**Response 200:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "branch": "456e7890-e89b-12d3-a456-426614174001",
  "branch_name": "Alpha School",
  "name": "2024-2025",
  "start_date": "2024-09-01",
  "end_date": "2025-06-30",
  "is_active": true,
  "quarters": [
    {
      "id": "789e0123-e89b-12d3-a456-426614174002",
      "name": "1-chorak",
      "number": 1,
      "start_date": "2024-09-01",
      "end_date": "2024-11-30",
      "is_active": true
    }
  ],
  "created_at": "2024-09-01T10:00:00Z",
  "updated_at": "2024-09-01T10:00:00Z"
}
```

**Error 404:**
```json
{
  "detail": "Joriy akademik yil topilmadi."
}
```

### 7. Choraklar Ro'yxati

**GET** `/api/v1/school/academic-years/{academic_year_id}/quarters/`

Akademik yildagi barcha choraklarni qaytaradi.

**Response 200:**
```json
[
  {
    "id": "789e0123-e89b-12d3-a456-426614174002",
    "name": "1-chorak",
    "number": 1,
    "start_date": "2024-09-01",
    "end_date": "2024-11-30",
    "is_active": true,
    "created_at": "2024-09-01T10:00:00Z",
    "updated_at": "2024-09-01T10:00:00Z"
  }
]
```

### 8. Chorak Yaratish

**POST** `/api/v1/school/academic-years/{academic_year_id}/quarters/`

Yangi chorak yaratadi.

**Request Body:**
```json
{
  "name": "1-chorak",
  "number": 1,
  "start_date": "2024-09-01",
  "end_date": "2024-11-30",
  "is_active": true
}
```

**Validation Rules:**
- `number` akademik yil ichida unique bo'lishi kerak (1-4)
- `end_date` `start_date` dan keyin bo'lishi kerak
- Chorak sanalari akademik yil ichida bo'lishi kerak
- Agar `is_active=true` bo'lsa, boshqa choraklar `is_active=false` ga o'zgaradi

**Response 201:**
```json
{
  "id": "789e0123-e89b-12d3-a456-426614174002",
  "name": "1-chorak",
  "number": 1,
  "start_date": "2024-09-01",
  "end_date": "2024-11-30",
  "is_active": true,
  "created_at": "2024-09-01T10:00:00Z",
  "updated_at": "2024-09-01T10:00:00Z"
}
```

**Error 400:**
```json
{
  "start_date": ["Chorak boshlanish sanasi akademik yil ichida bo'lishi kerak."],
  "end_date": ["Chorak tugash sanasi akademik yil ichida bo'lishi kerak."]
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

### Akademik yil yaratish va choraklar qo'shish

```javascript
// 1. Akademik yil yaratish
const createAcademicYear = async () => {
  const response = await fetch('/api/v1/school/branches/{branch_id}/academic-years/', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer <token>',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      name: '2024-2025',
      start_date: '2024-09-01',
      end_date: '2025-06-30',
      is_active: true
    })
  });
  const academicYear = await response.json();
  return academicYear;
};

// 2. Chorak yaratish
const createQuarter = async (academicYearId, number, startDate, endDate) => {
  const response = await fetch(`/api/v1/school/academic-years/${academicYearId}/quarters/`, {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer <token>',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      name: `${number}-chorak`,
      number: number,
      start_date: startDate,
      end_date: endDate,
      is_active: number === 1 // Birinchi chorakni active qilish
    })
  });
  const quarter = await response.json();
  return quarter;
};

// 3. Barcha choraklarni yaratish
const createAllQuarters = async (academicYearId) => {
  const quarters = [
    { number: 1, start: '2024-09-01', end: '2024-11-30' },
    { number: 2, start: '2024-12-01', end: '2025-02-28' },
    { number: 3, start: '2025-03-01', end: '2025-05-15' },
    { number: 4, start: '2025-05-16', end: '2025-06-30' }
  ];
  
  for (const q of quarters) {
    await createQuarter(academicYearId, q.number, q.start, q.end);
  }
};
```

### Joriy akademik yilni olish

```javascript
const getCurrentAcademicYear = async () => {
  const response = await fetch('/api/v1/school/branches/{branch_id}/academic-years/current/', {
    method: 'GET',
    headers: {
      'Authorization': 'Bearer <token>'
    }
  });
  const academicYear = await response.json();
  return academicYear;
};
```

## Eslatmalar

1. **Soft Delete**: Akademik yil yoki chorak o'chirilganda, ular `deleted_at` maydoni bilan belgilanadi va faol ro'yxatlarda ko'rinmaydi.

2. **Unique Constraints**: 
   - Har bir filial uchun akademik yil nomi unique
   - Har bir akademik yil uchun chorak raqami unique (1-4)

3. **Active State**:
   - Faqat bitta akademik yil `is_active=true` bo'lishi mumkin
   - Faqat bitta chorak `is_active=true` bo'lishi mumkin
   - Yangi active yaratilganda, eskisi avtomatik `is_active=false` ga o'zgaradi

4. **Date Validation**:
   - Chorak sanalari akademik yil ichida bo'lishi kerak
   - Tugash sanasi boshlanish sanasidan keyin bo'lishi kerak

