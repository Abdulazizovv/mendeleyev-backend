# Dashboard API — O'qituvchi va O'quvchi Dashboard

Dashboard moduli o'qituvchi va o'quvchilar uchun shaxsiy ma'lumotlarni ko'rish uchun API-lar taqdim etadi.

## Authentication

Barcha endpointlar JWT token talab qiladi:
```
Authorization: Bearer <access_token>
```

Branch context JWT token ichidagi `br` claim orqali aniqlanadi yoki `X-Branch-Id` header yoki `branch_id` query parameter orqali.

## Permissions

- **O'qituvchi endpointlari**: `teacher` roliga ega bo'lishi kerak
- **O'quvchi endpointlari**: `student` roliga ega bo'lishi kerak

## O'qituvchi Dashboard Endpoints

### 1. O'qituvchining Sinflari

**GET** `/api/v1/school/dashboard/teacher/classes/`

O'qituvchining boshqaradigan yoki dars beradigan sinflarini qaytaradi.

**Query Parameters:**
- `branch_id` (UUID, optional) — Filial ID (JWT dan yoki header dan olinadi)
- `academic_year_id` (UUID, optional) — Akademik yil bo'yicha filter
- `is_active` (Boolean, optional) — Faol sinflar bo'yicha filter

**Response 200:**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "branch": "456e7890-e89b-12d3-a456-426614174001",
    "branch_name": "Alpha School",
    "academic_year": "789e0123-e89b-12d3-a456-426614174002",
    "academic_year_name": "2024-2025",
    "name": "1-A",
    "grade_level": 1,
    "section": "A",
    "max_students": 30,
    "current_students_count": 25,
    "subjects_count": 5,
    "room": "345e6789-e89b-12d3-a456-426614174004",
    "room_name": "101",
    "is_active": true
  }
]
```

**Eslatma**: O'qituvchi `class_teacher` sifatida yoki `ClassSubject` orqali biriktirilgan sinflarni ko'radi.

### 2. O'qituvchining Fanlari

**GET** `/api/v1/school/dashboard/teacher/subjects/`

O'qituvchining o'qitadigan fanlarini qaytaradi.

**Query Parameters:**
- `branch_id` (UUID, optional) — Filial ID
- `class_id` (UUID, optional) — Sinf bo'yicha filter
- `is_active` (Boolean, optional) — Faol fanlar bo'yicha filter

**Response 200:**
```json
[
  {
    "id": "234e5678-e89b-12d3-a456-426614174005",
    "subject": "345e6789-e89b-12d3-a456-426614174006",
    "subject_name": "Matematika",
    "subject_code": "MATH",
    "class_obj": "123e4567-e89b-12d3-a456-426614174000",
    "class_id": "123e4567-e89b-12d3-a456-426614174000",
    "class_name": "1-A",
    "academic_year_name": "2024-2025",
    "hours_per_week": 4,
    "quarter": "789e0123-e89b-12d3-a456-426614174008",
    "quarter_name": "1-chorak",
    "students_count": 25,
    "is_active": true
  }
]
```

### 3. O'qituvchining O'quvchilari

**GET** `/api/v1/school/dashboard/teacher/students/`

O'qituvchining sinflaridagi barcha o'quvchilarini qaytaradi.

**Query Parameters:**
- `branch_id` (UUID, optional) — Filial ID
- `class_id` (UUID, optional) — Sinf bo'yicha filter

**Response 200:**
```json
[
  {
    "id": "456e7890-e89b-12d3-a456-426614174009",
    "student_id": "567e8901-e89b-12d3-a456-426614174010",
    "student_name": "Jane Smith",
    "student_phone": "+998901234568",
    "class_obj": "123e4567-e89b-12d3-a456-426614174000",
    "class_id": "123e4567-e89b-12d3-a456-426614174000",
    "class_name": "1-A",
    "academic_year_name": "2024-2025",
    "enrollment_date": "2024-09-01",
    "is_active": true
  }
]
```

## O'quvchi Dashboard Endpoints

### 4. O'quvchining Sinfi

**GET** `/api/v1/school/dashboard/student/class/`

O'quvchining sinfini to'liq ma'lumotlari bilan qaytaradi.

**Query Parameters:**
- `branch_id` (UUID, optional) — Filial ID

**Response 200:**
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
  "students_count": 25,
  "room": "345e6789-e89b-12d3-a456-426614174004",
  "room_name": "101",
  "subjects": [
    {
      "id": "234e5678-e89b-12d3-a456-426614174005",
      "subject_id": "345e6789-e89b-12d3-a456-426614174006",
      "subject_name": "Matematika",
      "subject_code": "MATH",
      "teacher_id": "567e8901-e89b-12d3-a456-426614174007",
      "teacher_name": "John Doe",
      "hours_per_week": 4,
      "quarter_id": "789e0123-e89b-12d3-a456-426614174008",
      "quarter_name": "1-chorak"
    }
  ],
  "is_active": true
}
```

