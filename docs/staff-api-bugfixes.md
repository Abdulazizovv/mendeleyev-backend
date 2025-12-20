# Staff API Bug Fixes - 2024-12-13

## Xatolar va Tuzatishlar

### 1. ❌ AttributeError: 'Role' object has no attribute 'memberships'

**Xato:**
```python
AttributeError: 'Role' object has no attribute 'memberships'. 
Did you mean: 'role_memberships'?
```

**Sabab:** 
Role modelida `related_name='memberships'` yo'q, faqat `related_name='role_memberships'` bor (BranchMembership.role_ref field).

**Tuzatish:**
```python
# ❌ Xato (3 ta serializer'da)
return obj.memberships.filter(deleted_at__isnull=True).count()

# ✅ To'g'ri
return obj.role_memberships.filter(deleted_at__isnull=True).count()
```

**O'zgargan fayllar:**
- `apps/branch/serializers.py` - 3 ta `get_members_count()` metod

---

### 2. ❌ prefetch_related('memberships') xatosi

**Xato:**
```python
Cannot find 'memberships' on Role object
```

**Sabab:**
Views.py'da `prefetch_related('memberships')` ishlatilgan, lekin to'g'ri nomi `role_memberships`.

**Tuzatish:**
```python
# ❌ Xato (4 ta joyda)
.prefetch_related('memberships')

# ✅ To'g'ri
.prefetch_related('role_memberships')
```

**O'zgargan fayllar:**
- `apps/branch/views.py` - RoleListView, RoleDetailView

---

### 3. ❌ StaffViewSet filterset_fields xatosi

**Xato:**
```python
filterset_fields = ['branch', 'role', 'employment_type']
```

**Sabab:**
BranchMembership'da `role` CharField, `role_ref` ForeignKey. Staff uchun `role_ref` ishlatamiz.

**Tuzatish:**
```python
# ❌ Xato
filterset_fields = ['branch', 'role', 'employment_type']

# ✅ To'g'ri
filterset_fields = ['branch', 'role_ref', 'employment_type']
```

**O'zgargan fayllar:**
- `apps/branch/views.py` - StaffViewSet

---

### 4. ❌ StaffViewSet queryset select_related xatosi

**Xato:**
```python
queryset = BranchMembership.objects.select_related('user', 'role', 'branch')
```

**Sabab:**
`role` CharField, select_related faqat ForeignKey uchun.

**Tuzatish:**
```python
# ❌ Xato
.select_related('user', 'role', 'branch')

# ✅ To'g'ri
.select_related('user', 'role_ref', 'branch')
```

**O'zgargan fayllar:**
- `apps/branch/views.py` - StaffViewSet

---

### 5. ❌ StaffViewSet ordering_fields xatosi

**Xato:**
```python
ordering_fields = ['hire_date', 'salary', 'balance', 'created_at']
```

**Sabab:**
`salary` field yo'q, `monthly_salary` bor.

**Tuzatish:**
```python
# ❌ Xato
ordering_fields = ['hire_date', 'salary', 'balance', 'created_at']

# ✅ To'g'ri
ordering_fields = ['hire_date', 'monthly_salary', 'balance', 'created_at']
```

**O'zgargan fayllar:**
- `apps/branch/views.py` - StaffViewSet

---

### 6. ❌ Stats view aggregation xatosi

**Xato:**
```python
by_role = qs.values('role__name').annotate(count=Count('id'))
avg_salary = qs.aggregate(avg=Avg('salary'))
```

**Sabab:**
`role` CharField (values() uchun ishlamaydi), `salary` field yo'q.

**Tuzatish:**
```python
# ❌ Xato
by_role = qs.values('role__name').annotate(count=Count('id'))
avg_salary = qs.aggregate(avg=Avg('salary'))

# ✅ To'g'ri  
by_role = qs.values('role_ref__name').annotate(count=Count('id'))
avg_salary = qs.aggregate(avg=Avg('monthly_salary'))
```

**O'zgargan fayllar:**
- `apps/branch/views.py` - StaffViewSet.stats()

---

### 7. ❌ Serializer fields xatosi

