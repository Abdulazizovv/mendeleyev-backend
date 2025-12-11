# HR (Xodimlar Boshqaruvi) API

HR moduli xodimlarni boshqarish, maosh va balans tranzaksiyalarini kuzatish uchun to'liq API taqdim etadi.

## Arxitektura

### Asosiy Modellar

1. **StaffRole** - Xodim rollari (Oshpaz, Qorovul, O'qituvchi, va h.k.)
   - Har filial o'z rollarini yaratadi
   - Ruxsatlar (permissions) JSON formatida saqlanadi
   - Maosh diapazoni (ixtiyoriy)

2. **StaffProfile** - Xodim profili
   - User, Branch va StaffRole bilan bog'lanadi
   - Moliyaviy ma'lumotlar (asosiy maosh, joriy balans)
   - Ish ma'lumotlari (ishga qabul sanasi, ish turi, holat)
   - Bank va soliq ma'lumotlari

3. **BalanceTransaction** - Balans tranzaksiyalari
   - Har bir balans o'zgarishi tranzaksiya yaratadi
   - Previous/new balance snapshots
   - Atomic operations via BalanceService
   - To'liq audit trail

4. **SalaryPayment** - Maosh to'lovlari
   - Oylik maosh to'lovlarini kuzatadi
   - Status: pending, paid, cancelled, failed
   - Paid holatga o'tganda avtomatik BalanceTransaction yaratiladi

### Data Flow

```
User → BranchMembership (lightweight) → StaffProfile (HR data)
                                           ↓
                                    BalanceTransaction
                                           ↑
                                    SalaryPayment (when status=paid)
```

**Muhim:** `BranchMembership` yengil qoladi, barcha HR-specific ma'lumotlar `StaffProfile`da saqlanadi.

## API Endpoints

### Base URL
```
/api/v1/hr/
```

### 1. Rollar (Staff Roles)

#### Rollar ro'yxati
```http
GET /api/v1/hr/roles/
```

Query parametrlari:
- `branch` - Filial ID
- `is_active` - Faol rollar (true/false)
- `search` - Qidiruv (name, code, description)
- `ordering` - Tartiblash (name, created_at)

Response:
```json
{
  "count": 5,
  "results": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "Oshpaz",
      "code": "cook",
      "branch": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
      "branch_name": "Toshkent filiali",
      "is_active": true,
      "staff_count": 3
    }
  ]
}
```

#### Rol yaratish
```http
POST /api/v1/hr/roles/
```

Request:
```json
{
  "name": "Oshpaz",
  "code": "cook",
  "branch": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "permissions": ["view_menu", "manage_inventory"],
  "salary_range_min": 3000000,
  "salary_range_max": 5000000,
  "description": "Oshxona xodimi",
  "is_active": true
}
```

#### Rol tafsilotlari
```http
GET /api/v1/hr/roles/{id}/
```

Response:
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Oshpaz",
  "code": "cook",
  "branch": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "permissions": ["view_menu", "manage_inventory"],
  "salary_range_min": 3000000,
  "salary_range_max": 5000000,
  "description": "Oshxona xodimi",
  "is_active": true,
  "staff_count": 3,
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

#### Rol ruxsatlari
```http
GET /api/v1/hr/roles/{id}/permissions/
```

Response:
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Oshpaz",
  "permissions": ["view_menu", "manage_inventory"]
}
```

### 2. Xodimlar (Staff Profiles)

#### Xodimlar ro'yxati
```http
GET /api/v1/hr/staff/
```

Query parametrlari:
- `branch` - Filial ID
- `staff_role` - Rol ID
- `employment_type` - Ish turi (full_time, part_time, contract, temporary)
- `status` - Holat (active, inactive, on_leave, terminated)
- `active` - Faqat faol xodimlar (true/false)
- `search` - Qidiruv (ism, familiya, telefon, tax_id, bank_account)
- `ordering` - Tartiblash (hire_date, base_salary, current_balance, created_at)

Response:
```json
{
  "count": 15,
  "results": [
    {
      "id": "8f7e6d5c-4b3a-2109-8765-4321dcba0987",
      "user": "9a8b7c6d-5e4f-3a2b-1c0d-9e8f7a6b5c4d",
      "user_name": "Ali Valiyev",
      "branch": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
      "branch_name": "Toshkent filiali",
      "staff_role": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "role_name": "Oshpaz",
      "employment_type": "full_time",
      "base_salary": 4000000,
      "current_balance": 2500000,
      "status": "active",
      "hire_date": "2024-01-01"
    }
  ]
}
```

#### Xodim yaratish
```http
POST /api/v1/hr/staff/
```

Request:
```json
{
  "user": "9a8b7c6d-5e4f-3a2b-1c0d-9e8f7a6b5c4d",
  "branch": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "membership": "7b6c5d4e-3f2a-1b0c-9d8e-7f6a5b4c3d2e",
  "staff_role": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "employment_type": "full_time",
  "hire_date": "2024-01-01",
  "base_salary": 4000000,
  "bank_account": "8600123456789012",
  "tax_id": "12345678901234",
  "notes": "Tajribali oshpaz"
}
```

#### Xodim tafsilotlari
```http
GET /api/v1/hr/staff/{id}/
```

Response:
```json
{
  "id": "8f7e6d5c-4b3a-2109-8765-4321dcba0987",
  "user": "9a8b7c6d-5e4f-3a2b-1c0d-9e8f7a6b5c4d",
  "user_info": {
    "id": "9a8b7c6d-5e4f-3a2b-1c0d-9e8f7a6b5c4d",
    "phone_number": "+998901234567",
    "first_name": "Ali",
    "last_name": "Valiyev",
    "full_name": "Ali Valiyev",
    "email": "ali@example.com"
  },
  "branch": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "branch_name": "Toshkent filiali",
  "membership": "7b6c5d4e-3f2a-1b0c-9d8e-7f6a5b4c3d2e",
  "staff_role": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "staff_role_info": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "Oshpaz",
    "code": "cook"
  },
  "employment_type": "full_time",
  "hire_date": "2024-01-01",
  "termination_date": null,
  "base_salary": 4000000,
  "current_balance": 2500000,
  "balance_summary": {
    "current_balance": 2500000,
    "total_credits": 8000000,
    "total_debits": 5500000,
    "net": 2500000
  },
  "bank_account": "8600123456789012",
  "tax_id": "12345678901234",
  "status": "active",
  "notes": "Tajribali oshpaz",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-15T14:30:00Z"
}
```

#### Maoshni yangilash
```http
PATCH /api/v1/hr/staff/{id}/salary/
```

Request:
```json
{
  "base_salary": 4500000
}
```

Response:
```json
{
  "message": "Maosh muvaffaqiyatli yangilandi.",
  "old_salary": 4000000,
  "new_salary": 4500000
}
```

#### Xodim tranzaksiyalari
```http
GET /api/v1/hr/staff/{id}/transactions/
```

Response:
```json
{
  "count": 10,
  "results": [
    {
      "id": "f1e2d3c4-b5a6-7890-1234-567890abcdef",
      "staff": "8f7e6d5c-4b3a-2109-8765-4321dcba0987",
      "staff_name": "Ali Valiyev",
      "transaction_type": "salary",
      "transaction_type_display": "Maosh",
      "amount": 4000000,
      "previous_balance": 0,
      "new_balance": 4000000,
      "reference": "SALARY-2024-01",
      "description": "Maosh to'lovi - Yanvar 2024",
      "salary_payment": "e4d5c6b7-a890-1234-5678-90abcdef1234",
      "processed_by": "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
      "processed_by_name": "Admin User",
      "created_at": "2024-01-05T10:00:00Z"
    }
  ]
}
```

#### Tranzaksiya yaratish
```http
POST /api/v1/hr/staff/{id}/create_transaction/
```

Request:
```json
{
  "transaction_type": "bonus",
  "amount": 500000,
  "description": "Yanvar oyi uchun bonus",
  "reference": "BONUS-2024-01"
}
```

Transaction type'lar:
- `deposit` - Kirim (to'lov)
- `withdrawal` - Chiqim
- `salary` - Maosh
- `bonus` - Bonus
- `fine` - Jarima
- `adjustment` - Tuzatish
- `advance` - Avans

Response:
```json
{
  "id": "c2d3e4f5-a6b7-8901-2345-67890abcdef1",
  "staff": "8f7e6d5c-4b3a-2109-8765-4321dcba0987",
  "staff_name": "Ali Valiyev",
  "transaction_type": "bonus",
  "transaction_type_display": "Bonus",
  "amount": 500000,
  "previous_balance": 4000000,
  "new_balance": 4500000,
  "reference": "BONUS-2024-01",
  "description": "Yanvar oyi uchun bonus",
  "processed_by": "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "processed_by_name": "Admin User",
  "created_at": "2024-01-15T10:00:00Z"
}
```

### 3. Balans Tranzaksiyalari

#### Tranzaksiyalar ro'yxati
```http
GET /api/v1/hr/transactions/
```

Query parametrlari:
- `staff` - Xodim ID
- `transaction_type` - Tranzaksiya turi
- `branch` - Filial ID (staff__branch)
- `search` - Qidiruv (reference, description, xodim ismi)
- `ordering` - Tartiblash (created_at, amount)

Response - yuqoridagi `/staff/{id}/transactions/` bilan bir xil format.

### 4. Maosh To'lovlari

#### Maosh to'lovlari ro'yxati
```http
GET /api/v1/hr/salaries/
```

Query parametrlari:
- `staff` - Xodim ID
- `status` - Holat (pending, paid, cancelled, failed)
- `payment_method` - To'lov usuli (cash, bank_transfer, card, click, payme, other)
- `branch` - Filial ID (staff__branch)
- `month` - Oy (YYYY-MM-DD format)
- `search` - Qidiruv (xodim ismi, reference_number)
- `ordering` - Tartiblash (payment_date, amount, created_at)

Response:
```json
{
  "count": 20,
  "results": [
    {
      "id": "e4d5c6b7-a890-1234-5678-90abcdef1234",
      "staff": "8f7e6d5c-4b3a-2109-8765-4321dcba0987",
      "staff_name": "Ali Valiyev",
      "month": "2024-01-01",
      "amount": 4000000,
      "payment_date": "2024-01-05",
      "payment_method": "bank_transfer",
      "payment_method_display": "Bank o'tkazmasi",
      "status": "paid",
      "status_display": "To'langan",
      "notes": "",
      "reference_number": "PAY-2024-01-001",
      "processed_by": "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
      "processed_by_name": "Admin User",
      "created_at": "2024-01-05T10:00:00Z",
      "updated_at": "2024-01-05T10:00:00Z"
    }
  ]
}
```

#### Maosh to'lovi yaratish
```http
POST /api/v1/hr/salaries/
```

Request:
```json
{
  "staff": "8f7e6d5c-4b3a-2109-8765-4321dcba0987",
  "month": "2024-02-01",
  "amount": 4000000,
  "payment_date": "2024-02-05",
  "payment_method": "bank_transfer",
  "status": "paid",
  "notes": "Fevral oyi maoshi",
  "reference_number": "PAY-2024-02-001"
}
```

**Muhim:** Status `paid` bo'lganda avtomatik ravishda BalanceTransaction yaratiladi.

#### Bulk maosh to'lovlari
```http
POST /api/v1/hr/salaries/bulk/
```

Request:
```json
{
  "month": "2024-02-01",
  "payments": [
    {
      "staff_id": "8f7e6d5c-4b3a-2109-8765-4321dcba0987",
      "amount": 4000000,
      "payment_date": "2024-02-05",
      "payment_method": "bank_transfer",
      "notes": ""
    },
    {
      "staff_id": "b3c4d5e6-f7a8-9012-3456-7890abcdef12",
      "amount": 3500000,
      "payment_date": "2024-02-05",
      "payment_method": "cash",
      "notes": ""
    }
  ]
}
```

Response:
```json
{
  "message": "Maosh to'lovlari navbatga qo'shildi.",
  "task_id": "d4e5f6a7-b8c9-0123-4567-890abcdef123",
  "total_payments": 2
}
```

**Eslatma:** Bu endpoint Celery task yaratadi va asinxron ishlanadi. Task ID orqali statusni tekshirish mumkin.

#### Oylik hisobot
```http
GET /api/v1/hr/salaries/report/2024-02-01/
```

Query parametrlari:
- `branch` - Filial ID (ixtiyoriy)

Response:
```json
{
  "month": "2024-02-01",
  "total_staff": 15,
  "total_paid": 12,
  "total_amount": 48000000,
  "by_role": [
    {
      "staff__staff_role__name": "Oshpaz",
      "count": 3,
      "total": 12000000
    },
    {
      "staff__staff_role__name": "Qorovul",
      "count": 2,
      "total": 6000000
    }
  ],
  "by_status": {
    "paid": 12,
    "pending": 3
  }
}
```

## Frontend Integration

### React Query Misollari

#### 1. Rollar ro'yxatini olish

```typescript
import { useQuery } from '@tanstack/react-query';

