# Rooms API — Binolar va Xonalar Boshqaruvi

Rooms moduli maktabda binolar va xonalarni boshqarish uchun API-lar taqdim etadi.

## Model Struktura

### Building Model

Binolar quyidagi maydonlarga ega:

- `id` (UUID) — Bino ID
- `branch` (UUID) — Filial ID (ForeignKey)
- `name` (String) — Bino nomi (masalan: "Asosiy bino", "Yangi bino")
- `address` (Text, optional) — Manzil
- `floors` (Integer) — Qavatlar soni
- `description` (Text, optional) — Tavsif
- `is_active` (Boolean) — Faol bino
- `rooms_count` (Integer, read-only) — Xonalar soni
- Audit trail: `created_at`, `updated_at`, `created_by`, `updated_by`

### Room Model

Xonalar quyidagi maydonlarga ega:

- `id` (UUID) — Xona ID
- `branch` (UUID) — Filial ID (ForeignKey)
- `building` (UUID) — Bino ID (ForeignKey)
- `name` (String) — Xona nomi (masalan: "101", "Laboratoriya")
- `room_type` (String) — Xona turi:
  - `classroom` — Dars xonasi
  - `lab` — Laboratoriya
  - `library` — Kutubxona
  - `gym` — Sport zali
  - `office` — Ofis
  - `auditorium` — Auditoriya
  - `other` — Boshqa
- `floor` (Integer) — Qavat
- `capacity` (Integer) — Sig'imi (o'quvchilar soni)
- `equipment` (JSON, optional) — Jihozlar (masalan: `{"projector": true, "computers": 20}`)
- `is_active` (Boolean) — Faol xona
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

### 1. Binolar Ro'yxati

**GET** `/api/v1/school/branches/{branch_id}/buildings/`

Filialdagi barcha binolarni qaytaradi.

**Query Parameters:**
- `is_active` (Boolean, optional) — Faol binolar bo'yicha filter

**Response 200:**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "branch": "456e7890-e89b-12d3-a456-426614174001",
    "branch_name": "Alpha School",
    "name": "Asosiy bino",
    "address": "Toshkent shahar, Chilonzor tumani",
    "floors": 3,
    "description": "Asosiy o'quv binosi",
    "is_active": true,
    "rooms_count": 15,
    "created_at": "2024-09-01T10:00:00Z",
    "updated_at": "2024-09-01T10:00:00Z"
  }
]
```

### 2. Bino Yaratish

**POST** `/api/v1/school/branches/{branch_id}/buildings/`

Yangi bino yaratadi.

**Request Body:**
```json
{
  "name": "Asosiy bino",
  "address": "Toshkent shahar, Chilonzor tumani",
  "floors": 3,
  "description": "Asosiy o'quv binosi",
  "is_active": true
}
```

**Validation Rules:**
- `name` tanlangan filialda unique bo'lishi kerak
- `floors` 1 dan katta bo'lishi kerak

**Response 201:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "branch": "456e7890-e89b-12d3-a456-426614174001",
  "branch_name": "Alpha School",
  "name": "Asosiy bino",
  "address": "Toshkent shahar, Chilonzor tumani",
  "floors": 3,
  "description": "Asosiy o'quv binosi",
  "is_active": true,
  "rooms_count": 0,
  "created_at": "2024-09-01T10:00:00Z",
  "updated_at": "2024-09-01T10:00:00Z"
}
```

**Error 400:**
```json
{
  "name": ["Bino nomi allaqachon mavjud."]
}
```

### 3. Bino Detallari

**GET** `/api/v1/school/branches/{branch_id}/buildings/{id}/`

Bino to'liq ma'lumotlarini qaytaradi.

