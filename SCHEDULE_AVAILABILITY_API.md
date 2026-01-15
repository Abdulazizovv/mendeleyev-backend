# Schedule Availability API Documentation

## Overview
Bu API sinfga yangi dars yaratish uchun berilgan sana va vaqtda qaysi fanlar va xonalar bo'shligini tekshirish uchun ishlatiladi.

## Endpoint
```
GET /api/v1/school/branches/{branch_id}/schedule/availability/
```

## Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `class_id` | string (UUID) | ✅ | Tekshirilayotgan sinf ID |
| `date` | string | ✅ | Sana (YYYY-MM-DD formatda) |
| `start_time` | string | ✅ | Dars boshlanish vaqti (HH:MM formatda) |
| `end_time` | string | ✅ | Dars tugash vaqti (HH:MM formatda) |

## Authentication
- JWT token kerakli
- Foydalanuvchi filialda `branch_admin`, `super_admin`, yoki `teacher` roli bo'lishi kerak

## Response Format

### Success Response (200)
```json
{
  "available_subjects": [
    {
      "id": "uuid-string",
      "subject_name": "Matematika",
      "teacher_name": "Ali Valiyev",
      "teacher_id": "uuid-string"
    }
  ],
  "available_rooms": [
    {
      "id": "uuid-string",
      "name": "101-xona",
      "capacity": 30
    }
  ],
  "conflicts": [
    {
      "type": "teacher",
      "message": "O'qituvchi bir vaqtda ikki joyda dars o'ta olmaydi",
      "details": {
        "teacher": "Ali Valiyev",
        "class": "1-A",
        "time": "09:00 - 10:00"
      }
    }
  ]
}
```

### Error Responses

#### 400 Bad Request
```json
{
  "error": "class_id, date, start_time, end_time parametrlari majburiy"
}
```

#### 404 Not Found
```json
{
  "error": "Sinf topilmadi"
}
```

## Field Descriptions

### available_subjects
Ushbu sinfga biriktirilgan va berilgan vaqtda konflikti bo'lmagan fanlar ro'yxati.

- `id`: ClassSubject ID (fan biriktirish ID)
- `subject_name`: Fan nomi
- `teacher_name`: O'qituvchi to'liq ismi
- `teacher_id`: O'qituvchi membership ID

### available_rooms
Filialdagi va berilgan vaqtda band bo'lmagan xonalar ro'yxati.

- `id`: Xona ID
- `name`: Xona nomi
- `capacity`: Xona sig'imi

### conflicts
Topilgan konfliktlar ro'yxati. Agar konfliktlar bo'lsa, bu fanlar yoki xonalar `available_subjects` yoki `available_rooms` ga kirmaydi.

- `type`: Konflikt turi (`"teacher"` yoki `"room"`)
- `message`: O'zbek tilidagi xatolik xabari
- `details`: Qo'shimcha ma'lumotlar

## Usage Examples

### 1. Frontend da foydalanish
```javascript
// Sana va vaqt tanlanganda
const checkAvailability = async (classId, date, startTime, endTime) => {
  const params = new URLSearchParams({
    class_id: classId,
    date: date, // '2026-01-15'
    start_time: startTime, // '09:00'
    end_time: endTime // '10:00'
  });

  const response = await fetch(`/api/v1/school/branches/${branchId}/schedule/availability/?${params}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  const data = await response.json();

  if (response.ok) {
    // Dropdownlarni yangilash
    updateSubjectDropdown(data.available_subjects);
    updateRoomDropdown(data.available_rooms);

    // Agar konfliktlar bo'lsa, foydalanuvchiga ko'rsatish
    if (data.conflicts.length > 0) {
      showConflicts(data.conflicts);
    }
  } else {
    showError(data.error);
  }
};
```

### 2. Dropdownlarni yangilash
```javascript
const updateSubjectDropdown = (subjects) => {
  const select = document.getElementById('subject-select');
  select.innerHTML = '<option value="">Fan tanlang...</option>';

  subjects.forEach(subject => {
    const option = document.createElement('option');
    option.value = subject.id;
    option.textContent = `${subject.subject_name} (${subject.teacher_name})`;
    select.appendChild(option);
  });
};

const updateRoomDropdown = (rooms) => {
  const select = document.getElementById('room-select');
  select.innerHTML = '<option value="">Xona tanlang...</option>';

  rooms.forEach(room => {
    const option = document.createElement('option');
    option.value = room.id;
    option.textContent = `${room.name} (${room.capacity} o'rin)`;
    select.appendChild(option);
  });
};
```

### 3. Konfliktlarni ko'rsatish
```javascript
const showConflicts = (conflicts) => {
  const container = document.getElementById('conflicts-container');
  container.innerHTML = '';

  if (conflicts.length === 0) return;

  const alert = document.createElement('div');
  alert.className = 'alert alert-warning';
  alert.innerHTML = `
    <strong>Diqqat!</strong> Quyidagi konfliktlar topildi:<br>
    ${conflicts.map(c => `• ${c.message}`).join('<br>')}
  `;

  container.appendChild(alert);
};
```

## Business Logic

1. **Fanlar tekshiruvi**: Sinfga biriktirilgan barcha fanlar tekshiriladi. Agar o'qituvchi berilgan vaqtda boshqa darsda bo'lsa, bu fan mavjud fanlar ro'yxatiga kirmaydi.

2. **Xonalar tekshiruvi**: Filialdagi barcha xonalar tekshiriladi. Agar xona berilgan vaqtda band bo'lsa, bu xona mavjud xonalar ro'yxatiga kirmaydi.

3. **Konflikt turlari**:
   - `teacher`: O'qituvchi bir vaqtda ikki joyda dars o'ta olmaydi
   - `room`: Xona bir vaqtda ikki sinf uchun band bo'lishi mumkin emas

## Notes

- Bu API faqat mavjudlikni tekshiradi, dars yaratmaydi
- Dars yaratish uchun alohida API ishlatiladi (`POST /api/v1/school/branches/{branch_id}/lessons/`)
- Vaqtlar 24-soat formatida bo'lishi kerak (masalan: "09:00", "14:30")
- Sana YYYY-MM-DD formatida bo'lishi kerak (masalan: "2026-01-15")</content>
<parameter name="filePath">/home/abdulazizov/Desktop/mendeleyev/mendeleyev-backend/SCHEDULE_AVAILABILITY_API.md