interface StaffRole {
  id: string; // UUID
  name: string;
  code: string;
  branch: string; // UUID
  branch_name: string;
  is_active: boolean;
  staff_count: number;
}

const useStaffRoles = (branchId: string) => {
  return useQuery<StaffRole[]>({
    queryKey: ['staff-roles', branchId],
    queryFn: async () => {
      const res = await fetch(`/api/v1/hr/roles/?branch=${branchId}`);
      const data = await res.json();
      return data.results;
    },
  });
};

// Component
function RolesPage() {
  const { activeBranchId } = useBranch();
  const { data: roles, isLoading } = useStaffRoles(activeBranchId);
  
  if (isLoading) return <Spinner />;
  
  return (
    <div>
      {roles?.map(role => (
        <RoleCard key={role.id} role={role} />
      ))}
    </div>
  );
}
```

#### 2. Xodimlar ro'yxati va filter

```typescript
interface StaffProfile {
  id: string; // UUID
  user_name: string;
  branch_name: string;
  role_name: string;
  base_salary: number;
  current_balance: number;
  status: string;
}

interface StaffFilters {
  branch?: string; // UUID
  staff_role?: string; // UUID
  status?: string;
  search?: string;
}

const useStaffList = (filters: StaffFilters) => {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.append(key, String(value));
  });
  
  return useQuery<StaffProfile[]>({
    queryKey: ['staff-list', filters],
    queryFn: async () => {
      const res = await fetch(`/api/v1/hr/staff/?${params}`);
      const data = await res.json();
      return data.results;
    },
  });
};

