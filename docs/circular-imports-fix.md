# Circular Import Muammolari va Yechimlar

## 🔍 Muammo

`auth/profiles/models.py` da `BranchMembership` ga havola berilgan, lekin `apps/branch/__init__.py` da lazy import qilingan. Bu test va runtime'da muammolarga olib kelishi mumkin.

## ✅ Yechimlar

### 1. **String References (Model Fieldlarda)**

✅ **Yaxshi** - String formatida ishlatish:
```python
# auth/profiles/models.py
user_branch = models.OneToOneField(
    'branch.BranchMembership',  # String reference
    on_delete=models.CASCADE,
    related_name='student_profile',
)
```

❌ **Yomon** - To'g'ridan-to'g'ri import:
```python
from apps.branch.models import BranchMembership  # Circular import!

user_branch = models.OneToOneField(
    BranchMembership,  # Direct reference
    on_delete=models.CASCADE,
)
```

### 2. **Lazy Import (Signals da)**

✅ **Yaxshi** - String reference + lazy import:
```python
# auth/profiles/signals.py
@receiver(post_save, sender='branch.BranchMembership')  # String reference
def create_role_profiles(sender, instance, created, **kwargs):
    # Lazy import inside function
    from apps.branch.models import BranchRole
    
    # ... rest of code
```

❌ **Yomon** - Top-level import:
```python
from apps.branch.models import BranchMembership, BranchRole  # Circular import!

@receiver(post_save, sender=BranchMembership)
def create_role_profiles(...):
    ...
```

### 3. **Factory Function (Admin Inline da)**

✅ **Yaxshi** - Factory function:
```python
# apps/branch/admin.py
def get_admin_profile_inline():
    """Factory function to create AdminProfileInline with lazy import."""
    from auth.profiles.models import AdminProfile  # Lazy import
    
    class AdminProfileInline(admin.StackedInline):
        model = AdminProfile
        # ... rest of config
    
    return AdminProfileInline

AdminProfileInline = get_admin_profile_inline()
```

❌ **Yomon** - Top-level import:
```python
from auth.profiles.models import AdminProfile  # Circular import!

class AdminProfileInline(admin.StackedInline):
    model = AdminProfile
```

### 4. **Lazy Import (View va Serializer da)**

✅ **Yaxshi** - Function ichida import:
```python
# apps/branch/views.py
def some_view(self, request):
    # Lazy import inside method
    from auth.profiles.models import AdminProfile
    
    ap = AdminProfile.objects.get(...)
```

❌ **Yomon** - Top-level import:
```python
from auth.profiles.models import AdminProfile  # Circular import!

def some_view(self, request):
    ap = AdminProfile.objects.get(...)
```

---

## 📋 Qoidalar

### 1. **Model Fieldlarda**
- ✅ **Har doim string reference ishlating**: `'branch.BranchMembership'`
- ❌ **To'g'ridan-to'g'ri import qilmang**

### 2. **Signals da**
- ✅ **String reference + lazy import**: `sender='branch.BranchMembership'`
- ✅ **Function ichida import**: `from apps.branch.models import BranchRole`
- ❌ **Top-level import qilmang**

### 3. **Admin da**
- ✅ **Factory function ishlating**
- ✅ **Lazy import ishlating**
- ❌ **Top-level import qilmang**

### 4. **Views va Serializers da**
- ✅ **Function/method ichida import qiling**
- ✅ **Kerak bo'lganda import qiling**
- ❌ **Top-level import qilmang** (agar circular import bo'lsa)

---

## 🔧 Tuzatilgan Fayllar

### 1. `auth/profiles/signals.py`
- ✅ `sender='branch.BranchMembership'` (string reference)
- ✅ `from apps.branch.models import BranchRole` (lazy import)

### 2. `apps/branch/admin.py`
- ✅ Factory function: `get_admin_profile_inline()`
- ✅ Lazy import: `from auth.profiles.models import AdminProfile`

### 3. `auth/profiles/models.py`
- ✅ Barcha fieldlar string reference ishlatadi: `'branch.BranchMembership'`
- ✅ `current_class` metodida lazy import: `from apps.school.classes.models import ClassStudent`

---

## 🧪 Test

```python
# Test circular import
from auth.profiles.models import StudentProfile, AdminProfile
from apps.branch.models import BranchMembership
from apps.branch.admin import AdminProfileInline

# ✅ Barcha importlar muvaffaqiyatli
```

---

## 📚 Qo'shimcha Ma'lumotlar

- [Django Model Relationships](https://docs.djangoproject.com/en/stable/topics/db/models/#relationships)
- [Django Lazy References](https://docs.djangoproject.com/en/stable/ref/models/fields/#foreignkey)
- [Python Circular Imports](https://docs.python.org/3/faq/programming.html#what-are-the-best-practices-for-using-import-in-a-module)

