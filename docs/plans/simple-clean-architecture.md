# Oddiy va Tushunarli Arxitektura - Clean Refactoring

**Maqsad:** HR app'ni olib tashlash va barcha funksionallikni BranchMembership orqali amalga oshirish.  
**Sabab:** Ortiqcha murakkablik, kod chalkashligi, auth qismi sodda va ishonchli bo'lishi kerak.

---

## 🎯 Asosiy Prinsiplar

1. **User** - Foydalanuvchi (telefon, ism, parol)
2. **Branch** - Filial (maktab yoki o'quv markaz)
3. **BranchMembership** - User + Branch + Role = Barcha ma'lumotlar shu yerda
4. **Role** - Rol turlari (o'qituvchi, qorovul, oshpaz va boshqalar uchun maxsus rollar)

---

## 📊 Hozirgi Muammo

```
❌ MURAKKAB (hozir):

User
  ├── BranchMembership (role, balance, salary)
  │   └── branch_id, role (string: teacher, admin, student)
  │
  └── StaffProfile (HR app) 
      ├── user_id, branch_id, staff_role_id
      ├── current_balance (DUBLIKAT!)
      ├── base_salary (DUBLIKAT!)
      └── hire_date, passport, etc.

MUAMMOLAR:
- Balance 2 joyda (BranchMembership va StaffProfile)
- Salary 2 joyda
- O'qituvchilar BranchMembership'da, lekin StaffProfile'da yo'q
- BalanceTransaction StaffProfile'ga bog'langan
- API chalkash (qayerdan olish kerak?)
- Kod dublikatsiyasi
```

---

## ✅ Oddiy va To'g'ri Arxitektura

```
User (auth.users)
  ├── phone_number (username)
  ├── first_name, last_name
  ├── email (optional)
  └── password

Branch (branch.branch)
  ├── name
  ├── type: SCHOOL, CENTER
  ├── code: TAS, SAM, BUK
  └── status: ACTIVE, INACTIVE

BranchMembership (branch.branchmembership) [BARCHA MA'LUMOTLAR SHU YERDA]
  ├── user_id (ForeignKey to User)
  ├── branch_id (ForeignKey to Branch)
  │
  ├── role (CharField) - ASOSIY ROLLAR
  │   ├── 'super_admin' - Barcha filiallarni boshqaradi
  │   ├── 'branch_admin' - Faqat o'z filialini boshqaradi
  │   ├── 'teacher' - O'qituvchi (davomat, baholar, o'quvchilar)
  │   ├── 'student' - O'quvchi (faqat o'z ma'lumotlarini)
  │   ├── 'parent' - Ota-ona (farzandining ma'lumotlarini)
  │   └── 'other' - Boshqa xodimlar (qorovul, oshpaz, etc.)
  │
  ├── role_ref (ForeignKey to Role, optional)
  │   └── Faqat 'other' uchun (qorovul, oshpaz kabi maxsus rollar)
  │
  ├── MOLIYAVIY MA'LUMOTLAR (faqat staff uchun)
  │   ├── balance (IntegerField) - Xodim balansi
  │   ├── salary_type: MONTHLY, HOURLY, PER_LESSON
  │   ├── monthly_salary
  │   ├── hourly_rate
  │   └── per_lesson_rate
  │
  ├── ISH MA'LUMOTLARI (faqat staff uchun)
  │   ├── hire_date (ishga kirgan sana)
  │   ├── termination_date (ishdan chiqqan sana)
  │   ├── employment_type: FULL_TIME, PART_TIME, CONTRACT
  │   ├── passport_serial, passport_number
  │   ├── address
  │   └── emergency_contact
  │
  └── QO'SHIMCHA
      ├── title (lavozim nomi: "Fizika o'qituvchisi")
      ├── notes (JSONField - qo'shimcha ma'lumotlar)
      └── is_active (faol yoki yo'q)

Role (branch.role) - FAQAT MAXSUS ROLLAR UCHUN
  ├── name: "Qorovul", "Oshpaz", "Haydovchi"
  ├── code: "guard", "cook", "driver"
  ├── branch_id (optional - filiaga tegishli yoki umumiy)
  ├── permissions: {"kitchen": ["view_menu", "manage_inventory"]}
  ├── salary_range_min, salary_range_max (optional)
  └── description

BalanceTransaction (branch.balancetransaction)
  ├── membership_id (ForeignKey to BranchMembership)
  ├── amount (IntegerField)
  ├── transaction_type: SALARY, BONUS, DEDUCTION, ADVANCE, ADJUSTMENT
  ├── description
  ├── previous_balance, new_balance
  └── created_by, created_at

SalaryPayment (branch.salarypayment)
  ├── membership_id (ForeignKey to BranchMembership)
  ├── amount (IntegerField)
  ├── payment_date
  ├── payment_method: CASH, BANK_TRANSFER, CARD
  ├── status: PENDING, PAID, CANCELLED
  ├── notes
  └── created_by, created_at
```

---

## 🔄 Refactoring Plan

### Phase 1: BranchMembership'ni to'liq qilish ✅

```python
# apps/branch/models.py

class EmploymentType(models.TextChoices):
    FULL_TIME = 'full_time', 'To\'liq stavka'
    PART_TIME = 'part_time', 'Yarim stavka'
    CONTRACT = 'contract', 'Shartnoma asosida'

class BranchMembership(BaseModel):
    """Yagona model - barcha xodim va o'quvchilar uchun."""
    
    # ASOSIY
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='memberships')
    
    # ROL
    role = models.CharField(max_length=32, choices=BranchRole.choices)
    role_ref = models.ForeignKey(Role, null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=100, blank=True)
    
    # MOLIYAVIY (faqat staff: teacher, admin, other)
    balance = models.IntegerField(default=0)
    salary_type = models.CharField(max_length=20, choices=SalaryType.choices, default='monthly')
    monthly_salary = models.IntegerField(default=0)
    hourly_rate = models.IntegerField(default=0, null=True, blank=True)
    per_lesson_rate = models.IntegerField(default=0, null=True, blank=True)
    
    # ISH MA'LUMOTLARI (faqat staff)
    hire_date = models.DateField(null=True, blank=True, db_index=True)
    termination_date = models.DateField(null=True, blank=True, db_index=True)
    employment_type = models.CharField(
        max_length=20, 
        choices=EmploymentType.choices, 
        default=EmploymentType.FULL_TIME,
        blank=True
    )
    
    # SHAXSIY MA'LUMOTLAR (faqat staff)
    passport_serial = models.CharField(max_length=2, blank=True)
    passport_number = models.CharField(max_length=7, blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    
    # QO'SHIMCHA
    notes = models.JSONField(default=dict, blank=True)
    
    class Meta:
        unique_together = ('user', 'branch')
        indexes = [
            models.Index(fields=['branch', 'role']),
            models.Index(fields=['user', 'branch', 'role']),
            models.Index(fields=['hire_date']),
            models.Index(fields=['termination_date']),
        ]
    
    @property
    def is_staff(self):
        """Xodimmi? (student va parent emas)"""
        return self.role not in ['student', 'parent']
    
    @property
    def is_active_employment(self):
        """Hozir ishlayaptimi?"""
        return self.hire_date and not self.termination_date
    
    @property
    def days_employed(self):
        """Necha kun ishlamoqda?"""
        if not self.hire_date:
            return None
        end = self.termination_date or timezone.now().date()
        return (end - self.hire_date).days
    
    def get_salary(self):
        """Oylik maosh miqdorini qaytarish."""
        if self.salary_type == 'monthly':
            return self.monthly_salary
        elif self.salary_type == 'hourly':
            return self.hourly_rate or 0
        elif self.salary_type == 'per_lesson':
            return self.per_lesson_rate or 0
        return 0
```

### Phase 2: BalanceTransaction va SalaryPayment'ni ko'chirish

```python
# apps/branch/models.py (HR'dan ko'chirish)

class TransactionType(models.TextChoices):
    SALARY = 'salary', 'Maosh'
    BONUS = 'bonus', 'Bonus'
    DEDUCTION = 'deduction', 'Ushlab qolish'
    ADVANCE = 'advance', 'Avans'
    ADJUSTMENT = 'adjustment', 'To\'g\'rilash'

class BalanceTransaction(BaseModel):
    """Balans o'zgarishlari tarixi."""
    
    membership = models.ForeignKey(
        BranchMembership,
        on_delete=models.CASCADE,
        related_name='balance_transactions'
    )
    amount = models.IntegerField(validators=[MinValueValidator(1)])
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    description = models.TextField(blank=True)
    
    previous_balance = models.IntegerField()
    new_balance = models.IntegerField()
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

class PaymentStatus(models.TextChoices):
    PENDING = 'pending', 'Kutilmoqda'
    PAID = 'paid', 'To\'langan'
    CANCELLED = 'cancelled', 'Bekor qilingan'

class PaymentMethod(models.TextChoices):
    CASH = 'cash', 'Naqd'
    BANK_TRANSFER = 'bank_transfer', 'Bank o\'tkazmasi'
    CARD = 'card', 'Karta'

class SalaryPayment(BaseModel):
    """Maosh to'lovlari."""
    
    membership = models.ForeignKey(
        BranchMembership,
        on_delete=models.CASCADE,
        related_name='salary_payments'
    )
    amount = models.IntegerField(validators=[MinValueValidator(1)])
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default='pending')
    notes = models.TextField(blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
```

### Phase 3: Unified Staff API

```python
# apps/branch/views.py

class StaffViewSet(viewsets.ModelViewSet):
    """Barcha xodimlar uchun yagona API.
    
    GET /api/staff/?branch={id} - Barcha xodimlar
    GET /api/staff/?branch={id}&role=teacher - Faqat o'qituvchilar
    GET /api/staff/?branch={id}&status=active - Faqat faol xodimlar
    POST /api/staff/ - Yangi xodim qo'shish
    PUT /api/staff/{id}/ - Xodim ma'lumotlarini tahrirlash
    DELETE /api/staff/{id}/ - Xodimni o'chirish (soft delete)
    
    GET /api/staff/stats/?branch={id} - Statistika
    """
    
    permission_classes = [IsAuthenticated, IsBranchAdminOrSuperAdmin]
    serializer_class = StaffSerializer
    
    def get_queryset(self):
        branch_id = self.request.query_params.get('branch')
        if not branch_id:
            raise ValidationError({'branch': 'Branch ID required'})
        
        # Faqat xodimlar (student va parent emas)
        qs = BranchMembership.objects.filter(
            branch_id=branch_id,
            role__in=['teacher', 'branch_admin', 'super_admin', 'other']
        ).select_related('user', 'branch', 'role_ref')
        
        # Filters
        role = self.request.query_params.get('role')
        if role:
            qs = qs.filter(role=role)
        
        status = self.request.query_params.get('status')
        if status == 'active':
            qs = qs.filter(hire_date__isnull=False, termination_date__isnull=True)
        elif status == 'terminated':
            qs = qs.filter(termination_date__isnull=False)
        
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(user__phone_number__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search)
            )
        
        return qs
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Xodimlar statistikasi."""
        branch_id = request.query_params.get('branch')
        
        staff = BranchMembership.objects.filter(
            branch_id=branch_id,
            role__in=['teacher', 'branch_admin', 'super_admin', 'other']
        )
        
        return Response({
            'total': staff.count(),
            'active': staff.filter(hire_date__isnull=False, termination_date__isnull=True).count(),
            'terminated': staff.filter(termination_date__isnull=False).count(),
            'by_role': {
                'teachers': staff.filter(role='teacher').count(),
                'admins': staff.filter(role__in=['branch_admin', 'super_admin']).count(),
                'other': staff.filter(role='other').count(),
            },
            'total_balance': staff.aggregate(total=Sum('balance'))['total'] or 0,
        })

class StaffSerializer(serializers.ModelSerializer):
    """Xodim serializer."""
    
    # User ma'lumotlari
    phone_number = serializers.CharField(source='user.phone_number')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email', required=False, allow_blank=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    # Rol ma'lumotlari
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    role_ref_name = serializers.CharField(source='role_ref.name', read_only=True, allow_null=True)
    
    # Computed fields
    salary = serializers.IntegerField(source='get_salary', read_only=True)
    days_employed = serializers.IntegerField(read_only=True)
    is_active_employment = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = BranchMembership
        fields = [
            'id', 'user_id', 'branch_id',
            'phone_number', 'first_name', 'last_name', 'email', 'full_name',
            'role', 'role_display', 'role_ref', 'role_ref_name', 'title',
            'balance', 'salary', 'salary_type', 'monthly_salary', 'hourly_rate', 'per_lesson_rate',
            'hire_date', 'termination_date', 'employment_type',
            'passport_serial', 'passport_number', 'address', 'emergency_contact',
            'days_employed', 'is_active_employment',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user_id', 'created_at', 'updated_at']
```

---

## 🗑️ HR App'ni Deprecate Qilish

### Migration Strategy:

```python
# 1. Data migration: HR → BranchMembership
python manage.py migrate_hr_to_membership

# 2. Update BalanceTransaction foreign keys
python manage.py migrate_balance_transactions

# 3. Backup va delete HR app
python manage.py backup_hr_data
python manage.py remove_hr_app
```

### Migration Script:

```python
# apps/branch/management/commands/migrate_hr_to_membership.py

class Command(BaseCommand):
    def handle(self, *args, **options):
        from apps.hr.models import StaffProfile
        
        for staff in StaffProfile.objects.all():
            # BranchMembership topish yoki yaratish
            membership, created = BranchMembership.objects.get_or_create(
                user=staff.user,
                branch=staff.branch,
                defaults={'role': 'other'}  # default
            )
            
            # Ma'lumotlarni ko'chirish
            membership.hire_date = staff.hire_date
            membership.termination_date = staff.termination_date
            membership.employment_type = staff.employment_type
            membership.passport_serial = staff.passport_serial
            membership.passport_number = staff.passport_number
            membership.address = staff.address
            membership.emergency_contact = staff.emergency_contact
            membership.balance = staff.current_balance
            membership.monthly_salary = staff.base_salary
            
            # Role'ni to'g'rilash
            if staff.staff_role:
                # staff_role → role_ref (Role modelga)
                role, _ = Role.objects.get_or_create(
                    name=staff.staff_role.name,
                    branch=staff.branch,
                    defaults={
                        'code': staff.staff_role.code,
                        'permissions': staff.staff_role.permissions,
                        'salary_range_min': staff.staff_role.salary_range_min,
                        'salary_range_max': staff.staff_role.salary_range_max,
                    }
                )
                membership.role_ref = role
            
            membership.save()
            self.stdout.write(f'✓ {staff.user.get_full_name()} ko\'chirildi')
```

---

## 📁 Fayl Strukturasi

```
apps/
  branch/
    models.py          # BranchMembership, BalanceTransaction, SalaryPayment
    views.py           # StaffViewSet, BalanceViewSet, SalaryPaymentViewSet
    serializers.py     # StaffSerializer, BalanceTransactionSerializer
    admin.py           # Staff admin panel
    urls.py            # /api/staff/, /api/balance/, /api/salary/
    services.py        # BalanceService
    
  hr/                  # ❌ DEPRECATED - O'chiriladi
  
  auth/
    users/
      models.py        # User model
      views.py         # Login, register, profile
  
  school/
    classes/          # Sinflar
    subjects/         # Fanlar
    academic/         # Akademik yil, chorak
```

---

## ✅ Natija

**Endi:**
- ✅ Barcha xodim ma'lumotlari BranchMembership'da
- ✅ Bir source of truth (balance, salary)
- ✅ Oddiy va tushunarli API
- ✅ O'qituvchi, admin, oshpaz, qorovul - barchasi bir joyda
- ✅ Student va parent ham shu model orqali
- ✅ Kod dublikatsiyasi yo'q
- ✅ HR app muammosi hal qilindi
- ✅ Auth qismi sodda va ishonchli

**API misollari:**
```bash
# Barcha o'qituvchilar
GET /api/staff/?branch=123&role=teacher

# Faol xodimlar
GET /api/staff/?branch=123&status=active

# Xodim qo'shish
POST /api/staff/
{
  "phone_number": "+998901234567",
  "first_name": "Ali",
  "last_name": "Valiyev",
  "branch_id": "...",
  "role": "teacher",
  "monthly_salary": 5000000,
  "hire_date": "2025-01-01"
}

# Balance qo'shish
POST /api/balance/add/
{
  "membership_id": "...",
  "amount": 1000000,
  "transaction_type": "salary",
  "description": "Yanvar oyi maoshi"
}
```

---

Bu arxitektura oddiy, tushunarli va kengaytirish oson!
