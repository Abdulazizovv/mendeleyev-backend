# Super Admin API-lari Rejasi

## Maqsad
Super Adminlar uchun platforma bo'ylab barcha ma'lumotlarni ko'rish va boshqarish imkoniyatini beruvchi dashboard API-lari.

## Asosiy prinsiplar
- Super Adminlar barcha filiallardagi ma'lumotlarni ko'ra oladi
- Super Adminlar barcha foydalanuvchilarni, rollarni, a'zoliklarni boshqara oladi
- Super Adminlar statistika va hisobotlarni ko'ra oladi
- Barcha endpointlar `IsSuperAdmin` permission bilan himoyalangan

## API Endpointlar

### 1. Dashboard Statistika
**GET** `/api/super-admin/dashboard/stats/`

Umumiy statistika:
- Jami filiallar soni (active/inactive/archived)
- Jami foydalanuvchilar soni
- Jami xodimlar soni (teachers, admins, etc.)
- Jami o'quvchilar soni
- Jami ota-onalar soni
- Jami maosh fondi (oylik)
- Jami balanslar yig'indisi

**Response:**
```json
{
  "branches": {
    "total": 10,
    "active": 8,
    "inactive": 1,
    "archived": 1
  },
  "users": {
    "total": 500,
    "teachers": 50,
    "students": 400,
    "parents": 45,
    "admins": 5
  },
  "finance": {
    "total_monthly_salary": 50000000,
    "total_balances": 10000000
  }
}
```

### 2. Filiallar Boshqaruvi

#### 2.1. Barcha filiallar ro'yxati
**GET** `/api/super-admin/branches/`

- Barcha filiallar (active, inactive, archived)
- Filter: `?status=active&type=school`
- Search: `?search=alpha`
- Pagination

**Response:**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "<uuid>",
      "name": "Alpha School",
      "type": "school",
      "status": "active",
      "members_count": 150,
      "created_at": "..."
    }
  ]
}
```

#### 2.2. Filial detallari
**GET** `/api/super-admin/branches/{branch_id}/`

- Filial to'liq ma'lumotlari
- Filial statistikasi
- Filial xodimlari soni
- Filial o'quvchilari soni

#### 2.3. Filial yaratish
**POST** `/api/super-admin/branches/`

#### 2.4. Filial yangilash
**PATCH** `/api/super-admin/branches/{branch_id}/`

#### 2.5. Filial o'chirish (soft delete)
**DELETE** `/api/super-admin/branches/{branch_id}/`

### 3. Foydalanuvchilar Boshqaruvi

#### 3.1. Barcha foydalanuvchilar ro'yxati
**GET** `/api/super-admin/users/`

- Barcha foydalanuvchilar
- Filter: `?role=teacher&branch_id=<uuid>`
- Search: `?search=+998901234567`
- Pagination

#### 3.2. Foydalanuvchi detallari
**GET** `/api/super-admin/users/{user_id}/`

- Foydalanuvchi to'liq ma'lumotlari
- Barcha filiallardagi a'zoliklari
- Profil ma'lumotlari

#### 3.3. Foydalanuvchi yaratish
**POST** `/api/super-admin/users/`

#### 3.4. Foydalanuvchi yangilash
**PATCH** `/api/super-admin/users/{user_id}/`

#### 3.5. Foydalanuvchi o'chirish (soft delete)
**DELETE** `/api/super-admin/users/{user_id}/`

### 4. A'zoliklar Boshqaruvi

#### 4.1. Barcha a'zoliklar ro'yxati
**GET** `/api/super-admin/memberships/`

- Barcha filiallardagi a'zoliklar
- Filter: `?branch_id=<uuid>&role=teacher`
- Search: `?search=+998901234567`
- Pagination

#### 4.2. A'zolik yaratish
**POST** `/api/super-admin/memberships/`

- User va Branch tanlash
- Rol belgilash
- Maosh konfiguratsiyasi

#### 4.3. A'zolik yangilash
**PATCH** `/api/super-admin/memberships/{membership_id}/`

- Rol o'zgartirish
- Maosh o'zgartirish
- Balans o'zgartirish

#### 4.4. A'zolik o'chirish
**DELETE** `/api/super-admin/memberships/{membership_id}/`

### 5. Rollar Boshqaruvi

#### 5.1. Barcha rollar ro'yxati
**GET** `/api/super-admin/roles/`

- Barcha filiallardagi rollar
- Filter: `?branch_id=<uuid>`
- Search: `?search=director`

#### 5.2. Rol yaratish
**POST** `/api/super-admin/roles/`

#### 5.3. Rol yangilash
**PATCH** `/api/super-admin/roles/{role_id}/`

#### 5.4. Rol o'chirish
**DELETE** `/api/super-admin/roles/{role_id}/`

### 6. Moliya Boshqaruvi

#### 6.1. Umumiy moliya statistika
**GET** `/api/super-admin/finance/stats/`

- Jami maosh fondi
- Jami balanslar
- Filiallar bo'yicha taqsimot

#### 6.2. Maosh hisobotlari
**GET** `/api/super-admin/finance/salaries/`

- Barcha xodimlar maoshlari
- Filial bo'yicha guruhlash
- Maosh turi bo'yicha guruhlash

#### 6.3. Balans operatsiyalari
**GET** `/api/super-admin/finance/balance-operations/`

- Barcha balans o'zgarishlari
- Filter: `?branch_id=<uuid>&date_from=...&date_to=...`

### 7. Hisobotlar

#### 7.1. Foydalanuvchilar hisoboti
**GET** `/api/super-admin/reports/users/`

- Filiallar bo'yicha taqsimot
- Rollar bo'yicha taqsimot
- Aktivlik statistikasi

#### 7.2. Filiallar hisoboti
**GET** `/api/super-admin/reports/branches/`

- Filiallar statistikasi
- Filiallar bo'yicha xodimlar soni
- Filiallar bo'yicha o'quvchilar soni

## Permission
- Barcha endpointlar `IsSuperAdmin` permission bilan himoyalangan
- `apps/common/permissions.py` da `IsSuperAdmin` class mavjud

## Implementation Plan

### Bosqich 1: Asosiy struktura
1. `apps/super_admin/` package yaratish
2. `apps/super_admin/views.py` - barcha viewlar
3. `apps/super_admin/serializers.py` - serializers
4. `apps/super_admin/urls.py` - URL routing
5. `core/urls.py` ga qo'shish

### Bosqich 2: Dashboard va Statistika
1. Dashboard stats endpoint
2. Umumiy statistika hisoblash

### Bosqich 3: CRUD operatsiyalar
1. Filiallar CRUD
2. Foydalanuvchilar CRUD
3. A'zoliklar CRUD
4. Rollar CRUD

### Bosqich 4: Moliya va Hisobotlar
1. Moliya statistika
2. Hisobotlar

### Bosqich 5: Test va Hujjatlashtirish
1. Testlar yozish
2. API hujjatlashtirish

## Keyingi qadamlar
1. Super Admin API-larini implementatsiya qilish
2. Testlar yozish
3. Frontend uchun hujjatlashtirish

