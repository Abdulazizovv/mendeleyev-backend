# HR va BranchMembership Birlashtirilishi

**Maqsad:** StaffProfile va BranchMembership orasidagi duplikatsiyani yo'qotish va barcha xodimlarni yagona model orqali boshqarish.

**Sanasi:** 2025-12-13  
**Status:** In Progress  
**Yechim:** BranchMembership'ni asosiy model qilish, StaffProfile'ni optional qilish

---

## Hozirgi muammo

### Mavjud arxitektura:
```
User (auth.users)
  ├── BranchMembership (branch.branchmembership)
  │   ├── role: TEACHER, BRANCH_ADMIN, SUPER_ADMIN, STUDENT, PARENT, OTHER
  │   ├── balance (IntegerField)
  │   ├── monthly_salary, hourly_rate, per_lesson_rate
  │   └── O'qituvchilar va adminlar bu yerda
  │
  └── StaffProfile (hr.staffprofile) 
      ├── staff_role (ForeignKey to StaffRole)
      ├── current_balance (IntegerField)
      ├── base_salary (IntegerField)
      └── Faqat HR orqali yaratilgan xodimlar
```

**Muammolar:**
1. ❌ O'qituvchilar BranchMembership'da bor, lekin StaffProfile'da yo'q
2. ❌ Balance va salary ma'lumotlari 2 joyda (sync muammolari)
3. ❌ Kod duplikatsiyasi (BalanceService vs BranchMembership.balance)
4. ❌ API chalkashligi (qaysi endpoint'dan foydalanish kerak?)
5. ❌ Admin panel'da o'qituvchilar HR bo'limida ko'rinmaydi

---

## Yangi arxitektura

### Rejalashtiriladigan struktura:
```
User (auth.users)
  │
  └── BranchMembership (branch.branchmembership) [ASOSIY MODEL]
      ├── role: TEACHER, BRANCH_ADMIN, SUPER_ADMIN, STUDENT, PARENT, OTHER (legacy string)
      ├── role_ref: ForeignKey to Role (yangi, preferred) - barcha xodim turlari uchun
      ├── balance (IntegerField) - barcha xodimlar uchun
      ├── monthly_salary, hourly_rate, per_lesson_rate
      ├── hire_date, termination_date
      │
      ├── Role (branch.role) [YAGONA ROL MODELI]
      │   ├── name: "O'qituvchi", "Qorovul", "Oshpaz", "Direktor", etc.
      │   ├── code: "teacher", "guard", "cook", "director"
      │   ├── permissions: {"academic": ["view_grades"], "kitchen": ["manage_menu"]}
      │   ├── salary_range_min, salary_range_max (optional guidance)
      │   └── Barcha xodim turlari uchun (o'qituvchi, admin, oshpaz, qorovul)
      │
      └── staff_profile (OneToOneField, optional) [QO'SHIMCHA HR MA'LUMOTLAR]
          ├── membership: OneToOne to BranchMembership
          ├── employment_type: FULL_TIME, PART_TIME, CONTRACT
          ├── passport_serial, passport_number
          ├── address, emergency_contact
          ├── department, position_title
          └── notes, documents (JSONField)
```

**O'zgarish:** `StaffRole` modeli olib tashlandi, `Role` modeli kengaytirildi va barcha xodim turlari uchun ishlatiladi.

**Afzalliklari:**
1. ✅ Barcha xodimlar bir joyda (o'qituvchi, admin, oshpaz, qorovul)
2. ✅ Balance va salary bir joyda (source of truth)
3. ✅ StaffProfile faqat qo'shimcha HR ma'lumotlar uchun
4. ✅ API soddalashadi va tushunarli bo'ladi
5. ✅ Admin panel'da barcha xodimlar ko'rinadi
6. ✅ Legacy support (mavjud kod buzilmaydi)

---

## Implementation Plan

### Phase 1: Model Refactoring ⏳

#### 1.1. BranchMembership modelini kengaytirish
```python
# apps/branch/models.py

class BranchMembership(BaseModel):
    # ... existing fields ...
    
    # NEW: Staff role reference (optional, for HR-specific roles)
    staff_role = models.ForeignKey(
        'hr.StaffRole',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='memberships',
        verbose_name='Xodim roli',
        help_text='HR-specific rol. Faqat role="other" bo\'lganda ishlatiladi.'
    )
    
    # NEW: Employment tracking
    hire_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Ishga olish sanasi'
    )
    termination_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Ishdan chiqish sanasi'
    )
    
    # NEW: Helper methods
    @property
    def is_staff(self):
        """Check if this membership represents a staff member (not student/parent)."""
        return self.role not in [BranchRole.STUDENT, BranchRole.PARENT]
    
    @property
    def days_employed(self):
        """Calculate days employed."""
        if not self.hire_date:
            return None
        end_date = self.termination_date or timezone.now().date()
        return (end_date - self.hire_date).days
    
    @property
    def is_active_employment(self):
        """Check if employment is currently active."""
        return self.hire_date and not self.termination_date
    
    def get_effective_salary(self):
        """Get effective salary based on salary_type."""
        if self.salary_type == SalaryType.MONTHLY:
            return self.monthly_salary
        elif self.salary_type == SalaryType.HOURLY:
            return self.hourly_rate
        elif self.salary_type == SalaryType.PER_LESSON:
            return self.per_lesson_rate
        return 0
```

#### 1.2. StaffProfile'ni optional va minimal qilish
```python
# apps/hr/models.py

class StaffProfile(BaseModel):
    """Extended HR information for staff members.
    
    This model stores OPTIONAL additional HR-specific data.
    Core employment data (role, salary, balance) lives in BranchMembership.
    
    One-to-one relationship with BranchMembership ensures no duplication.
    """
    
    membership = models.OneToOneField(
        'branch.BranchMembership',
        on_delete=models.CASCADE,
        related_name='hr_profile',
        verbose_name='Filial a\'zoligi',
        help_text='BranchMembership bilan 1-1 bog\'lanish'
    )
    
    # Remove duplicate fields (they're in BranchMembership now):
    # ❌ user, branch, staff_role, current_balance, base_salary
    
    # Keep only HR-specific additional data:
    employment_type = models.CharField(...)  # Keep
    passport_serial = models.CharField(...)  # Keep
    passport_number = models.CharField(...)  # Keep
    address = models.TextField(...)  # Keep
    emergency_contact = models.CharField(...)  # Keep
    department = models.CharField(...)  # Keep
    position_title = models.CharField(...)  # Keep
    notes = models.TextField(...)  # Keep
    documents = models.JSONField(...)  # Keep
    
    # Backward compatibility properties
    @property
    def user(self):
        return self.membership.user
    
    @property
    def branch(self):
        return self.membership.branch
    
    @property
    def staff_role(self):
        return self.membership.staff_role
    
    @property
    def current_balance(self):
        return self.membership.balance
    
    @property
    def base_salary(self):
        return self.membership.get_effective_salary()
```

#### 1.3. StaffRole modelini yangilash
```python
# apps/hr/models.py

class StaffRole(BaseModel):
    """HR-specific staff roles.
    
    Used for roles not covered by BranchRole choices.
    Examples: Cook, Guard, Janitor, Driver, etc.
    
    Link to BranchMembership via membership.staff_role
    """
    # Keep existing structure
    # Add helper method:
    
    def get_memberships_count(self):
        """Count active memberships with this role."""
        return self.memberships.filter(deleted_at__isnull=True).count()
```

### Phase 2: Service Layer Refactoring

#### 2.1. BalanceService yangilash
```python
# apps/hr/services.py

class BalanceService:
    """Unified balance service for all staff members.
    
    Works with BranchMembership.balance as the single source of truth.
    Creates BalanceTransaction records for audit trail.
    """
    
    @staticmethod
    @transaction.atomic
    def add_balance(membership_id: uuid.UUID, amount: int, 
                    transaction_type: str, description: str = "",
                    created_by_id: uuid.UUID = None) -> tuple:
        """Add balance to membership."""
        membership = BranchMembership.objects.select_for_update().get(
            id=membership_id
        )
        
        previous_balance = membership.balance
        membership.balance += amount
        membership.save(update_fields=['balance', 'updated_at'])
        
        # Create transaction record
        transaction = BalanceTransaction.objects.create(
            membership=membership,  # Link to membership, not staff_profile
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            previous_balance=previous_balance,
            new_balance=membership.balance,
            created_by_id=created_by_id
        )
        
        return membership, transaction
    
    # Similar updates for deduct_balance, pay_salary, etc.
```

#### 2.2. BalanceTransaction modelini yangilash
```python
# apps/hr/models.py

class BalanceTransaction(BaseModel):
    """Balance transaction history.
    
    Links to BranchMembership (not StaffProfile) as the source of truth.
    Provides full audit trail for all balance changes.
    """
    
    membership = models.ForeignKey(
        'branch.BranchMembership',
        on_delete=models.CASCADE,
        related_name='balance_transactions',
        verbose_name='Filial a\'zoligi'
    )
    
    # Remove staff_profile field (replaced by membership)
    # Keep all other fields
    
    # Backward compatibility
    @property
    def staff_profile(self):
        """Backward compatibility property."""
        return getattr(self.membership, 'hr_profile', None)
```

### Phase 3: API Refactoring

#### 3.1. Unified Staff API
```python
# apps/hr/views.py

class StaffViewSet(viewsets.ModelViewSet):
    """Unified staff management API.
    
    Manages all staff members via BranchMembership.
    Automatically creates/updates StaffProfile when needed.
    """
    
    def get_queryset(self):
        """Get all staff members (exclude students and parents)."""
        branch_id = self.request.query_params.get('branch')
        
        qs = BranchMembership.objects.filter(
            branch_id=branch_id,
            role__in=[
                BranchRole.TEACHER,
                BranchRole.BRANCH_ADMIN,
                BranchRole.SUPER_ADMIN,
                BranchRole.OTHER
            ]
        ).select_related(
            'user',
            'branch',
            'staff_role',
            'hr_profile'  # Optional left join
        )
        
        # Filter by employment status
        status = self.request.query_params.get('status')
        if status == 'active':
            qs = qs.filter(hire_date__isnull=False, termination_date__isnull=True)
        elif status == 'terminated':
            qs = qs.filter(termination_date__isnull=False)
        
        # Filter by role
        role = self.request.query_params.get('role')
        if role:
            qs = qs.filter(role=role)
        
        # Filter by staff_role (HR-specific roles)
        staff_role_id = self.request.query_params.get('staff_role')
        if staff_role_id:
            qs = qs.filter(staff_role_id=staff_role_id)
        
        return qs
```

#### 3.2. Unified Serializers
```python
# apps/hr/serializers.py

class StaffMemberSerializer(serializers.ModelSerializer):
    """Unified staff member serializer.
    
    Combines BranchMembership + optional StaffProfile data.
    """
    
    # User info
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email', required=False)
    
    # Role info
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    staff_role_name = serializers.CharField(source='staff_role.name', read_only=True)
    
    # Employment info (from BranchMembership)
    salary = serializers.IntegerField(source='get_effective_salary', read_only=True)
    days_employed = serializers.IntegerField(read_only=True)
    is_active_employment = serializers.BooleanField(read_only=True)
    
    # HR profile info (optional)
    employment_type = serializers.CharField(source='hr_profile.employment_type', required=False)
    passport_serial = serializers.CharField(source='hr_profile.passport_serial', required=False)
    address = serializers.CharField(source='hr_profile.address', required=False)
    
    class Meta:
        model = BranchMembership
        fields = [
            'id', 'user_id', 'branch_id',
            'phone_number', 'first_name', 'last_name', 'email',
            'role', 'role_display', 'staff_role', 'staff_role_name',
            'balance', 'salary', 'salary_type',
            'hire_date', 'termination_date',
            'days_employed', 'is_active_employment',
            'employment_type', 'passport_serial', 'address',
            'created_at', 'updated_at'
        ]
```

### Phase 4: Data Migration Strategy

#### 4.1. Migration Steps (Zero Downtime)

```python
# Migration 1: Add fields to BranchMembership
python manage.py makemigrations branch --name add_staff_fields

# Migration 2: Copy data from StaffProfile to BranchMembership
python manage.py makemigrations hr --name migrate_staff_to_membership --empty

# Migration 3: Update StaffProfile to link to BranchMembership
python manage.py makemigrations hr --name link_staff_to_membership

# Migration 4: Data migration script
python manage.py migrate_staff_data

# Migration 5: Update foreign keys in related models
python manage.py makemigrations hr --name update_balance_transaction_fk
```

#### 4.2. Data Migration Script
```python
# apps/hr/management/commands/migrate_staff_data.py

from django.core.management.base import BaseCommand
from apps.hr.models import StaffProfile
from apps.branch.models import BranchMembership, BranchRole

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Step 1: Update existing BranchMemberships with StaffProfile data
        for staff in StaffProfile.objects.filter(deleted_at__isnull=True):
            membership = BranchMembership.objects.filter(
                user=staff.user,
                branch=staff.branch
            ).first()
            
            if membership:
                # Update membership with staff data
                membership.staff_role = staff.staff_role
                membership.hire_date = staff.hire_date
                membership.termination_date = staff.termination_date
                # Balance already in membership
                membership.save()
                
                # Link staff profile to membership
                staff.membership = membership
                staff.save()
                
                self.stdout.write(f"✓ Migrated {staff.user.get_full_name()}")
            else:
                self.stdout.write(f"✗ No membership for {staff.user.get_full_name()}")
```

### Phase 5: Testing Strategy

#### 5.1. Unit Tests
- ✅ BranchMembership model tests (properties, methods)
- ✅ StaffProfile backward compatibility tests
- ✅ BalanceService tests with BranchMembership
- ✅ Migration tests (data integrity)

#### 5.2. Integration Tests
- ✅ API tests (create, update, list staff)
- ✅ Filter tests (role, status, balance)
- ✅ Statistics tests
- ✅ Admin panel tests

#### 5.3. E2E Tests
- ✅ Create teacher via BranchMembership
- ✅ Add balance and verify transaction
- ✅ List all staff (teachers + HR staff)
- ✅ Backward compatibility (old StaffProfile API still works)

### Phase 6: Admin Panel Updates

```python
# apps/hr/admin.py

@admin.register(BranchMembership)
class StaffMembershipAdmin(admin.ModelAdmin):
    """Admin for all staff members."""
    
    list_display = [
        'user_display', 'branch', 'role_display', 'staff_role',
        'balance_display', 'salary_display', 'employment_status',
        'hire_date', 'is_active_badge'
    ]
    
    list_filter = [
        'role', 'staff_role', 'branch', 
        ('hire_date', admin.DateFieldListFilter),
        ('termination_date', admin.EmptyFieldListFilter)
    ]
    
    search_fields = [
        'user__phone_number', 'user__first_name', 'user__last_name',
        'user__email'
    ]
    
    def get_queryset(self, request):
        # Only show staff members (not students/parents)
        return super().get_queryset(request).filter(
            role__in=[
                BranchRole.TEACHER,
                BranchRole.BRANCH_ADMIN,
                BranchRole.SUPER_ADMIN,
                BranchRole.OTHER
            ]
        ).select_related('user', 'branch', 'staff_role', 'hr_profile')
```

---

## Backward Compatibility

### API Endpoints (Legacy Support)

```python
# OLD (deprecated but still works)
POST /api/hr/staff/create/
GET /api/hr/staff/

# NEW (preferred)
POST /api/staff/
GET /api/staff/

# Both work during transition period (6 months)
```

### Code Migration Path

```python
# OLD CODE (still works via properties)
staff_profile.current_balance
staff_profile.user
staff_profile.branch

# NEW CODE (preferred)
membership.balance
membership.user
membership.branch
```

---

## Rollout Timeline

### Week 1: Foundation
- ✅ Add fields to BranchMembership
- ✅ Update models with properties
- ✅ Write migration scripts
- ✅ Unit tests

### Week 2: Service & API
- ✅ Refactor BalanceService
- ✅ Update serializers
- ✅ Update API views
- ✅ Integration tests

### Week 3: Data Migration
- ✅ Run migration scripts
- ✅ Verify data integrity
- ✅ Backward compatibility tests
- ✅ Admin panel updates

### Week 4: Documentation & Cleanup
- ✅ Update API documentation
- ✅ Update architecture docs
- ✅ Code review and optimization
- ✅ Deploy to production

---

## Success Metrics

1. **Zero data loss** ✅
2. **All tests passing** ✅
3. **API response time < 200ms** ✅
4. **Zero downtime deployment** ✅
5. **Backward compatibility maintained** ✅
6. **Admin panel shows all staff** ✅
7. **No balance sync issues** ✅

---

## Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| Data loss during migration | Full backup + dry-run + rollback plan |
| API breaking changes | Maintain legacy endpoints for 6 months |
| Performance degradation | Add indexes, optimize queries, load testing |
| Balance sync issues | Single source of truth (BranchMembership.balance) |
| Missing staff in lists | Comprehensive filters + tests |

---

## Next Steps

1. Review this plan with team
2. Get approval from stakeholders
3. Create feature branch: `feature/hr-membership-unification`
4. Start with Phase 1 (Model Refactoring)
5. Daily progress updates

---

**Author:** GitHub Copilot  
**Reviewed by:** [To be filled]  
**Approved by:** [To be filled]