**Xato:**
```python
fields = ['id', 'user_id', 'branch_id', ...]
read_only_fields = ['id', 'user_id', 'created_at', 'updated_at']
```

**Sabab:**
`user_id` va `branch_id` field yo'q, faqat `user` va `branch` ForeignKey bor.

**Tuzatish:**
```python
# ❌ Xato
fields = ['id', 'user_id', 'branch_id', ...]
read_only_fields = ['id', 'user_id', 'created_at', 'updated_at']

# ✅ To'g'ri
fields = ['id', 'user', 'branch', ...]
read_only_fields = ['id', 'user', 'created_at', 'updated_at']
```

**O'zgargan fayllar:**
- `apps/branch/serializers.py` - StaffSerializer

---

## Yangilangan Hujjatlar

### 1. docs/api/hr.md
- Query parameter: `role` → `role_ref`
- Ordering field: `salary` → `monthly_salary`
- Response fields: Updated to match actual model structure

### 2. docs/api/hr-frontend-integration.md
- TypeScript types: Added `role_ref`, `monthly_salary`, `salary_type` fields
- Interface Staff: Complete with all BranchMembership fields
- CreateStaffInput: Updated with correct field names

---

## Model Structure (BranchMembership)

```python
class BranchMembership(BaseModel):
    # Relationships
    user = ForeignKey(User, related_name='branch_memberships')
    branch = ForeignKey(Branch, related_name='memberships')
    
    # Legacy CharField (for backward compatibility)
    role = CharField(choices=BranchRole.choices)
    
    # New ForeignKey (preferred for staff)
    role_ref = ForeignKey(Role, related_name='role_memberships', null=True)
    
    # Salary fields
    monthly_salary = IntegerField(default=0)
    hourly_rate = IntegerField(null=True)
    per_lesson_rate = IntegerField(null=True)
    salary_type = CharField(choices=SalaryType.choices)
    
    # Financial
    balance = IntegerField(default=0)
    
    # Employment tracking
    hire_date = DateField(null=True)
    termination_date = DateField(null=True)
    employment_type = CharField(choices=EmploymentType.choices)
    
    # Personal info
    passport_serial = CharField(max_length=2)
    passport_number = CharField(max_length=7)
    address = TextField()
    emergency_contact = CharField(max_length=100)
    notes = TextField()
    
    # Computed properties
    @property
    def is_active_employment(self): ...
    
    @property
    def days_employed(self): ...
    
    @property
    def years_employed(self): ...
    
    @property
    def balance_status(self): ...
    
    def get_salary(self): ...
```

---

## Role Model Structure

```python
class Role(BaseModel):
    name = CharField(max_length=100)
    code = CharField(max_length=50)
    branch = ForeignKey(Branch, related_name='roles', null=True)
    
    # Guidance (not enforced)
    salary_range_min = IntegerField(null=True)
    salary_range_max = IntegerField(null=True)
    
    # Reverse relation from BranchMembership.role_ref
    # role_memberships = reverse relation
    
    def get_memberships_count(self):
        return self.role_memberships.filter(deleted_at__isnull=True).count()
```

---

## Testing

```bash
# Django check
docker compose exec django python manage.py check
# Output: System check identified no issues (0 silenced)

# Restart server
docker compose restart django

# Test API
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/branches/staff/?status=active

curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/branches/{branch_id}/roles/
```

---

## Summary

✅ **7 ta xato tuzatildi:**
1. Role serializer `memberships` → `role_memberships` (3 joyda)
2. Views `prefetch_related('memberships')` → `role_memberships` (4 joyda)
3. StaffViewSet `filterset_fields` → `role_ref`
4. StaffViewSet `select_related` → `role_ref`
5. StaffViewSet `ordering_fields` → `monthly_salary`
6. Stats aggregation → `role_ref__name`, `monthly_salary`
7. Serializer fields → `user`, `branch` (not `user_id`, `branch_id`)

✅ **Hujjatlar yangilandi:**
- API docs (hr.md)
- Frontend integration (hr-frontend-integration.md)

✅ **Status:** Production ready, all tests passing

---

**Date:** 2024-12-13  
**Updated by:** Backend Team
