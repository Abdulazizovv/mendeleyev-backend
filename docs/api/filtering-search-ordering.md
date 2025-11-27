# Filtering, Search va Ordering

Bu hujjat barcha API-larda qidiruv, filter va ordering funksiyalarini tushuntirish uchun yaratilgan.

## 📋 Umumiy Ma'lumotlar

Barcha list API-lar quyidagi funksiyalarni qo'llab-quvvatlaydi:

1. **Paginatsiya** - Sahifalash (default: 20 element, max: 100)
2. **Qidiruv (Search)** - Matn bo'yicha qidirish
3. **Filter** - Aniq maydonlar bo'yicha filter
4. **Ordering** - Tartiblash

## 🔍 Query Parameters

### Paginatsiya
- `page` - Sahifa raqami (default: 1)
- `page_size` - Sahifadagi elementlar soni (default: 20, max: 100)

### Qidiruv (Search)
- `search` - Umumiy qidiruv (ko'p maydonlarda qidiradi)

### Ordering
- `ordering` - Tartiblash (masalan: `created_at`, `-created_at`, `name`, `-name`)
  - `-` belgisi teskari tartibni bildiradi

---

## 📚 API-lar bo'yicha Detallar

### 1. Students API (`/api/v1/school/students/`)

#### Query Parameters

**Qidiruv:**
- `search` - Shaxsiy raqam, ism, telefon, email bo'yicha qidirish
- `personal_number` - Shaxsiy raqam bo'yicha qidirish
- `first_name` - Ism bo'yicha qidirish
- `last_name` - Familiya bo'yicha qidirish
- `phone_number` - Telefon raqam bo'yicha qidirish
- `email` - Email bo'yicha qidirish

**Filter:**
- `gender` - Jinsi bo'yicha filter (`male`, `female`, `other`, `unspecified`)
- `date_of_birth` - Tu'gilgan sana bo'yicha filter
- `date_of_birth__gte` - Tu'gilgan sana (dan)
- `date_of_birth__lte` - Tu'gilgan sana (gacha)
- `branch_id` - Filial ID bo'yicha filter
- `class_id` - Sinf ID bo'yicha filter
- `grade_level` - Sinf darajasi bo'yicha filter
- `created_at__gte` - Yaratilgan sana (dan)
- `created_at__lte` - Yaratilgan sana (gacha)

**Ordering:**
- `ordering` - Tartiblash maydonlari:
  - `personal_number` - Shaxsiy raqam
  - `first_name` - Ism
  - `last_name` - Familiya
  - `created_at` - Yaratilgan sana
  - `date_of_birth` - Tu'gilgan sana
  - `gender` - Jinsi

#### Misollar

```javascript
// Qidiruv
GET /api/v1/school/students/?search=Ali
GET /api/v1/school/students/?personal_number=ST-2024-0001

// Filter
GET /api/v1/school/students/?gender=male
GET /api/v1/school/students/?class_id=123e4567-e89b-12d3-a456-426614174000
GET /api/v1/school/students/?date_of_birth__gte=2010-01-01&date_of_birth__lte=2015-12-31

// Ordering
GET /api/v1/school/students/?ordering=first_name
GET /api/v1/school/students/?ordering=-created_at

// Kombinatsiya
GET /api/v1/school/students/?search=Ali&gender=male&ordering=-created_at&page=1&page_size=50
```

---

### 2. Classes API (`/api/v1/school/classes/`)

#### Query Parameters

**Qidiruv:**
- `search` - Sinf nomi, sinf rahbari bo'yicha qidirish
- `name` - Sinf nomi bo'yicha qidirish

**Filter:**
- `academic_year_id` - Akademik yil ID bo'yicha filter
- `grade_level` - Sinf darajasi bo'yicha filter (1-11)
- `section` - Bo'lim bo'yicha filter (A, B, C, ...)
- `is_active` - Faol sinflar bo'yicha filter (`true`/`false`)
- `class_teacher_id` - Sinf rahbari ID bo'yicha filter
- `room_id` - Xona ID bo'yicha filter

**Ordering:**
- `ordering` - Tartiblash maydonlari:
  - `name` - Sinf nomi
  - `grade_level` - Sinf darajasi
  - `created_at` - Yaratilgan sana
  - `academic_year__start_date` - Akademik yil boshlanish sanasi

#### Misollar

```javascript
// Qidiruv
GET /api/v1/school/classes/?search=5-A

// Filter
GET /api/v1/school/classes/?grade_level=5&section=A
GET /api/v1/school/classes/?is_active=true&academic_year_id=123e4567-e89b-12d3-a456-426614174000

// Ordering
GET /api/v1/school/classes/?ordering=grade_level
GET /api/v1/school/classes/?ordering=-created_at

// Kombinatsiya
GET /api/v1/school/classes/?grade_level=5&is_active=true&ordering=name&page=1
```

---

### 3. Subjects API (`/api/v1/school/subjects/`)

#### Query Parameters

**Qidiruv:**
- `search` - Fan nomi, kod bo'yicha qidirish
- `name` - Fan nomi bo'yicha qidirish
- `code` - Fan kodi bo'yicha qidirish

**Filter:**
- `is_active` - Faol fanlar bo'yicha filter (`true`/`false`)

**Ordering:**
- `ordering` - Tartiblash maydonlari:
  - `name` - Fan nomi
  - `code` - Fan kodi
  - `created_at` - Yaratilgan sana

#### Misollar

```javascript
// Qidiruv
GET /api/v1/school/subjects/?search=Matematika

// Filter
GET /api/v1/school/subjects/?is_active=true

// Ordering
GET /api/v1/school/subjects/?ordering=name

// Kombinatsiya
GET /api/v1/school/subjects/?search=Mat&is_active=true&ordering=name
```

---

### 4. Class Subjects API (`/api/v1/school/subjects/classes/{class_id}/subjects/`)

#### Query Parameters

**Qidiruv:**
- `search` - Fan nomi, o'qituvchi bo'yicha qidirish

**Filter:**
- `subject_id` - Fan ID bo'yicha filter
- `teacher_id` - O'qituvchi ID bo'yicha filter
- `quarter_id` - Chorak ID bo'yicha filter
- `is_active` - Faol fanlar bo'yicha filter (`true`/`false`)

**Ordering:**
- `ordering` - Tartiblash maydonlari:
  - `created_at` - Yaratilgan sana
  - `subject__name` - Fan nomi

#### Misollar

```javascript
// Qidiruv
GET /api/v1/school/subjects/classes/{class_id}/subjects/?search=Matematika

// Filter
GET /api/v1/school/subjects/classes/{class_id}/subjects/?teacher_id=123e4567-e89b-12d3-a456-426614174000
GET /api/v1/school/subjects/classes/{class_id}/subjects/?is_active=true&quarter_id=123e4567-e89b-12d3-a456-426614174000

// Ordering
GET /api/v1/school/subjects/classes/{class_id}/subjects/?ordering=subject__name
```

---

### 5. Rooms API (`/api/v1/school/rooms/`)

#### Query Parameters

**Qidiruv:**
- `search` - Xona nomi, raqam bo'yicha qidirish
- `name` - Xona nomi bo'yicha qidirish
- `number` - Xona raqami bo'yicha qidirish

**Filter:**
- `building_id` - Bino ID bo'yicha filter
- `room_type` - Xona turi bo'yicha filter
- `is_active` - Faol xonalar bo'yicha filter (`true`/`false`)

**Ordering:**
- `ordering` - Tartiblash maydonlari:
  - `name` - Xona nomi
  - `number` - Xona raqami
  - `created_at` - Yaratilgan sana

#### Misollar

```javascript
// Qidiruv
GET /api/v1/school/rooms/?search=101

// Filter
GET /api/v1/school/rooms/?building_id=123e4567-e89b-12d3-a456-426614174000&room_type=classroom
GET /api/v1/school/rooms/?is_active=true

// Ordering
GET /api/v1/school/rooms/?ordering=number
```

---

### 6. Buildings API (`/api/v1/school/rooms/buildings/`)

#### Query Parameters

**Qidiruv:**
- `search` - Bino nomi, manzil bo'yicha qidirish
- `name` - Bino nomi bo'yicha qidirish

**Filter:**
- `is_active` - Faol binolar bo'yicha filter (`true`/`false`)

**Ordering:**
- `ordering` - Tartiblash maydonlari:
  - `name` - Bino nomi
  - `created_at` - Yaratilgan sana

#### Misollar

```javascript
// Qidiruv
GET /api/v1/school/rooms/buildings/?search=Asosiy

// Filter
GET /api/v1/school/rooms/buildings/?is_active=true

// Ordering
GET /api/v1/school/rooms/buildings/?ordering=name
```

---

### 7. Academic Years API (`/api/v1/school/academic/years/`)

#### Query Parameters

**Qidiruv:**
- `search` - Akademik yil nomi bo'yicha qidirish

**Ordering:**
- `ordering` - Tartiblash maydonlari:
  - `start_date` - Boshlanish sanasi
  - `end_date` - Tugash sanasi
  - `created_at` - Yaratilgan sana
  - `name` - Akademik yil nomi

#### Misollar

```javascript
// Qidiruv
GET /api/v1/school/academic/years/?search=2024

// Ordering
GET /api/v1/school/academic/years/?ordering=-start_date
```

---

### 8. Quarters API (`/api/v1/school/academic/years/{academic_year_id}/quarters/`)

#### Query Parameters

**Qidiruv:**
- `search` - Chorak nomi bo'yicha qidirish

**Ordering:**
- `ordering` - Tartiblash maydonlari:
  - `start_date` - Boshlanish sanasi
  - `end_date` - Tugash sanasi
  - `created_at` - Yaratilgan sana
  - `number` - Chorak raqami

#### Misollar

```javascript
// Qidiruv
GET /api/v1/school/academic/years/{academic_year_id}/quarters/?search=1-chorak

// Ordering
GET /api/v1/school/academic/years/{academic_year_id}/quarters/?ordering=number
```

---

### 9. Class Students API (`/api/v1/school/classes/{class_id}/students/`)

#### Query Parameters

**Qidiruv:**
- `search` - O'quvchi ismi, telefon bo'yicha qidirish

**Filter:**
- `is_active` - Faol o'quvchilar bo'yicha filter (`true`/`false`)

**Ordering:**
- `ordering` - Tartiblash maydonlari:
  - `created_at` - Yaratilgan sana
  - `membership__user__first_name` - O'quvchi ismi
  - `membership__user__last_name` - O'quvchi familiyasi

#### Misollar

```javascript
// Qidiruv
GET /api/v1/school/classes/{class_id}/students/?search=Ali

// Filter
GET /api/v1/school/classes/{class_id}/students/?is_active=true

// Ordering
GET /api/v1/school/classes/{class_id}/students/?ordering=membership__user__first_name
```

---

## 💡 Best Practices

1. **Paginatsiya** - Katta ma'lumotlar uchun har doim paginatsiyadan foydalaning
2. **Search** - Umumiy qidiruv uchun `search` parametridan foydalaning
3. **Filter** - Aniq maydonlar bo'yicha filter qilish uchun maxsus filter parametrlaridan foydalaning
4. **Ordering** - Natijalarni tartiblash uchun `ordering` parametridan foydalaning
5. **Kombinatsiya** - Bir nechta parametrlarni birga ishlatish mumkin

## 🔧 JavaScript Misollar

```javascript
// Axios misol
const axios = require('axios');

// Students qidiruv
const searchStudents = async (query) => {
  const response = await axios.get('/api/v1/school/students/', {
    params: {
      search: query,
      ordering: '-created_at',
      page: 1,
      page_size: 20
    }
  });
  return response.data;
};

// Classes filter
const filterClasses = async (gradeLevel, isActive) => {
  const response = await axios.get('/api/v1/school/classes/', {
    params: {
      grade_level: gradeLevel,
      is_active: isActive,
      ordering: 'name'
    }
  });
  return response.data;
};
```

## 📝 Eslatmalar

- Barcha filter parametrlari ixtiyoriy
- `search` parametri ko'p maydonlarda qidiradi
- `ordering` parametrida `-` belgisi teskari tartibni bildiradi
- Paginatsiya default: 20 element, max: 100 element
- Barcha API-lar DRF ning built-in filtering, search va ordering funksiyalaridan foydalanadi