// Component
function StaffList() {
  const [filters, setFilters] = useState<StaffFilters>({});
  const { data: staff, isLoading } = useStaffList(filters);
  
  return (
    <div>
      <StaffFilters filters={filters} onChange={setFilters} />
      <StaffTable data={staff} loading={isLoading} />
    </div>
  );
}
```

#### 3. Balans tranzaksiyasi yaratish

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';

interface CreateTransactionInput {
  transaction_type: string;
  amount: number;
  description: string;
  reference?: string;
}

const useCreateTransaction = (staffId: string) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (input: CreateTransactionInput) => {
      const res = await fetch(`/api/v1/hr/staff/${staffId}/create_transaction/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(input),
      });
      return res.json();
    },
    onSuccess: () => {
      // Invalidate queries to refetch
      queryClient.invalidateQueries({ queryKey: ['staff-detail', staffId] });
      queryClient.invalidateQueries({ queryKey: ['staff-transactions', staffId] });
    },
  });
};

// Component
function CreateTransactionModal({ staffId }: { staffId: string }) {
  const { mutate, isPending } = useCreateTransaction(staffId);
  
  const handleSubmit = (data: CreateTransactionInput) => {
    mutate(data, {
      onSuccess: () => {
        toast.success('Tranzaksiya muvaffaqiyatli yaratildi');
        closeModal();
      },
    });
  };
  
  return <TransactionForm onSubmit={handleSubmit} loading={isPending} />;
}
```

#### 4. Bulk maosh to'lovlari

```typescript
interface BulkPaymentInput {
  month: string;
  payments: Array<{
    staff_id: string; // UUID
    amount: number;
    payment_date: string;
    payment_method: string;
    notes?: string;
  }>;
}

