# RBAC, Salary va Balance API Reference

Bu hujjat frontend developerlar uchun Role, Salary va Balance API-larini qanday ishlatishni tushuntiradi.

## Umumiy ko'rinish

Mendeleyev Backend endi quyidagi yangi imkoniyatlarga ega:

1. **Role Model** — Har bir filial uchun konfiguratsiyalanadigan rollar (maosh va ruxsatlar bilan)
2. **Balance Management** — Har bir xodimning balansi (ish haqini ko'rish va boshqarish)
3. **Audit Trail** — Kim nima yaratdi/o'zgartirdi (created_by, updated_by)

## /auth/me Endpoint Yangilanishi

`GET /api/v1/auth/me/` endpoint endi quyidagi qo'shimcha maydonlarni qaytaradi:

```json
{
  "user": {...},
  "profile": {...},
  "current_branch": {
    "branch_id": "<uuid>",
    "branch_name": "Alpha School",
    "branch_type": "school",
    "branch_status": "active",
    "role": "teacher",
    "effective_role": "Math Teacher",
    "role_ref_id": "<uuid>",
    "salary": "5000000.00",
    "balance": "1500000.00",
    "title": "Senior Teacher",
    "role_data": {...}
  },
  "memberships": [
    {
      "branch_id": "<uuid>",
      "branch_name": "Alpha School",
      "role": "teacher",
      "effective_role": "Math Teacher",
      "role_ref_id": "<uuid>",
      "salary": "5000000.00",
      "balance": "1500000.00",
      "title": "Senior Teacher",
      "role_data": {...}
    }
  ],
  "auth_state": "READY"
}
```

### Yangi maydonlar

- **`effective_role`** (string) — Samarali rol nomi. Agar `role_ref` mavjud bo'lsa, `role_ref.name`, aks holda `role` maydoni.
- **`role_ref_id`** (UUID, nullable) — Role modeliga havola. Agar mavjud bo'lsa, bu yangi tizim ishlatilmoqda.
- **`salary`** (decimal, nullable) — Xodimning maoshi. `role_ref` dan olinadi.
- **`balance`** (decimal) — Xodimning balansi (so'm). Ish haqini ko'rish va boshqarish uchun.

## Role CRUD API

### Rollar ro'yxati

**GET** `/api/branches/{branch_id}/roles/`

```typescript
interface Role {
  id: string;
  name: string;
  branch: string | null;
  branch_name: string | null;
  salary_type: 'monthly' | 'hourly' | 'per_item';
  monthly_salary: string;
  hourly_rate: string | null;
  per_item_rate: string | null;
  salary: number; // Computed field
  permissions: Record<string, string[]>;
  description: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
```

**Example Request:**
```typescript
const response = await fetch('/api/branches/{branch_id}/roles/', {
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'X-Branch-Id': branchId
  }
});
const roles: Role[] = await response.json();
```

### Yangi rol yaratish

**POST** `/api/branches/{branch_id}/roles/`

**Permissions:**
- SuperAdmin: istalgan filialga rol qo'sha oladi
- BranchAdmin: faqat o'z filialiga rol qo'sha oladi

**Request:**
```json
{
  "name": "Director",
  "salary_type": "monthly",
  "monthly_salary": "5000000",
  "permissions": {
    "academic": ["view_grades", "edit_grades"],
    "finance": ["view_payments"]
  },
  "description": "Maktab direktori",
  "is_active": true
}
```

**Example:**
```typescript
const newRole = {
  name: "Director",
  salary_type: "monthly",
  monthly_salary: "5000000",
  permissions: {
    academic: ["view_grades", "edit_grades"],
    finance: ["view_payments"]
  },
  description: "Maktab direktori",
  is_active: true
};

const response = await fetch(`/api/branches/${branchId}/roles/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json',
    'X-Branch-Id': branchId
  },
  body: JSON.stringify(newRole)
});
const role: Role = await response.json();
```

### Rolni tahrirlash

**PATCH** `/api/branches/{branch_id}/roles/{role_id}/`

**Request:**
```json
{
  "monthly_salary": "6000000",
  "is_active": false
}
```

### Rolni o'chirish

**DELETE** `/api/branches/{branch_id}/roles/{role_id}/`

## Membership Balance Management

### A'zoliklar ro'yxati

**GET** `/api/branches/{branch_id}/memberships/`

**Response:**
```json
[
  {
    "id": "<uuid>",
    "user": "<uuid>",
    "user_phone": "+998901234567",
    "user_name": "John Doe",
    "branch": "<uuid>",
    "branch_name": "Alpha School",
    "role": "teacher",
    "role_ref": "<uuid>",
    "role_name": "Math Teacher",
    "effective_role": "Math Teacher",
    "title": "Senior Teacher",
    "balance": "1500000.00",
    "salary": "5000000.00",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
]
```

### Balansni yangilash

**POST** `/api/branches/{branch_id}/memberships/{membership_id}/balance/`

**Permissions:**
- SuperAdmin: istalgan a'zolikning balansini yangilay oladi
- BranchAdmin: faqat o'z filialidagi a'zoliklarning balansini yangilay oladi

**Request:**
```json
{
  "amount": "500000.00",
  "note": "Ish haqi to'lovi"
}
```

- `amount` musbat bo'lsa — balansga qo'shadi
- `amount` manfiy bo'lsa — balansdan ayiradi (balans yetarli bo'lishi kerak)

**Example:**
```typescript
// Balansga qo'shish
const addBalance = async (membershipId: string, amount: number, note: string) => {
  const response = await fetch(
    `/api/branches/${branchId}/memberships/${membershipId}/balance/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
        'X-Branch-Id': branchId
      },
      body: JSON.stringify({
        amount: amount.toString(),
        note
      })
    }
  );
  return await response.json();
};

// Balansdan ayirish
const subtractBalance = async (membershipId: string, amount: number, note: string) => {
  return addBalance(membershipId, -amount, note);
};
```

## Frontend UI Misollari

### 1. Xodim Profilida Maosh va Balans Ko'rsatish

```tsx
function EmployeeProfile({ membership }) {
  return (
    <div>
      <h2>{membership.user_name}</h2>
      <p>Rol: {membership.effective_role}</p>
      <p>Oylik maosh: {formatCurrency(membership.salary)}</p>
      <p>Balans: {formatCurrency(membership.balance)}</p>
    </div>
  );
}
```

### 2. Admin Panel: Rollar Boshqaruvi

```tsx
function RolesManagement({ branchId }) {
  const [roles, setRoles] = useState<Role[]>([]);
  
  useEffect(() => {
    fetchRoles(branchId).then(setRoles);
  }, [branchId]);
  
  const createRole = async (roleData) => {
    const newRole = await createRoleAPI(branchId, roleData);
    setRoles([...roles, newRole]);
  };
  
  return (
    <div>
      <h2>Rollar</h2>
      <RoleForm onSubmit={createRole} />
      <RoleList roles={roles} />
    </div>
  );
}
```

### 3. Balans Boshqaruvi

```tsx
function BalanceManagement({ membership }) {
  const [amount, setAmount] = useState('');
  const [note, setNote] = useState('');
  
  const handleAddBalance = async () => {
    await updateBalance(membership.branch, membership.id, parseFloat(amount), note);
    // Refresh membership data
  };
  
  const handleSubtractBalance = async () => {
    await updateBalance(membership.branch, membership.id, -parseFloat(amount), note);
    // Refresh membership data
  };
  
  return (
    <div>
      <h3>Balans: {formatCurrency(membership.balance)}</h3>
      <input
        type="number"
        value={amount}
        onChange={(e) => setAmount(e.target.value)}
        placeholder="Summa"
      />
      <input
        type="text"
        value={note}
        onChange={(e) => setNote(e.target.value)}
        placeholder="Sabab"
      />
      <button onClick={handleAddBalance}>Qo'shish</button>
      <button onClick={handleSubtractBalance}>Ayirish</button>
    </div>
  );
}
```

### 4. Salary Type Selector

```tsx
function RoleForm({ onSubmit }) {
  const [salaryType, setSalaryType] = useState('monthly');
  
  return (
    <form onSubmit={onSubmit}>
      <select value={salaryType} onChange={(e) => setSalaryType(e.target.value)}>
        <option value="monthly">Oylik</option>
        <option value="hourly">Soatlik</option>
        <option value="per_item">Har bir uchun</option>
      </select>
      
      {salaryType === 'monthly' && (
        <input type="number" name="monthly_salary" placeholder="Oylik maosh" />
      )}
      {salaryType === 'hourly' && (
        <input type="number" name="hourly_rate" placeholder="Soatlik stavka" />
      )}
      {salaryType === 'per_item' && (
        <input type="number" name="per_item_rate" placeholder="Har bir uchun stavka" />
      )}
    </form>
  );
}
```

## Xatoliklar

### 403 Forbidden
- BranchAdmin boshqa filialga rol qo'shishga harakat qilganda
- BranchAdmin boshqa filialdagi balansni yangilashga harakat qilganda

### 400 Bad Request
- Balans yetarli emas (ayirishda)
- Maosh maydonlari noto'g'ri to'ldirilganda

## Eslatmalar

1. **Backward Compatibility**: Eski `role` maydoni hali ham mavjud va ishlaydi. `effective_role` yangi va eski tizimlarni birlashtiradi.

2. **Salary Calculation**: `salary` maydoni `role_ref.get_salary()` metodidan olinadi va `salary_type` ga qarab qaytaradi.

3. **Balance Updates**: Balans yangilanishi audit trail bilan qayd etiladi (`updated_by`).

4. **Permissions**: `Role.permissions` JSON formatida saqlanadi va kelajakda maktab modullarida ishlatiladi.

