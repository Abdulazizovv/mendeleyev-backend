# Modellar Arxitekturasi va Tavsiyalar

Bu hujjat loyihadagi barcha modellarni tushuntirish va ularni qanday tashkil qilish haqida tavsiyalar beradi.

## 📊 Modellar Strukturasi

### 1. **Asosiy Modellar (Core Models)**

#### `User` (auth/users/models.py)
- **Maqsad**: Barcha foydalanuvchilar uchun asosiy model
- **Asosiy fieldlar**: 
  - `phone_number` (unique, USERNAME_FIELD)
  - `first_name`, `last_name`, `email`
  - `phone_verified`, `is_active`, `is_staff`, `is_superuser`
- **Munosabatlar**:
  - `branches` (ManyToMany through BranchMembership)
  - `profile` (OneToOne to Profile)

#### `Branch` (apps/branch/models.py)
- **Maqsad**: Filiallar (maktablar va o'quv markazlari)
- **Asosiy fieldlar**:
  - `name`, `slug` (unique)
  - `type` (SCHOOL | CENTER)
  - `status` (PENDING | ACTIVE | INACTIVE | ARCHIVED)
- **Munosabatlar**:
  - `users` (ManyToMany through BranchMembership)
  - `memberships` (ForeignKey from BranchMembership)

#### `BranchMembership` (apps/branch/models.py)
- **Maqsad**: User va Branch o'rtasidagi bog'lanish + Role
- **Asosiy fieldlar**:
  - `user` (ForeignKey to User)
  - `branch` (ForeignKey to Branch)
  - `role` (CharField: super_admin, branch_admin, teacher, student, parent)
  - `role_ref` (ForeignKey to Role - optional)
- **Munosabatlar**:
  - `student_profile` (OneToOne to StudentProfile)
  - `teacher_profile` (OneToOne to TeacherProfile)
  - `parent_profile` (OneToOne to ParentProfile)
  - `admin_profile` (OneToOne to AdminProfile)
  - `generic_profile` (OneToOne to UserBranchProfile)

---

### 2. **Profil Modellari (Profile Models)**

#### `Profile` (auth/profiles/models.py)
- **Maqsad**: User uchun global profil (barcha filiallar uchun umumiy)
- **Munosabat**: `user` (OneToOne)
- **Fieldlar**: avatar, date_of_birth, gender, language, timezone, bio, address, socials

#### `UserBranchProfile` (auth/profiles/models.py)
- **Maqsad**: Backward compatibility uchun umumiy rolga xos profil
- **Munosabat**: `user_branch` (OneToOne to BranchMembership)
- **Fieldlar**: display_name, title, about, contacts

#### `StudentProfile` (auth/profiles/models.py)
- **Maqsad**: O'quvchi uchun to'liq profil
- **Munosabat**: `user_branch` (OneToOne to BranchMembership)
- **Asosiy fieldlar**:
  - `personal_number` (unique, auto-generated: {BRANCH_CODE}-{ACADEMIC_YEAR_SHORT}-{ORDER})
  - `middle_name`, `gender`, `date_of_birth`, `address`
  - `birth_certificate`, `additional_fields` (JSON)
- **Munosabatlar**:
  - `relatives` (ForeignKey from StudentRelative)

#### `TeacherProfile` (auth/profiles/models.py)
- **Maqsad**: O'qituvchi uchun profil
- **Munosabat**: `user_branch` (OneToOne to BranchMembership)
- **Fieldlar**: subject, experience_years, bio

#### `ParentProfile` (auth/profiles/models.py)
- **Maqsad**: Ota-ona uchun profil
- **Munosabat**: `user_branch` (OneToOne to BranchMembership)
- **Fieldlar**: notes, related_students (ManyToMany)

#### `AdminProfile` (auth/profiles/models.py)
- **Maqsad**: Admin uchun profil
- **Munosabat**: `user_branch` (OneToOne to BranchMembership)
- **Fieldlar**: is_super_admin, managed_branches, title, notes

#### `StudentRelative` (auth/profiles/models.py)
- **Maqsad**: O'quvchi yaqinlari
- **Munosabat**: `student_profile` (ForeignKey to StudentProfile)
- **Fieldlar**: relationship_type, first_name, middle_name, last_name, phone_number, email, gender, date_of_birth, address, workplace, position, passport_number, photo, is_primary_contact, is_guardian, additional_info, notes

---

### 3. **Maktab Modellari (School Models)**

#### `AcademicYear` (apps/school/academic/models.py)
- **Maqsad**: Akademik yillar
- **Fieldlar**: name, start_date, end_date, is_current

#### `Quarter` (apps/school/academic/models.py)
- **Maqsad**: Choraklar
- **Munosabat**: `academic_year` (ForeignKey)
- **Fieldlar**: name, start_date, end_date, is_current

#### `Class` (apps/school/classes/models.py)
- **Maqsad**: Sinflar
- **Munosabatlar**:
  - `branch` (ForeignKey to Branch)
  - `academic_year` (ForeignKey to AcademicYear)
  - `class_teacher` (ForeignKey to BranchMembership, role=teacher)
  - `room` (ForeignKey to Room)
- **Fieldlar**: name, grade_level, section, max_students, is_active

#### `ClassStudent` (apps/school/classes/models.py)
- **Maqsad**: O'quvchini sinfga biriktirish
- **Munosabatlar**:
  - `class_obj` (ForeignKey to Class)
  - `membership` (ForeignKey to BranchMembership, role=student)
- **Fieldlar**: enrollment_date, is_active, notes

#### `Subject` (apps/school/subjects/models.py)
- **Maqsad**: Fanlar
- **Munosabat**: `branch` (ForeignKey to Branch)
- **Fieldlar**: name, code, description, is_active

#### `ClassSubject` (apps/school/subjects/models.py)
- **Maqsad**: Sinfga fan biriktirish
- **Munosabatlar**:
  - `class_obj` (ForeignKey to Class)
  - `subject` (ForeignKey to Subject)
  - `teacher` (ForeignKey to BranchMembership, role=teacher)
  - `quarter` (ForeignKey to Quarter)
- **Fieldlar**: hours_per_week, is_active

#### `Building` (apps/school/rooms/models.py)
- **Maqsad**: Binolar
- **Munosabat**: `branch` (ForeignKey to Branch)
- **Fieldlar**: name, address, description

#### `Room` (apps/school/rooms/models.py)
- **Maqsad**: Xonalar
- **Munosabat**: `building` (ForeignKey to Building)
- **Fieldlar**: name, capacity, room_type, description

#### `CashRegister` (apps/school/finance/models.py)
- **Maqsad**: Kassalar (har bir filial uchun bir nechta)
- **Munosabat**: `branch` (ForeignKey to Branch)
- **Fieldlar**: name, description, balance (BigIntegerField, so'm), is_active, location

#### `Transaction` (apps/school/finance/models.py)
- **Maqsad**: Barcha moliyaviy operatsiyalar
- **Munosabatlar**:
  - `branch` (ForeignKey to Branch)
  - `cash_register` (ForeignKey to CashRegister)
  - `student_profile` (ForeignKey to StudentProfile, optional)
  - `employee_membership` (ForeignKey to BranchMembership, optional)
- **Fieldlar**: transaction_type, status, amount (BigIntegerField, so'm), payment_method, description, reference_number, transaction_date, metadata

#### `StudentBalance` (apps/school/finance/models.py)
- **Maqsad**: O'quvchi balanslari
- **Munosabat**: `student_profile` (OneToOne to StudentProfile)
- **Fieldlar**: balance (BigIntegerField, so'm), notes

#### `SubscriptionPlan` (apps/school/finance/models.py)
- **Maqsad**: Abonement tariflari (sinf darajasi bo'yicha)
- **Munosabat**: `branch` (ForeignKey to Branch, optional - umumiy tariflar uchun)
- **Fieldlar**: name, description, grade_level_min, grade_level_max, period, price (BigIntegerField, so'm), is_active

#### `Discount` (apps/school/finance/models.py)
- **Maqsad**: Chegirmalar (foiz yoki aniq summa)
- **Munosabat**: `branch` (ForeignKey to Branch, optional - umumiy chegirmalar uchun)
- **Fieldlar**: name, discount_type, amount (BigIntegerField, foiz yoki summa), is_active, valid_from, valid_until, description, conditions (JSON)

#### `Payment` (apps/school/finance/models.py)
- **Maqsad**: O'quvchi to'lovlari
- **Munosabatlar**:
  - `student_profile` (ForeignKey to StudentProfile)
  - `branch` (ForeignKey to Branch)
  - `subscription_plan` (ForeignKey to SubscriptionPlan, optional)
  - `discount` (ForeignKey to Discount, optional)
  - `transaction` (OneToOne to Transaction)
- **Fieldlar**: base_amount, discount_amount, final_amount (BigIntegerField, so'm), payment_method, period, payment_date, period_start, period_end, notes

---

## 🔗 Modellar O'rtasidagi Munosabatlar

```
User
  ├── Profile (OneToOne) - Global profil
  └── BranchMembership (ManyToMany through)
      ├── Branch
      ├── Role (optional)
      └── Role-specific Profiles:
          ├── StudentProfile (OneToOne)
          │   └── StudentRelative (ForeignKey, many)
          ├── TeacherProfile (OneToOne)
          ├── ParentProfile (OneToOne)
          └── AdminProfile (OneToOne)

Branch
  ├── BranchMembership (ForeignKey, many)
  ├── Class (ForeignKey, many)
  ├── Subject (ForeignKey, many)
  ├── Building (ForeignKey, many)
  ├── CashRegister (ForeignKey, many)
  ├── Transaction (ForeignKey, many)
  ├── SubscriptionPlan (ForeignKey, many, optional - umumiy tariflar uchun null)
  └── Discount (ForeignKey, many, optional - umumiy chegirmalar uchun null)

Class
  ├── AcademicYear (ForeignKey)
  ├── BranchMembership (class_teacher, ForeignKey)
  ├── Room (ForeignKey)
  ├── ClassStudent (ForeignKey, many)
  └── ClassSubject (ForeignKey, many)

ClassStudent
  ├── Class (ForeignKey)
  └── BranchMembership (membership, ForeignKey, role=student)

ClassSubject
  ├── Class (ForeignKey)
  ├── Subject (ForeignKey)
  ├── BranchMembership (teacher, ForeignKey, role=teacher)
  └── Quarter (ForeignKey)

StudentProfile
  ├── StudentBalance (OneToOne)
  ├── Transaction (ForeignKey, many)
  └── Payment (ForeignKey, many)

CashRegister
  └── Transaction (ForeignKey, many)

Transaction
  ├── CashRegister (ForeignKey)
  ├── StudentProfile (ForeignKey, optional)
  ├── BranchMembership (employee_membership, ForeignKey, optional)
  └── Payment (OneToOne, optional)

Payment
  ├── StudentProfile (ForeignKey)
  ├── Branch (ForeignKey)
  ├── SubscriptionPlan (ForeignKey, optional)
  ├── Discount (ForeignKey, optional)
  └── Transaction (OneToOne)
```

---

## ✅ Best Practices va Tavsiyalar

### 1. **Modellar Tashkiloti**

✅ **Yaxshi**:
- Har bir app o'z modellarini o'z `models.py` faylida saqlaydi
- BaseModel dan meros olish (UUID, timestamps, soft delete)
- Related_name lar aniq va tushunarli

❌ **Yomon**:
- Barcha modellarni bir faylda saqlash
- Circular import muammolari
- Related_name larni o'zgartirish

### 2. **Field Naming**

✅ **Yaxshi**:
- `user_branch` - BranchMembership ga havola
- `class_obj` - Class ga havola (class Python keyword)
- `personal_number` - aniq va tushunarli

❌ **Yomon**:
- `userBranch` (camelCase)
- `class` (Python keyword)
- `num` (qisqartirilgan)

### 3. **Relationships**

✅ **Yaxshi**:
- OneToOne: Profile, StudentProfile, TeacherProfile
- ForeignKey: Class -> Branch, ClassStudent -> Class
- ManyToMany through: User -> Branch (through BranchMembership)

❌ **Yomon**:
- Ortiqcha ManyToMany (keraksiz)
- Circular dependencies
- Related_name larni o'zgartirish

### 4. **Indexes va Performance**

✅ **Yaxshi**:
- `db_index=True` - tez-tez qidiriladigan fieldlar uchun
- `unique=True` - unique constraint uchun
- `select_related()` va `prefetch_related()` ishlatish

❌ **Yomon**:
- Barcha fieldlarni index qilish
- N+1 query muammolari

### 5. **Soft Delete**

✅ **Yaxshi**:
- Barcha modellar BaseModel dan meros oladi
- `deleted_at` orqali soft delete
- `objects.active()` va `objects.deleted()` metodlari

❌ **Yomon**:
- Hard delete (ma'lumotlar yo'qoladi)
- Soft delete ni unutish

---

## 🎯 Kod Tashkiloti Tavsiyalari

### 1. **Modellar Tartibi**

Har bir model faylida quyidagi tartibni saqlang:

```python
# 1. Imports
from django.db import models
from apps.common.models import BaseModel

# 2. Choices (agar mavjud bo'lsa)
class Gender(models.TextChoices):
    ...

# 3. Managers (agar mavjud bo'lsa)
class CustomManager(models.Manager):
    ...

# 4. Models
class MyModel(BaseModel):
    # 4.1. ForeignKey/OneToOne fields
    # 4.2. CharField/TextField fields
    # 4.3. IntegerField/BooleanField fields
    # 4.4. DateTimeField/DateField fields
    # 4.5. JSONField/FileField fields
    
    class Meta:
        ...
    
    def __str__(self):
        ...
    
    # Properties va methods
```

### 2. **Field Gruppalash**

Fieldlarni mantiqiy guruhlarga ajrating:

```python
class StudentProfile(BaseModel):
    # 1. Relationships
    user_branch = models.OneToOneField(...)
    
    # 2. Identifiers
    personal_number = models.CharField(...)
    
    # 3. Personal info
    middle_name = models.CharField(...)
    gender = models.CharField(...)
    date_of_birth = models.DateField(...)
    
    # 4. Contact info
    address = models.TextField(...)
    
    # 5. Documents
    birth_certificate = models.FileField(...)
    
    # 6. Additional
    additional_fields = models.JSONField(...)
```

### 3. **Docstrings**

Har bir model uchun docstring yozing:

```python
class StudentProfile(BaseModel):
    """Maktab o'quvchilari uchun to'liq profil.
    
    Maktab o'quvchilarining barcha ma'lumotlari shu modelda saqlanadi.
    Shaxsiy raqam avtomatik generatsiya qilinadi ({BRANCH_CODE}-{ACADEMIC_YEAR_SHORT}-{ORDER}).
    """
```

### 4. **Meta Class**

Meta class da quyidagilarni belgilang:

```python
class Meta:
    verbose_name = 'O\'quvchi profili'
    verbose_name_plural = 'O\'quvchi profillari'
    ordering = ['-created_at']
    indexes = [
        models.Index(fields=['personal_number']),
        models.Index(fields=['date_of_birth']),
    ]
    unique_together = [('field1', 'field2')]  # agar kerak bo'lsa
```

---

## 🔍 Qidirish va Filtering

### 1. **Search Fields**

Admin panelda qidirish uchun:

```python
search_fields = (
    'personal_number',
    'user_branch__user__first_name',
    'user_branch__user__last_name',
    'user_branch__user__phone_number',
)
```

### 2. **Query Optimization**

```python
# Yaxshi
queryset = StudentProfile.objects.select_related(
    'user_branch',
    'user_branch__user',
    'user_branch__branch'
).prefetch_related('relatives')

# Yomon
queryset = StudentProfile.objects.all()  # N+1 query muammosi
```

---

## 📝 Xulosa

### Asosiy Qoidalar:

1. ✅ **BaseModel dan meros oling** - UUID, timestamps, soft delete
2. ✅ **Related_name larni aniq belgilang** - `student_profile`, `teacher_profile`
3. ✅ **Indexes qo'shing** - tez-tez qidiriladigan fieldlar uchun
4. ✅ **Docstrings yozing** - har bir model uchun
5. ✅ **Fieldlarni guruhlang** - mantiqiy tartibda
6. ✅ **Query optimization** - `select_related()` va `prefetch_related()`
7. ✅ **Soft delete ishlating** - ma'lumotlarni saqlash uchun

### Muammolarni Hal Qilish:

1. **Circular import**: `'app.Model'` string formatida ishlating
2. **N+1 queries**: `select_related()` va `prefetch_related()` ishlating
3. **Field naming**: Python keyword lardan qoching (`class` -> `class_obj`)
4. **Relationships**: OneToOne, ForeignKey, ManyToMany ni to'g'ri tanlang

---

## 🔄 Circular Import Muammolari

Circular import muammolarini hal qilish uchun quyidagi qoidalarga rioya qiling:

1. **Model Fieldlarda**: Har doim string reference ishlating (`'branch.BranchMembership'`)
2. **Signals da**: String reference + lazy import
3. **Admin da**: Factory function ishlating
4. **Views/Serializers da**: Function ichida import qiling

Batafsil ma'lumot: [Circular Imports Fix](circular-imports-fix.md)

## 🔔 Signallar (Auto-Creation)

Quyidagi modellar avtomatik yaratiladi:

1. **Profile** - `User` yaratilganda (`auth.profiles.signals.create_user_profile`)
2. **BranchSettings** - `Branch` yaratilganda (`apps.branch.signals.create_branch_settings`)
3. **Role Profiles** - `BranchMembership` yaratilganda (`auth.profiles.signals.create_role_profiles`)
   - `UserBranchProfile` (har doim)
   - `StudentProfile` (role=student)
   - `TeacherProfile` (role=teacher)
   - `ParentProfile` (role=parent)
   - `AdminProfile` (role=branch_admin yoki super_admin)
4. **StudentBalance** - `StudentProfile` yaratilganda (`apps.school.finance.signals.create_student_balance`)

Barcha signallar `apps.py` da `ready()` metodida import qilinadi.

## 📚 Qo'shimcha Ma'lumotlar

- [Django Models Documentation](https://docs.djangoproject.com/en/stable/topics/db/models/)
- [Django Relationships](https://docs.djangoproject.com/en/stable/topics/db/models/#relationships)
- [Query Optimization](https://docs.djangoproject.com/en/stable/topics/db/optimization/)
- [Circular Imports Fix](circular-imports-fix.md)