const useBulkSalaryPayments = () => {
  return useMutation({
    mutationFn: async (input: BulkPaymentInput) => {
      const res = await fetch('/api/v1/hr/salaries/bulk/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(input),
      });
      return res.json();
    },
  });
};

// Component
function BulkPaymentPage() {
  const { mutate, isPending } = useBulkSalaryPayments();
  const [selectedStaff, setSelectedStaff] = useState<string[]>([]); // UUID array
  
  const handleBulkPayment = () => {
    const payments = selectedStaff.map(staffId => ({
      staff_id: staffId,
      amount: getStaffSalary(staffId),
      payment_date: new Date().toISOString().split('T')[0],
      payment_method: 'bank_transfer',
    }));
    
    mutate({
      month: getCurrentMonth(),
      payments,
    }, {
      onSuccess: (data) => {
        toast.success(`${data.total_payments} ta to'lov navbatga qo'shildi`);
      },
    });
  };
  
  return (
    <div>
      <StaffSelector selected={selectedStaff} onChange={setSelectedStaff} />
      <Button onClick={handleBulkPayment} loading={isPending}>
        To'lovlarni amalga oshirish
      </Button>
    </div>
  );
}
```

### State Management

Branch context bilan integratsiya:

```typescript
// contexts/BranchContext.tsx
export const BranchProvider = ({ children }) => {
  const [activeBranchId, setActiveBranchId] = useState<string | null>(null); // UUID
  
  return (
    <BranchContext.Provider value={{ activeBranchId, setActiveBranchId }}>
      {children}
    </BranchContext.Provider>
  );
};

