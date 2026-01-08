# Joriy Timetable API - To'liq Hujjat

## Umumiy Ma'lumot

Bu API joriy aktiv chorak uchun dars jadvali shablonini olish yoki yaratish uchun ishlatiladi.

**Asosiy xususiyatlar:**
- JWT tokendan branch_id olinadi (`br` claim)
- URL'da branch_id kerak emas
- Avtomatik chorak aniqlash (is_active yoki bugungi sana bo'yicha)
- Idempotent POST (mavjud bo'lsa qaytaradi, yo'q bo'lsa yaratadi)

## Endpoint

```
GET/POST /api/v1/schedule/timetables/current/
```

## Authentication

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

JWT tokenida `br` claim bo'lishi kerak (branch UUID).

## Permissions

**GET:**
- `branch_admin`, `super_admin`, `teacher`, `student`, `parent`
- Barcha rol'lar o'qiy oladi

**POST:**
- `branch_admin`, `super_admin`
- Faqat adminlar yaratishi mumkin

## GET Request

Joriy aktiv chorak uchun template qaytaradi.

### Success Response (200)

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "branch": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "branch_name": "Markaziy filial",
  "academic_year": "b0e42fe4-6b3a-4b7e-9c2d-8f1a3b4c5d6e",
  "academic_year_name": "2025-2026",
  "name": "1-chorak - 2025-2026",
  "description": "Avtomatik yaratilgan jadval - 1-chorak",
  "is_active": true,
  "effective_from": "2025-09-02",
  "effective_until": "2025-11-04",
  "slots_count": 120,
  "created_at": "2025-09-01T10:00:00Z",
  "updated_at": "2025-09-01T10:00:00Z"
}
```

### Error Response (404 - Template topilmadi)

```json
{
  "error": "Joriy chorak uchun aktiv template topilmadi.",
  "quarter": {
    "id": "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
    "name": "1-chorak",
    "number": 1,
    "start_date": "2025-09-02",
    "end_date": "2025-11-04"
  }
}
```

**Izoh:** Bu response frontendga template yaratish taklif qilish uchun foydali. Chorak ma'lumotlari bilan POST so'rovini yuborish mumkin.

### Error Response (404 - Akademik yil topilmadi)

```json
{
  "error": "Aktiv akademik yil topilmadi. Iltimos, avval akademik yil yarating."
}
```

### Error Response (404 - Chorak topilmadi)

```json
{
  "error": "Joriy chorak topilmadi. Iltimos, choraklar sozlamalarini tekshiring."
}
```

## POST Request

Joriy aktiv chorak uchun template yaratadi. Agar mavjud bo'lsa, mavjud templateni qaytaradi.

### Request Body

**Bo'sh body:**
```json
{}
```

Barcha ma'lumotlar avtomatik to'ldiriladi:
- `branch` - JWT tokendan
- `academic_year` - Aktiv akademik yildan
- `name` - `"{chorak.name} - {academic_year.name}"`
- `description` - `"Avtomatik yaratilgan jadval - {chorak.name}"`
- `is_active` - `true`
- `effective_from` - `quarter.start_date`
- `effective_until` - `quarter.end_date`

### Success Response (201 - Yangi yaratildi)

```json
{
  "id": "8d7c6b5a-4e3d-2c1b-0a9f-8e7d6c5b4a3f",
  "branch": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "branch_name": "Markaziy filial",
  "academic_year": "b0e42fe4-6b3a-4b7e-9c2d-8f1a3b4c5d6e",
  "academic_year_name": "2025-2026",
  "name": "1-chorak - 2025-2026",
  "description": "Avtomatik yaratilgan jadval - 1-chorak",
  "is_active": true,
  "effective_from": "2025-09-02",
  "effective_until": "2025-11-04",
  "slots_count": 0,
  "created_at": "2025-09-01T12:30:45Z",
  "updated_at": "2025-09-01T12:30:45Z"
}
```

### Success Response (200 - Mavjud qaytarildi)

Agar template allaqachon mavjud bo'lsa, uni qaytaradi (201 emas, 200):

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "branch": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "branch_name": "Markaziy filial",
  "academic_year": "b0e42fe4-6b3a-4b7e-9c2d-8f1a3b4c5d6e",
  "academic_year_name": "2025-2026",
  "name": "1-chorak - 2025-2026",
  "description": "Avtomatik yaratilgan jadval - 1-chorak",
  "is_active": true,
  "effective_from": "2025-09-02",
  "effective_until": "2025-11-04",
  "slots_count": 120,
  "created_at": "2025-09-01T10:00:00Z",
  "updated_at": "2025-09-01T10:00:00Z"
}
```

**Idempotency:** POST so'rovini bir necha marta yuborish xavfsiz - mavjud template qaytariladi.

### Error Response (400 - Branch ID topilmadi)

```json
{
  "error": "Branch ID topilmadi. JWT tokenni tekshiring."
}
```

**Sabab:** JWT tokenida `br` claim yo'q.

### Error Response (403 - Ruxsat yo'q)

```json
{
  "error": "Faqat adminlar yangi template yaratishi mumkin."
}
```

**Sabab:** Foydalanuvchi `branch_admin` yoki `super_admin` emas.

### Error Response (404 - Prerequisite yo'q)

Akademik yil yoki chorak topilmadi (GET'dagi kabi).

## Ishlash Jarayoni

### 1. Joriy Chorakni Aniqlash

API quyidagi tartibda chorakni aniqlaydi:

1. **Aktiv akademik yilni topadi:**
   - `AcademicYear.is_active = True`
   - Agar yo'q: 404 error

2. **Aktiv chorakni topadi:**
   - Avval `Quarter.is_active = True` qidiradi
   - Agar yo'q: bugungi sana bilan moslashtiradi
     - `quarter.start_date <= today <= quarter.end_date`
   - Agar yo'q: 404 error

3. **Template topadi:**
   - `TimetableTemplate.is_active = True`
   - `effective_from <= quarter.end_date`
   - `effective_until >= quarter.start_date` (yoki NULL)

### 2. Template Yaratish (POST)

Agar template topilmasa, yangi yaratadi:

```python
template = TimetableTemplate.objects.create(
    branch_id=branch_id,  # JWT tokendan
    academic_year=academic_year,  # Aktiv yil
    name=f"{quarter.name} - {academic_year.name}",  # "1-chorak - 2025-2026"
    description=f"Avtomatik yaratilgan jadval - {quarter.name}",
    is_active=True,
    effective_from=quarter.start_date,  # 2025-09-02
    effective_until=quarter.end_date,  # 2025-11-04
    created_by=request.user
)
```

**Auto-deactivation:** `is_active=True` bo'lganda, bir xil branch va academic_year uchun boshqa templatelar avtomatik `is_active=False` bo'ladi.

## Frontend Integratsiya

### React/TypeScript Example

```typescript
// types/schedule.ts
interface TimetableTemplate {
  id: string;
  branch: string;
  branch_name: string;
  academic_year: string;
  academic_year_name: string;
  name: string;
  description: string;
  is_active: boolean;
  effective_from: string; // YYYY-MM-DD
  effective_until: string | null;
  slots_count: number;
  created_at: string;
  updated_at: string;
}

interface CurrentTimetableError {
  error: string;
  quarter?: {
    id: string;
    name: string;
    number: number;
    start_date: string;
    end_date: string;
  };
}

// hooks/use-current-timetable.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/lib/api-client';

export function useCurrentTimetable() {
  return useQuery<TimetableTemplate>({
    queryKey: ['timetable', 'current'],
    queryFn: async () => {
      const { data } = await apiClient.get<TimetableTemplate>(
        '/schedule/timetables/current/'
      );
      return data;
    },
    retry: false, // 404 uchun retry yo'q
  });
}

export function useCreateCurrentTimetable() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post<TimetableTemplate>(
        '/schedule/timetables/current/',
        {}
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timetable', 'current'] });
      toast.success('Jadval yaratildi');
    },
    onError: (error: any) => {
      const message = error.response?.data?.error || 'Xatolik yuz berdi';
      toast.error(message);
    },
  });
}

// components/TimetableManager.tsx
function TimetableManager() {
  const { data: timetable, isLoading, error } = useCurrentTimetable();
  const createTimetable = useCreateCurrentTimetable();
  
  if (isLoading) {
    return <Skeleton />;
  }
  
  if (error) {
    const errorData = error.response?.data as CurrentTimetableError;
    
    return (
      <div className="alert alert-warning">
        <p>{errorData.error}</p>
        {errorData.quarter && (
          <>
            <p>Chorak: {errorData.quarter.name}</p>
            <p>Muddat: {errorData.quarter.start_date} - {errorData.quarter.end_date}</p>
            <button onClick={() => createTimetable.mutate()}>
              Jadval Yaratish
            </button>
          </>
        )}
      </div>
    );
  }
  
  return (
    <div>
      <h2>{timetable.name}</h2>
      <p>{timetable.description}</p>
      <p>Slotlar: {timetable.slots_count}</p>
      {/* Slots management UI */}
    </div>
  );
}
```

## Use Cases

### 1. Admin Jadval Boshqaruvi

```javascript
// Admin sahifasi yuklanganda
const { data: timetable } = useCurrentTimetable();

// Agar template yo'q bo'lsa, yaratish tugmasi ko'rsatiladi
if (!timetable) {
  <button onClick={createTimetable}>Jadval Yaratish</button>
}

// Template mavjud bo'lsa, slotlar boshqarish
if (timetable) {
  <TimetableSlotManager timetableId={timetable.id} />
}
```

### 2. O'qituvchi Dashboard

```javascript
// O'qituvchi faqat o'qiy oladi
const { data: timetable } = useCurrentTimetable();

if (timetable) {
  // O'z darslarini ko'rish
  <TeacherLessons timetableId={timetable.id} />
}
```

### 3. Mobile App

```javascript
// Mobile app'da JWT token bilan so'rov
const getCurrentTimetable = async (token) => {
  try {
    const response = await fetch(API_URL + '/schedule/timetables/current/', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      }
    });
    
    if (response.status === 404) {
      const error = await response.json();
      // Show "No timetable" message with quarter info
      return { error, timetable: null };
    }
    
    const timetable = await response.json();
    return { timetable, error: null };
  } catch (err) {
    // Handle network errors
    return { error: err.message, timetable: null };
  }
};
```

## Testing

### cURL Examples

**GET:**
```bash
curl -X GET "http://localhost:8000/api/v1/schedule/timetables/current/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

**POST:**
```bash
curl -X POST "http://localhost:8000/api/v1/schedule/timetables/current/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Postman

1. Create new request
2. Method: GET or POST
3. URL: `{{base_url}}/schedule/timetables/current/`
4. Headers:
   - Authorization: `Bearer {{access_token}}`
   - Content-Type: `application/json`
5. Body (POST only): `{}`

## Best Practices

1. **Cache timetable data:**
   - Use React Query cache
   - `staleTime: 5 * 60 * 1000` (5 minutes)

2. **Error handling:**
   - Show helpful messages with quarter info
   - Provide "Create" action for admins

3. **Optimistic updates:**
   - POST so'rovidan keyin cache'ni yangilash

4. **Loading states:**
   - Skeleton loaders
   - Disable buttons during mutations

5. **Permissions:**
   - Client-side permission check
   - Hide "Create" button for non-admins

## Troubleshooting

### JWT tokenida `br` claim yo'q
**Xato:** `Branch ID topilmadi`
**Yechim:** Login qayta qiling yoki token refresh qiling

### Aktiv akademik yil yo'q
**Xato:** `Aktiv akademik yil topilmadi`
**Yechim:** Admin panelda akademik yil yarating va `is_active=True` qiling

### Choraklar yaratilmagan
**Xato:** `Joriy chorak topilmadi`
**Yechim:** 
- Akademik yil yaratilganda choraklar avtomatik yaratiladi
- Eski akademik yillar uchun qo'lda chorak qo'shing

### Teacher POST qila olmaydi
**Xato:** `Faqat adminlar yangi template yaratishi mumkin`
**Yechim:** Bu normal - faqat GET ishlatsin

## Related APIs

- **Joriy Chorak:** `GET /api/v1/school/academic/branches/{branch_id}/quarters/current/`
- **Template Ro'yxati:** `GET /api/v1/schedule/branches/{branch_id}/timetables/`
- **Slotlar:** `GET /api/v1/schedule/branches/{branch_id}/timetables/{template_id}/slots/`
