# API Hujjatlari

Bu papka barcha API endpointlarining to'liq hujjatlarini o'z ichiga oladi.

## Asosiy API'lar

- [Auth API](auth.md) - Autentifikatsiya, OTP, JWT
- [Branch API](branch.md) - Filiallar boshqaruvi
- [Profile API](profile.md) - Foydalanuvchi profillari

## Maktab Moduli API'lar

- [Academic API](academic.md) - Akademik yillar va choraklar
- [Classes API](academic.md) - Sinflar boshqaruvi
- [Subjects API](subjects.md) - Fanlar boshqaruvi
- [Rooms API](rooms.md) - Binolar va xonalar
- [Students API](students.md) - O'quvchilar va ularning yaqinlari
- [Dashboard API](dashboard.md) - O'qituvchi va o'quvchi dashboard
- [Finance API](finance.md) - Moliya tizimi (Kassalar, Tranzaksiyalar, To'lovlar, Tariflar, Chegirmalar)

## Qo'shimcha Hujjatlar

- [Filtering, Search va Ordering](filtering-search-ordering.md) - Qidiruv, filter va ordering qo'llanmasi
- [API Overview](overview.md) - Umumiy API ma'lumotlari

## Umumiy Ma'lumotlar

### Base URL
```
/api/v1/
```

### Authentication
Barcha API'lar JWT token talab qiladi:
```
Authorization: Bearer <access_token>
```

### Branch Context
Ko'p filialli tizimda, branch context quyidagi usullar bilan aniqlanadi:
1. JWT token ichidagi `br` claim
2. `X-Branch-Id` header
3. `branch_id` query parameter

### Pagination
Barcha list endpointlar pagination qo'llab-quvvatlaydi:
- Default: 20 element
- Max: 100 element
- Query: `?page=1&page_size=20`

### Filtering, Search, Ordering
Barcha list endpointlar filtering, search va ordering qo'llab-quvvatlaydi:
- `search` - Qidirish
- `ordering` - Tartiblash
- Filter parametrlar - Har bir endpoint uchun alohida

### Valyuta
Barcha moliyaviy summalar so'm (butun sonlar) formatida.

### Avtomatik Yaratiladigan Modellar

Quyidagi modellar signallar orqali avtomatik yaratiladi:

1. **Profile** - `User` yaratilganda
2. **BranchSettings** - `Branch` yaratilganda
3. **Role Profiles** - `BranchMembership` yaratilganda:
   - `UserBranchProfile` (har doim)
   - `StudentProfile` (role=student)
   - `TeacherProfile` (role=teacher)
   - `ParentProfile` (role=parent)
   - `AdminProfile` (role=branch_admin yoki super_admin)
4. **StudentBalance** - `StudentProfile` yaratilganda

## Xatoliklar

Barcha API'lar quyidagi xatolik formatini qaytaradi:

```json
{
  "detail": "Human-readable error message",
  "code": "error_code_optional"
}
```

### Xatolik Kodlari

- `400` - Bad Request (noto'g'ri so'rov)
- `401` - Unauthorized (autentifikatsiya talab qilinadi)
- `403` - Forbidden (ruxsat yo'q)
- `404` - Not Found (obyekt topilmadi)
- `500` - Internal Server Error (server xatosi)

## Rate Limiting

- Webhooklar uchun alohida throttling
- Auth/OTP endpointlari uchun qat'iy throttling (brute-force oldini olish)

## Versiyalash

- Hozirgi versiya: v1
- Path-based versiyalash: `/api/v1/...`
- Breaking change bo'lsa v2 ga ko'tariladi

