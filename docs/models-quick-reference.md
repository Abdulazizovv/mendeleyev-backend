# Modellar Tezkor Qo'llanmasi

## 🎯 Asosiy Modellar

### 1. User (auth/users/models.py)
```python
User
├── phone_number (unique, USERNAME_FIELD)
├── first_name, last_name, email
├── phone_verified, is_active
└── branches (ManyToMany through BranchMembership)
```

### 2. Branch (apps/branch/models.py)
```python
Branch
├── name, slug (unique)
├── type (SCHOOL | CENTER)
├── status (PENDING | ACTIVE | INACTIVE | ARCHIVED)
└── memberships (ForeignKey from BranchMembership)
```

### 3. BranchMembership (apps/branch/models.py)
```python
BranchMembership
├── user (ForeignKey to User)
├── branch (ForeignKey to Branch)
├── role (super_admin | branch_admin | teacher | student | parent)
├── role_ref (ForeignKey to Role, optional)
└── Profiles:
    ├── student_profile (OneToOne)
    ├── teacher_profile (OneToOne)
    ├── parent_profile (OneToOne)
    └── admin_profile (OneToOne)
```

---

## 📚 Profil Modellari

### StudentProfile (auth/profiles/models.py)
```python
StudentProfile
├── user_branch (OneToOne to BranchMembership)
├── personal_number (unique, auto: ST-YYYY-NNNN)
├── middle_name, gender, date_of_birth
├── address, birth_certificate
├── additional_fields (JSON)
└── relatives (ForeignKey from StudentRelative)
```

### TeacherProfile (auth/profiles/models.py)
```python
TeacherProfile
├── user_branch (OneToOne to BranchMembership)
├── subject, experience_years
└── bio
```

### StudentRelative (auth/profiles/models.py)
```python
StudentRelative
├── student_profile (ForeignKey to StudentProfile)
├── relationship_type (father | mother | brother | ...)
├── first_name, middle_name, last_name
├── phone_number, email
├── workplace, position
├── is_primary_contact, is_guardian
└── additional_info (JSON)
```

---

## 🏫 Maktab Modellari

### Class (apps/school/classes/models.py)
```python
Class
├── branch (ForeignKey)
├── academic_year (ForeignKey)
├── name, grade_level, section
├── class_teacher (ForeignKey to BranchMembership, role=teacher)
├── room (ForeignKey to Room)
├── max_students, is_active
└── class_students (ForeignKey from ClassStudent)
```

### ClassStudent (apps/school/classes/models.py)
```python
ClassStudent
├── class_obj (ForeignKey to Class)
├── membership (ForeignKey to BranchMembership, role=student)
├── enrollment_date, is_active
└── notes
```

### Subject (apps/school/subjects/models.py)
```python
Subject
├── branch (ForeignKey)
├── name, code (unique per branch)
└── is_active
```

### ClassSubject (apps/school/subjects/models.py)
```python
ClassSubject
├── class_obj (ForeignKey to Class)
├── subject (ForeignKey to Subject)
├── teacher (ForeignKey to BranchMembership, role=teacher)
├── quarter (ForeignKey to Quarter)
├── hours_per_week
└── is_active
```

---

## 🔗 Asosiy Munosabatlar

### User → BranchMembership → Profiles
```
User (1) 
  └── BranchMembership (N)
      ├── StudentProfile (1) ──→ StudentRelative (N)
      ├── TeacherProfile (1)
      ├── ParentProfile (1)
      └── AdminProfile (1)
```

### Branch → School Entities
```
Branch (1)
  ├── Class (N)
  │   ├── ClassStudent (N) ──→ BranchMembership (1)
  │   └── ClassSubject (N) ──→ Subject (1)
  ├── Subject (N)
  ├── Building (N) ──→ Room (N)
  └── AcademicYear (N) ──→ Quarter (N)
```

---

## ⚡ Tezkor Qidiruv

### O'quvchi topish
```python
# Shaxsiy raqam bo'yicha
StudentProfile.objects.get(personal_number='ST-2024-0001')

# Telefon bo'yicha
StudentProfile.objects.filter(
    user_branch__user__phone_number='+998901234567'
)

# Ism bo'yicha
StudentProfile.objects.filter(
    user_branch__user__first_name__icontains='Ali'
)
```

### O'qituvchi sinflari
```python
# O'qituvchi sinflari
Class.objects.filter(class_teacher=teacher_membership)

# O'qituvchi fanlari
ClassSubject.objects.filter(teacher=teacher_membership)
```

### Sinf o'quvchilari
```python
# Sinf o'quvchilari
ClassStudent.objects.filter(
    class_obj=class_obj,
    is_active=True,
    deleted_at__isnull=True
)
```

---

## 🎨 Best Practices

### 1. Query Optimization
```python
# ✅ Yaxshi
StudentProfile.objects.select_related(
    'user_branch',
    'user_branch__user',
    'user_branch__branch'
).prefetch_related('relatives')

# ❌ Yomon
StudentProfile.objects.all()  # N+1 query
```

### 2. Soft Delete
```python
# ✅ Faol o'quvchilar
StudentProfile.objects.active()

# ✅ O'chirilgan o'quvchilar
StudentProfile.objects.deleted()

# ✅ Barcha (faol + o'chirilgan)
StudentProfile.objects.all()
```

### 3. Field Naming
```python
# ✅ Yaxshi
user_branch  # BranchMembership ga havola
class_obj    # Class ga havola (class keyword)
personal_number  # Aniq va tushunarli

# ❌ Yomon
userBranch   # camelCase
class        # Python keyword
num          # Qisqartirilgan
```

---

## 📝 Field Types

### Identifiers
- `id`: UUID (primary key)
- `personal_number`: CharField (unique, indexed)
- `phone_number`: CharField (unique, indexed)

### Relationships
- `OneToOne`: Profile, StudentProfile, TeacherProfile
- `ForeignKey`: Class → Branch, ClassStudent → Class
- `ManyToMany through`: User → Branch (through BranchMembership)

### Data Types
- `CharField`: name, code, title
- `TextField`: address, bio, notes
- `DateField`: date_of_birth, enrollment_date
- `JSONField`: additional_fields, additional_info
- `FileField`: birth_certificate, photo
- `BooleanField`: is_active, is_primary_contact

---

## 🔍 Indexes

### Asosiy Indexes
- `User.phone_number` - db_index
- `StudentProfile.personal_number` - db_index
- `Branch.slug` - unique
- `Branch.status`, `Branch.type` - indexes
- `Class.grade_level`, `Class.is_active` - indexes

### Composite Indexes
- `(user, branch)` - unique_together (BranchMembership)
- `(class_obj, membership)` - unique_together (ClassStudent)
- `(class_obj, subject)` - unique_together (ClassSubject)

---

## 🚀 Performance Tips

1. **select_related()** - ForeignKey va OneToOne uchun
2. **prefetch_related()** - ManyToMany va reverse ForeignKey uchun
3. **only()** va **defer()** - faqat kerakli fieldlarni olish
4. **Indexes** - tez-tez qidiriladigan fieldlar uchun
5. **Pagination** - katta ro'yxatlar uchun

---

## 📖 Qo'shimcha Ma'lumotlar

- [Batafsil Arxitektura](models-architecture.md)
- [Visual Diagramma](models-diagram.md)
- [Django Models Docs](https://docs.djangoproject.com/en/stable/topics/db/models/)