// hooks/useStaff.ts
export const useStaff = () => {
  const { activeBranchId } = useBranch();
  
  return useQuery({
    queryKey: ['staff', activeBranchId],
    queryFn: () => fetchStaff(activeBranchId),
    enabled: !!activeBranchId, // Only fetch when branch is selected
  });
};
```

## Permissions & Security

### Required Permissions

- **Rollarni boshqarish:** `manage_staff_roles` yoki `branch_admin`
- **Xodimlarni ko'rish:** `view_staff`
- **Xodimlarni yaratish/tahrirlash:** `manage_staff` yoki `branch_admin`
- **Maoshni yangilash:** `manage_salary` yoki `branch_admin`
- **Tranzaksiya yaratish:** `manage_balance` yoki `branch_admin`
- **Maosh to'lovlari:** `manage_salary_payments` yoki `branch_admin`

Frontend'da permissionlarni tekshirish:

```typescript
const { user } = useAuth();

const canManageStaff = user?.permissions?.includes('manage_staff');
const isBranchAdmin = user?.role === 'branch_admin';

if (canManageStaff || isBranchAdmin) {
  // Show edit buttons
}
```

## Validation & Constraints

1. **StaffRole:**
   - `code` unique per branch
   - `salary_range_min <= salary_range_max`

2. **StaffProfile:**
   - `user-branch` combination unique
   - `base_salary >= 0`

3. **BalanceTransaction:**
   - `amount > 0` (always positive, direction determined by type)
   - Atomic operations via `select_for_update()`

4. **SalaryPayment:**
   - `staff-month` combination unique
   - `amount > 0`

## Error Handling

### Common Errors

```json
{
  "error": "Bu foydalanuvchi uchun bu filialda allaqachon xodim profili mavjud."
}
```

```json
{
  "error": "Maosh minimal qiymatdan (3,000,000) kam bo'lishi mumkin emas."
}
```

```json
{
  "error": "Bu oy uchun maosh allaqachon to'langan"
}
```

Frontend'da error handling:

```typescript
mutate(data, {
  onError: (error: any) => {
    const message = error.response?.data?.error || 'Xatolik yuz berdi';
    toast.error(message);
  },
});
```

## Celery Tasks

### Background Tasks

1. **process_bulk_salary_payments** - Bulk maosh to'lovlarini asinxron ishlatish
2. **reconcile_staff_balances** - Balanslarni tranzaksiyalar bilan solishtirish (kunlik)
3. **generate_monthly_salary_report** - Oylik hisobotni yaratish

### Task Status

Celery task statusini tekshirish uchun Django Celery Results API'dan foydalaning:

```python
from celery.result import AsyncResult