**Error 404:**
```json
{
  "detail": "O'quvchi sinfga biriktirilmagan."
}
```

### 5. O'quvchining Fanlari

**GET** `/api/v1/school/dashboard/student/subjects/`

O'quvchining sinfidagi barcha fanlarini qaytaradi.

**Query Parameters:**
- `branch_id` (UUID, optional) — Filial ID

**Response 200:**
```json
[
  {
    "id": "234e5678-e89b-12d3-a456-426614174005",
    "subject": "345e6789-e89b-12d3-a456-426614174006",
    "subject_name": "Matematika",
    "subject_code": "MATH",
    "teacher": "567e8901-e89b-12d3-a456-426614174007",
    "teacher_id": "567e8901-e89b-12d3-a456-426614174007",
    "teacher_name": "John Doe",
    "hours_per_week": 4,
    "quarter": "789e0123-e89b-12d3-a456-426614174008",
    "quarter_name": "1-chorak",
    "is_active": true
  }
]
```

## Error Responses

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
  "detail": "O'quvchi sinfga biriktirilmagan."
}
```

## Misollar

### O'qituvchi dashboard

```javascript
// 1. O'qituvchining sinflarini olish
const getTeacherClasses = async (token, branchId) => {
  const response = await fetch('/api/v1/school/dashboard/teacher/classes/', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Branch-Id': branchId
    }
  });
  const classes = await response.json();
  return classes;
};

// 2. O'qituvchining fanlarini olish
const getTeacherSubjects = async (token, branchId, classId = null) => {
  const url = classId 
    ? `/api/v1/school/dashboard/teacher/subjects/?class_id=${classId}`
    : '/api/v1/school/dashboard/teacher/subjects/';
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Branch-Id': branchId
    }
  });
  const subjects = await response.json();
  return subjects;
};

// 3. O'qituvchining o'quvchilarini olish
const getTeacherStudents = async (token, branchId, classId = null) => {
  const url = classId
    ? `/api/v1/school/dashboard/teacher/students/?class_id=${classId}`
    : '/api/v1/school/dashboard/teacher/students/';
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Branch-Id': branchId
    }
  });
  const students = await response.json();
  return students;
};
```

### O'quvchi dashboard

```javascript
// 1. O'quvchining sinfini olish
const getStudentClass = async (token, branchId) => {
  const response = await fetch('/api/v1/school/dashboard/student/class/', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Branch-Id': branchId
    }
  });
  const classData = await response.json();
  return classData;
};

// 2. O'quvchining fanlarini olish
const getStudentSubjects = async (token, branchId) => {
  const response = await fetch('/api/v1/school/dashboard/student/subjects/', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Branch-Id': branchId
    }
  });
  const subjects = await response.json();
  return subjects;
};
```

## Eslatmalar

1. **Branch Context**: Branch ID JWT token ichidagi `br` claim, `X-Branch-Id` header yoki `branch_id` query parameter orqali aniqlanadi.

2. **O'qituvchi Sinflari**: O'qituvchi quyidagi sinflarni ko'radi:
   - `class_teacher` sifatida biriktirilgan sinflar
   - `ClassSubject` orqali biriktirilgan sinflar (qaysi sinfda dars beradi)

3. **O'quvchi Ma'lumotlari**: O'quvchi faqat o'z sinfini va sinfidagi fanlarni ko'radi.

4. **Filtering**: Barcha endpointlar query parameterlar orqali filter qilishni qo'llab-quvvatlaydi.

5. **Permissions**: Har bir endpoint faqat tegishli rolga ega foydalanuvchilar uchun ochiq.

