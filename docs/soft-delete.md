# Soft Delete Implementation

## Umumiy Ma'lumot

Loyihada professional soft delete tizimi joriy qilindi. Barcha modellar `BaseModel` dan meros oladi va soft delete qo'llab-quvvatlaydi.

## BaseModel Metodlari

### 1. `soft_delete(user=None)`

Obyektni soft delete qiladi (`deleted_at` timestamp o'rnatadi).

**Parametrlar:**
- `user` (optional): Audit trail uchun - kim o'chirgan

**Returns:** `self` - O'chirilgan obyekt

**Misol:**
```python
from apps.branch.models import BranchMembership

staff = BranchMembership.objects.get(id=staff_id)
staff.soft_delete(user=request.user)
```

### 2. `delete(hard=False)`

Default soft delete. `hard=True` bo'lsa permanent delete.

**Parametrlar:**
- `hard` (default: False): Agar True bo'lsa, permanent o'chiradi

**Misol:**
```python
# Soft delete
staff.delete()  # yoki staff.delete(hard=False)

# Hard delete (permanent)
staff.delete(hard=True)
```

### 3. `hard_delete()`

Obyektni permanent o'chiradi (database dan butunlay).

**Misol:**
```python
staff.hard_delete()
```

### 4. `restore()`

Soft delete qilingan obyektni tiklaydi.

**Misol:**
```python
staff.restore()
```

## BranchMembership Custom Implementation

`BranchMembership` modeli uchun maxsus `soft_delete()` va `restore()` metodlari mavjud.

### Xususiyatlari:

1. **Soft Delete:**
   - `deleted_at` o'rnatadi
   - `termination_date` o'rnatadi (xodimlar uchun)
   - Audit trail yangilanadi (`updated_by`)

2. **Restore:**
   - `deleted_at` ni tozalaydi
   - `termination_date` ni tozalaydi
   - Xodim qayta ishga qabul qilinganga o'xshaydi

### Misol:

```python
from apps.branch.models import BranchMembership
from django.utils import timezone

# Xodimni ishdan chiqarish (soft delete)
staff = BranchMembership.objects.get(id=staff_id)
staff.soft_delete(user=request.user)

# Natija:
# - deleted_at: 2024-12-20 10:30:00
# - termination_date: 2024-12-20
# - updated_by: request.user

# Xodimni qayta tiklash
staff.restore()

# Natija:
# - deleted_at: None
# - termination_date: None
```

## BaseManager Metodlari

### 1. `active()`

Faqat o'chirilmagan (faol) obyektlarni qaytaradi.

**Misol:**
```python
# Faqat faol xodimlar
active_staff = BranchMembership.objects.active()

# Faqat faol branchlar
active_branches = Branch.objects.active()
```

### 2. `deleted()`

Faqat o'chirilgan obyektlarni qaytaradi.

**Misol:**
```python
# O'chirilgan xodimlar
deleted_staff = BranchMembership.objects.deleted()
```

## Properties

### `is_active`

Obyekt faolmi yoki yo'qligini tekshiradi.

```python
if staff.is_active:
    print("Xodim hali ishlamoqda")
```

### `is_deleted`

Obyekt o'chirilganmi yoki yo'qligini tekshiradi.

```python
if staff.is_deleted:
    print("Xodim ishdan chiqqan")
```

## API Usage

### Staff DELETE Endpoint

```http
DELETE /api/v1/branches/staff/{id}/
```

**Response:** `204 No Content`

Bu endpoint avtomatik `soft_delete()` ishlatadi:
1. `deleted_at` o'rnatadi
2. Xodimlar uchun `termination_date` o'rnatadi
3. Audit trail yangilanadi

### Best Practices

1. **Har doim soft delete ishlating:**
   ```python
   # ✅ TO'G'RI
   staff.delete()  # yoki staff.soft_delete()
   
   # ❌ NOTO'G'RI (faqat zarurat bo'lganda)
   staff.delete(hard=True)
   ```

2. **Faol obyektlarni filter qiling:**
   ```python
   # ✅ TO'G'RI
   staff = BranchMembership.objects.active().filter(role='teacher')
   
   # ❌ NOTO'G'RI (o'chirilganlarni ham oladi)
   staff = BranchMembership.objects.filter(role='teacher')
   ```

3. **Audit trail qo'llab-quvvatlang:**
   ```python
   # ✅ TO'G'RI
   staff.soft_delete(user=request.user)
   
   # ⚠️ Yaxshi, lekin audit yo'q
   staff.soft_delete()
   ```

## Migration

Soft delete allaqachon barcha modellarda mavjud (`BaseModel` orqali):
- ✅ `deleted_at` field
- ✅ `created_by`, `updated_by` fields
- ✅ Indexes
- ✅ Metodlar

## Testing

```python
from apps.branch.models import BranchMembership

# Create test staff
staff = BranchMembership.objects.create(...)

# Test soft delete
staff.soft_delete()
assert staff.deleted_at is not None
assert staff.termination_date is not None  # if staff

# Test restore
staff.restore()
assert staff.deleted_at is None
assert staff.termination_date is None  # if staff

# Test queries
active = BranchMembership.objects.active().count()
deleted = BranchMembership.objects.deleted().count()
```

## Xulosa

✅ Professional soft delete tizimi to'liq joriy qilindi:
- BaseModel da universal metodlar
- BranchMembership da custom logic (termination_date)
- Manager metodlari (active(), deleted())
- Properties (is_active, is_deleted)
- Audit trail qo'llab-quvvati
- API integratsiyasi

**Versiya:** 1.0  
**Sana:** 2024-12-20  
**Holat:** Production Ready