task = AsyncResult(task_id)
status = task.status  # PENDING, STARTED, SUCCESS, FAILURE
result = task.result if task.successful() else None
```

## Best Practices

1. **Balans o'zgarishlari faqat BalanceService orqali:**
   ```python
   # ✅ Correct
   BalanceService.apply_transaction(...)
   
   # ❌ Wrong
   staff.current_balance += amount
   staff.save()
   ```

2. **Bulk operatsiyalar uchun Celery ishlatish:**
   - 10+ to'lovlar uchun bulk endpoint
   - Real-time feedback uchun WebSocket

3. **Filial context:**
   - Har doim `branch` filter qo'llang
   - URL'da yoki query param'da branch ID o'tkazing

4. **Optimistic vs Pessimistic updates:**
   - Balans/maosh - pessimistic (refetch after mutation)
   - UI state (filters, sorting) - optimistic

5. **Cache invalidation:**
   ```typescript
   onSuccess: () => {
     queryClient.invalidateQueries({ queryKey: ['staff'] });
     queryClient.invalidateQueries({ queryKey: ['transactions'] });
   }
   ```

## Migration Strategy

### Mavjud BranchMembership'dan HR'ga o'tish

1. **Phase 1:** HR modellari yaratildi, BranchMembership saqlanadi
2. **Phase 2:** Yangi xodimlar uchun StaffProfile yaratish
3. **Phase 3:** Eski ma'lumotlarni migrate qilish (data migration)
4. **Phase 4:** BranchMembership'dagi salary/balance fieldlarini deprecate qilish

Data migration script:

```python
# apps/hr/management/commands/migrate_staff_profiles.py
from django.core.management.base import BaseCommand
from apps.branch.models import BranchMembership
from apps.hr.models import StaffProfile, StaffRole
from apps.hr.choices import EmploymentType, StaffStatus

class Command(BaseCommand):
    help = 'Migrate existing BranchMembership data to StaffProfile'

    def handle(self, *args, **options):
        migrated = 0
        skipped = 0
        
        for membership in BranchMembership.objects.filter(deleted_at__isnull=True):
            # Skip if already has staff profile
            if hasattr(membership, 'staff_profile'):
                skipped += 1
                continue
            
            # Get or create role for this membership
            role_mapping = {
                'teacher': ('O\'qituvchi', ['view_grades', 'edit_attendance']),
                'student': ('O\'quvchi', ['view_grades', 'view_schedule']),
                'parent': ('Ota-ona', ['view_student_grades']),
                'branch_admin': ('Filial admin', ['manage_staff', 'manage_finance']),
            }
            
            role_info = role_mapping.get(membership.role, ('Xodim', []))
            role, _ = StaffRole.objects.get_or_create(
                branch=membership.branch,
                code=membership.role,
                defaults={
                    'name': role_info[0],
                    'permissions': role_info[1]
                }
            )
            
            # Create staff profile
            StaffProfile.objects.create(
                user=membership.user,
                branch=membership.branch,
                membership=membership,
                staff_role=role,
                employment_type=EmploymentType.FULL_TIME,
                hire_date=membership.created_at.date(),
                base_salary=getattr(membership, 'monthly_salary', 0),
                current_balance=getattr(membership, 'balance', 0),
                status=StaffStatus.ACTIVE
            )
            migrated += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Migration complete: {migrated} migrated, {skipped} skipped'
            )
        )
```

Ishlatish:
```bash
docker compose exec django python manage.py migrate_staff_profiles
```

## Monitoring & Logging

### Key Metrics

- Total staff per branch
- Active vs inactive staff
- Average salary by role
- Balance transaction volume
- Failed payment count

### Logs

```python
import logging
logger = logging.getLogger('apps.hr')

logger.info(f"Created staff profile {profile.id} for {profile.user}")
logger.warning(f"Balance discrepancy for staff {staff.id}: {diff}")
logger.error(f"Failed salary payment: {e}")
```

Frontend metrics:

```typescript
// Track API errors
useEffect(() => {
  if (isError) {
    analytics.track('api_error', {
      endpoint: '/api/v1/hr/staff/',
      error: error.message,
    });
  }
}, [isError]);
```

## Support & Troubleshooting

### Common Issues

**Issue:** Balans tranzaksiyasi yaratilmayapti
**Solution:** `status='paid'` qilib SalaryPayment save qiling, signal avtomatik tranzaksiya yaratadi.

**Issue:** Bulk payment task muvaffaqiyatsiz
**Solution:** Celery worker logs'ni tekshiring: `docker compose logs celery`

**Issue:** Frontend'da balans yangilanmayapti
**Solution:** Mutation'dan keyin `queryClient.invalidateQueries()` chaqirilganini tekshiring.

---

**Version:** 1.0.0  
**Last Updated:** 2024-12-11  
**Maintainer:** Mendeleyev Backend Team