**Response 200:** (Binolar ro'yxati bilan bir xil format)

### 4. Binoni Yangilash

**PATCH** `/api/v1/school/branches/{branch_id}/buildings/{id}/`

Bino ma'lumotlarini yangilaydi.

**Request Body:**
```json
{
  "name": "Yangi bino",
  "floors": 4,
  "is_active": false
}
```

**Response 200:** (Yangilangan bino ma'lumotlari)

### 5. Binoni O'chirish

**DELETE** `/api/v1/school/branches/{branch_id}/buildings/{id}/`

Binoni soft-delete qiladi (xonalar saqlanadi).

**Response 204:** No Content

### 6. Xonalar Ro'yxati

**GET** `/api/v1/school/branches/{branch_id}/rooms/`

Filialdagi barcha xonalarni qaytaradi.

**Query Parameters:**
- `building_id` (UUID, optional) — Bino bo'yicha filter
- `room_type` (String, optional) — Xona turi bo'yicha filter
- `is_active` (Boolean, optional) — Faol xonalar bo'yicha filter

**Response 200:**
```json
[
  {
    "id": "234e5678-e89b-12d3-a456-426614174005",
    "branch": "456e7890-e89b-12d3-a456-426614174001",
    "branch_name": "Alpha School",
    "building": "123e4567-e89b-12d3-a456-426614174000",
    "building_name": "Asosiy bino",
    "name": "101",
    "room_type": "classroom",
    "room_type_display": "Dars xonasi",
    "floor": 1,
    "capacity": 30,
    "equipment": {
      "projector": true,
      "computers": 0,
      "whiteboard": true
    },
    "is_active": true,
    "created_at": "2024-09-01T10:00:00Z",
    "updated_at": "2024-09-01T10:00:00Z"
  }
]
```

### 7. Xona Yaratish

**POST** `/api/v1/school/branches/{branch_id}/rooms/`

Yangi xona yaratadi.

**Request Body:**
```json
{
  "building": "123e4567-e89b-12d3-a456-426614174000",
  "name": "101",
  "room_type": "classroom",
  "floor": 1,
  "capacity": 30,
  "equipment": {
    "projector": true,
    "computers": 0,
    "whiteboard": true
  },
  "is_active": true
}
```

**Validation Rules:**
- `building` tanlangan filialga tegishli bo'lishi kerak
- `floor` binoning qavatlar sonidan oshib ketmasligi kerak
- `name` tanlangan binoda unique bo'lishi kerak
- `capacity` 1 dan katta bo'lishi kerak

**Response 201:**
```json
{
  "id": "234e5678-e89b-12d3-a456-426614174005",
  "branch": "456e7890-e89b-12d3-a456-426614174001",
  "branch_name": "Alpha School",
  "building": "123e4567-e89b-12d3-a456-426614174000",
  "building_name": "Asosiy bino",
  "name": "101",
  "room_type": "classroom",
  "room_type_display": "Dars xonasi",
  "floor": 1,
  "capacity": 30,
  "equipment": {
    "projector": true,
    "computers": 0,
    "whiteboard": true
  },
  "is_active": true,
  "created_at": "2024-09-01T10:00:00Z",
  "updated_at": "2024-09-01T10:00:00Z"
}
```

**Error 400:**
```json
{
  "building": ["Bino tanlangan filialga tegishli emas."],
  "floor": ["Qavat binoning qavatlar sonidan (3) oshib ketmasligi kerak."]
}
```

### 8. Xona Detallari

**GET** `/api/v1/school/branches/{branch_id}/rooms/{id}/`

Xona to'liq ma'lumotlarini qaytaradi.

**Response 200:** (Xonalar ro'yxati bilan bir xil format)

### 9. Xonani Yangilash

**PATCH** `/api/v1/school/branches/{branch_id}/rooms/{id}/`

Xona ma'lumotlarini yangilaydi.

**Request Body:**
```json
{
  "name": "102",
  "capacity": 35,
  "equipment": {
    "projector": true,
    "computers": 10,
    "whiteboard": true
  },
  "is_active": false
}
```

**Response 200:** (Yangilangan xona ma'lumotlari)

### 10. Xonani O'chirish

**DELETE** `/api/v1/school/branches/{branch_id}/rooms/{id}/`

Xonani soft-delete qiladi.

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

### Bino va xona yaratish

```javascript
// 1. Bino yaratish
const createBuilding = async () => {
  const response = await fetch('/api/v1/school/branches/{branch_id}/buildings/', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer <token>',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      name: 'Asosiy bino',
      address: 'Toshkent shahar, Chilonzor tumani',
      floors: 3,
      description: 'Asosiy o\'quv binosi',
      is_active: true
    })
  });
  const buildingData = await response.json();
  return buildingData;
};

// 2. Xona yaratish
const createRoom = async (buildingId) => {
  const response = await fetch('/api/v1/school/branches/{branch_id}/rooms/', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer <token>',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      building: buildingId,
      name: '101',
      room_type: 'classroom',
      floor: 1,
      capacity: 30,
      equipment: {
        projector: true,
        computers: 0,
        whiteboard: true
      },
      is_active: true
    })
  });
  const roomData = await response.json();
  return roomData;
};
```

### Xonalarni filter qilish

```javascript
// Bino bo'yicha xonalarni olish
const getRoomsByBuilding = async (buildingId) => {
  const response = await fetch(`/api/v1/school/branches/{branch_id}/rooms/?building_id=${buildingId}`, {
    method: 'GET',
    headers: {
      'Authorization': 'Bearer <token>'
    }
  });
  const rooms = await response.json();
  return rooms;
};

// Xona turi bo'yicha filter
const getRoomsByType = async (roomType) => {
  const response = await fetch(`/api/v1/school/branches/{branch_id}/rooms/?room_type=${roomType}`, {
    method: 'GET',
    headers: {
      'Authorization': 'Bearer <token>'
    }
  });
  const rooms = await response.json();
  return rooms;
};
```

### Xona jihozlarini yangilash

```javascript
const updateRoomEquipment = async (roomId, equipment) => {
  const response = await fetch(`/api/v1/school/branches/{branch_id}/rooms/${roomId}/`, {
    method: 'PATCH',
    headers: {
      'Authorization': 'Bearer <token>',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      equipment: equipment
    })
  });
  const updatedRoom = await response.json();
  return updatedRoom;
};

// Misol: Jihozlar yangilash
updateRoomEquipment('room-id', {
  projector: true,
  computers: 20,
  whiteboard: true,
  airConditioner: true
});
```

## Xona Turlari

Xona turlari quyidagilar:

- `classroom` — Dars xonasi
- `lab` — Laboratoriya
- `library` — Kutubxona
- `gym` — Sport zali
- `office` — Ofis
- `auditorium` — Auditoriya
- `other` — Boshqa

## Eslatmalar

1. **Soft Delete**: Bino yoki xona o'chirilganda, ular `deleted_at` maydoni bilan belgilanadi va faol ro'yxatlarda ko'rinmaydi.

2. **Unique Constraints**: 
   - Har bir filial uchun bino nomi unique
   - Har bir filial va bino uchun xona nomi unique

3. **Relationships**:
   - Bino filialga bog'liq
   - Xona bino va filialga bog'liq
   - Xona sinflarga bog'liq (Class modelida `room` field)

4. **Validation**:
   - Xona qavati binoning qavatlar sonidan oshib ketmasligi kerak
   - Bino va xona bir xil filialga tegishli bo'lishi kerak

5. **Equipment Field**:
   - Equipment JSON formatida saqlanadi
   - Har qanday struktura bo'lishi mumkin (masalan: `{"projector": true, "computers": 20}`)
   - Frontend tomonidan to'liq boshqariladi

