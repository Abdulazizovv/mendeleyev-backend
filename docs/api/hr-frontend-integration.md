# Staff Management API - Frontend Integration Guide

**Base URL:** `/api/branch/staff/`  
**Auth:** Bearer token required  
**Updated:** 2024-12-13

## Quick Start

### Authentication
```typescript
// Har bir request'da token qo'shing
const headers = {
  'Authorization': `Bearer ${localStorage.getItem('token')}`,
  'Content-Type': 'application/json',
};
```

### TypeScript Types

```typescript
// Core Types
interface User {
  id: string;
  first_name: string;
  last_name: string;
  phone: string;
  email: string;
}

interface Branch {
  id: string;
  name: string;
}

interface Role {
  id: string;
  name: string;
  code: string;
  salary_range_min: string;
  salary_range_max: string;
}

interface Staff {
  id: string;
  user: User;
  branch: Branch;
  role: string; // Legacy CharField
  role_ref: string | null; // UUID of Role (ForeignKey)
  role_ref_name: string | null;
  role_display: string;
  title: string;
  hire_date: string;
  termination_date: string | null;
  employment_type: 'full_time' | 'part_time' | 'contract' | 'intern';
  monthly_salary: number;
  salary: number; // Computed from get_salary()
  salary_type: 'monthly' | 'hourly' | 'per_lesson';
  hourly_rate: number | null;
  per_lesson_rate: number | null;
  balance: number;
  passport_serial: string;
  passport_number: string;
  address: string;
  emergency_contact: string;
  notes: string;
  is_active_employment: boolean;
  days_employed: number;
  years_employed: number;
  balance_status: 'positive' | 'negative' | 'zero';
  created_at: string;
}

interface StaffListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Staff[];
}

interface StaffStats {
  total_staff: number;
  active_staff: number;
  terminated_staff: number;
  by_employment_type: Array<{
    employment_type: string;
    count: number;
  }>;
  by_role: Array<{
    role__name: string;
    count: number;
  }>;
  average_salary: number;
}

interface BalanceTransaction {
  amount: number;
  transaction_type: 'salary' | 'bonus' | 'deduction' | 'advance' | 'fine';
  description: string;
}

interface SalaryPayment {
  amount: number;
  payment_method: 'cash' | 'bank_transfer' | 'card';
  payment_status: 'pending' | 'completed' | 'failed';
  notes?: string;
}
```

---

## 1. List Staff (GET /api/branch/staff/)

### React Query Hook

```typescript
import { useQuery } from '@tanstack/react-query';

interface StaffFilters {
  branch?: string;
  role?: string;
  employment_type?: string;
  status?: 'active' | 'terminated';
  search?: string;
  ordering?: string;
  page?: number;
  page_size?: number;
}

const useStaffList = (filters: StaffFilters) => {
  return useQuery<StaffListResponse>({
    queryKey: ['staff', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, String(value));
      });
      
      const response = await fetch(
        `/api/branch/staff/?${params}`,
        { headers }
      );
      
      if (!response.ok) throw new Error('Failed to fetch staff');
      return response.json();
    },
  });
};

// Component
function StaffListPage() {
  const [filters, setFilters] = useState<StaffFilters>({
    status: 'active',
    page: 1,
    page_size: 20,
  });
  
  const { data, isLoading, error } = useStaffList(filters);
  
  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error.message} />;
  
  return (
    <div>
      <h1>Xodimlar ({data?.count})</h1>
      
      {/* Filters */}
      <StaffFilters filters={filters} onChange={setFilters} />
      
      {/* List */}
      <table>
        <thead>
          <tr>
            <th>Ism</th>
            <th>Lavozim</th>
            <th>Maosh</th>
            <th>Balans</th>
            <th>Holat</th>
          </tr>
        </thead>
        <tbody>
          {data?.results.map(staff => (
            <tr key={staff.id}>
              <td>{staff.user.first_name} {staff.user.last_name}</td>
              <td>{staff.role.name}</td>
              <td>{formatCurrency(staff.salary)}</td>
              <td className={staff.balance_status}>
                {formatCurrency(staff.balance)}
              </td>
              <td>
                {staff.is_active_employment ? (
                  <Badge color="green">Faol</Badge>
                ) : (
                  <Badge color="red">Ishdan chiqqan</Badge>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      
      {/* Pagination */}
      <Pagination
        current={filters.page || 1}
        total={data?.count || 0}
        pageSize={filters.page_size || 20}
        onChange={(page) => setFilters({ ...filters, page })}
      />
    </div>
  );
}
```

### Axios Example

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: '/api/branch',
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`,
  },
});

// Get staff list
const getStaffList = async (params: StaffFilters) => {
  const { data } = await api.get<StaffListResponse>('/staff/', { params });
  return data;
};

// Usage
const staffList = await getStaffList({ status: 'active' });
```

---

## 2. Create Staff (POST /api/branch/staff/)

```typescript
interface CreateStaffInput {
  user: string;
  branch: string;
  role_ref: string; // Role UUID
  hire_date: string;
  employment_type: 'full_time' | 'part_time' | 'contract' | 'intern';
  monthly_salary: number;
  salary_type?: 'monthly' | 'hourly' | 'per_lesson';
  hourly_rate?: number;
  per_lesson_rate?: number;
  passport_serial?: string;
  passport_number?: string;
  address?: string;
  emergency_contact?: string;
  notes?: string;
}

const useCreateStaff = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: CreateStaffInput) => {
      const response = await fetch('/api/branch/staff/', {
        method: 'POST',
        headers,
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(JSON.stringify(error));
      }
      
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['staff'] });
      toast.success('Xodim muvaffaqiyatli qo\'shildi');
    },
    onError: (error: Error) => {
      const errors = JSON.parse(error.message);
      Object.entries(errors).forEach(([field, messages]) => {
        toast.error(`${field}: ${messages}`);
      });
    },
  });
};

// Component
function CreateStaffForm() {
  const createStaff = useCreateStaff();
  const { data: roles } = useRoles(); // Get available roles
  
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    
    createStaff.mutate({
      user: formData.get('user') as string,
      branch: formData.get('branch') as string,
      role: formData.get('role') as string,
      hire_date: formData.get('hire_date') as string,
      employment_type: formData.get('employment_type') as any,
      salary: Number(formData.get('salary')),
      passport_serial: formData.get('passport_serial') as string,
      passport_number: formData.get('passport_number') as string,
      address: formData.get('address') as string,
      emergency_contact: formData.get('emergency_contact') as string,
      notes: formData.get('notes') as string,
    });
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <input name="user" placeholder="User ID" required />
      <input name="branch" placeholder="Branch ID" required />
      
      <select name="role" required>
        <option value="">Lavozimni tanlang</option>
        {roles?.map(role => (
          <option key={role.id} value={role.id}>
            {role.name} ({formatCurrency(role.salary_range_min)} - {formatCurrency(role.salary_range_max)})
          </option>
        ))}
      </select>
      
      <input name="hire_date" type="date" required />
      
      <select name="employment_type" required>
        <option value="full_time">To'liq stavka</option>
        <option value="part_time">Yarim stavka</option>
        <option value="contract">Shartnoma</option>
        <option value="intern">Amaliyotchi</option>
      </select>
      
      <input name="salary" type="number" placeholder="Maosh" required />
      <input name="passport_serial" placeholder="Pasport seriya (AB)" />
      <input name="passport_number" placeholder="Pasport raqam (1234567)" />
      <textarea name="address" placeholder="Manzil" />
      <input name="emergency_contact" placeholder="Tez yordam aloqa (+998...)" />
      <textarea name="notes" placeholder="Qo'shimcha ma'lumot" />
      
      <button type="submit" disabled={createStaff.isPending}>
        {createStaff.isPending ? 'Yuklanmoqda...' : 'Qo\'shish'}
      </button>
    </form>
  );
}
```

---

## 3. Get Staff Details (GET /api/branch/staff/{id}/)

```typescript
const useStaffDetail = (staffId: string) => {
  return useQuery<Staff>({
    queryKey: ['staff', staffId],
    queryFn: async () => {
      const response = await fetch(`/api/branch/staff/${staffId}/`, { headers });
      if (!response.ok) throw new Error('Failed to fetch staff details');
      return response.json();
    },
    enabled: !!staffId,
  });
};

// Component
function StaffDetailPage({ staffId }: { staffId: string }) {
  const { data: staff, isLoading } = useStaffDetail(staffId);
  
  if (isLoading) return <LoadingSpinner />;
  if (!staff) return <NotFound />;
  
  return (
    <div>
      <h1>{staff.user.first_name} {staff.user.last_name}</h1>
      
      <InfoSection title="Umumiy ma'lumotlar">
        <InfoRow label="Telefon" value={staff.user.phone} />
        <InfoRow label="Email" value={staff.user.email} />
        <InfoRow label="Filial" value={staff.branch.name} />
        <InfoRow label="Lavozim" value={staff.role.name} />
      </InfoSection>
      
      <InfoSection title="Ish ma'lumotlari">
        <InfoRow label="Ish turi" value={staff.employment_type} />
        <InfoRow label="Ishga qabul sanasi" value={formatDate(staff.hire_date)} />
        <InfoRow label="Ish staji" value={`${staff.years_employed} yil (${staff.days_employed} kun)`} />
        <InfoRow label="Maosh" value={formatCurrency(staff.salary)} />
      </InfoSection>
      
      <InfoSection title="Moliyaviy ma'lumotlar">
        <InfoRow 
          label="Balans" 
          value={formatCurrency(staff.balance)}
          className={staff.balance_status}
        />
      </InfoSection>
      
      {staff.passport_serial && (
        <InfoSection title="Shaxsiy ma'lumotlar">
          <InfoRow label="Pasport" value={`${staff.passport_serial} ${staff.passport_number}`} />
          <InfoRow label="Manzil" value={staff.address} />
          <InfoRow label="Tez yordam aloqa" value={staff.emergency_contact} />
        </InfoSection>
      )}
    </div>
  );
}
```

---

## 4. Update Staff (PATCH /api/branch/staff/{id}/)

```typescript
interface UpdateStaffInput {
  salary?: number;
  address?: string;
  emergency_contact?: string;
  notes?: string;
  termination_date?: string | null;
}

const useUpdateStaff = (staffId: string) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: UpdateStaffInput) => {
      const response = await fetch(`/api/branch/staff/${staffId}/`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify(data),
      });
      
      if (!response.ok) throw new Error('Failed to update staff');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['staff', staffId] });
      queryClient.invalidateQueries({ queryKey: ['staff'] });
      toast.success('Ma\'lumotlar yangilandi');
    },
  });
};

// Terminate employment
const terminateEmployment = useUpdateStaff(staffId);
terminateEmployment.mutate({
  termination_date: new Date().toISOString().split('T')[0],
});
```

---

## 5. Delete Staff (DELETE /api/branch/staff/{id}/)

```typescript
const useDeleteStaff = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (staffId: string) => {
      const response = await fetch(`/api/branch/staff/${staffId}/`, {
        method: 'DELETE',
        headers,
      });
      
      if (!response.ok) throw new Error('Failed to delete staff');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['staff'] });
      toast.success('Xodim o\'chirildi');
    },
  });
};

// Usage with confirmation
function DeleteStaffButton({ staffId }: { staffId: string }) {
  const deleteStaff = useDeleteStaff();
  
  const handleDelete = () => {
    if (confirm('Rostdan ham o\'chirmoqchimisiz?')) {
      deleteStaff.mutate(staffId);
    }
  };
  
  return (
    <button onClick={handleDelete} disabled={deleteStaff.isPending}>
      O'chirish
    </button>
  );
}
```

---

## 6. Staff Statistics (GET /api/branch/staff/stats/)

```typescript
const useStaffStats = (branchId?: string) => {
  return useQuery<StaffStats>({
    queryKey: ['staff', 'stats', branchId],
    queryFn: async () => {
      const params = branchId ? `?branch=${branchId}` : '';
      const response = await fetch(`/api/branch/staff/stats/${params}`, { headers });
      if (!response.ok) throw new Error('Failed to fetch stats');
      return response.json();
    },
  });
};

// Component
function StaffDashboard({ branchId }: { branchId: string }) {
  const { data: stats } = useStaffStats(branchId);
  
  return (
    <div>
      <StatsGrid>
        <StatCard
          title="Jami xodimlar"
          value={stats?.total_staff}
          icon={<UsersIcon />}
        />
        <StatCard
          title="Faol xodimlar"
          value={stats?.active_staff}
          icon={<UserCheckIcon />}
          color="green"
        />
        <StatCard
          title="O'rtacha maosh"
          value={formatCurrency(stats?.average_salary)}
          icon={<DollarIcon />}
        />
      </StatsGrid>
      
      <Chart
        title="Ish turi bo'yicha"
        data={stats?.by_employment_type}
      />
      
      <Chart
        title="Lavozim bo'yicha"
        data={stats?.by_role}
      />
    </div>
  );
}
```

---

## 7. Add Balance Transaction (POST /api/branch/staff/{id}/add_balance/)

```typescript
const useAddBalance = (staffId: string) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: BalanceTransaction) => {
      const response = await fetch(
        `/api/branch/staff/${staffId}/add_balance/`,
        {
          method: 'POST',
          headers,
          body: JSON.stringify(data),
        }
      );
      
      if (!response.ok) throw new Error('Failed to add balance');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['staff', staffId] });
      toast.success('Balans yangilandi');
    },
  });
};

// Component
function AddBalanceModal({ staffId }: { staffId: string }) {
  const addBalance = useAddBalance(staffId);
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const formData = new FormData(e.target as HTMLFormElement);
    
    addBalance.mutate({
      amount: Number(formData.get('amount')),
      transaction_type: formData.get('transaction_type') as any,
      description: formData.get('description') as string,
    });
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <select name="transaction_type" required>
        <option value="salary">Maosh</option>
        <option value="bonus">Bonus</option>
        <option value="deduction">Chegirma</option>
        <option value="advance">Avans</option>
        <option value="fine">Jarima</option>
      </select>
      
      <input
        name="amount"
        type="number"
        placeholder="Summa"
        required
      />
      
      <textarea
        name="description"
        placeholder="Izoh"
        required
      />
      
      <button type="submit" disabled={addBalance.isPending}>
        Qo'shish
      </button>
    </form>
  );
}
```

---

## 8. Record Salary Payment (POST /api/branch/staff/{id}/pay_salary/)

```typescript
const usePaySalary = (staffId: string) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: SalaryPayment) => {
      const response = await fetch(
        `/api/branch/staff/${staffId}/pay_salary/`,
        {
          method: 'POST',
          headers,
          body: JSON.stringify(data),
        }
      );
      
      if (!response.ok) throw new Error('Failed to record payment');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['staff', staffId] });
      toast.success('To\'lov qayd qilindi');
    },
  });
};

// Component
function PaySalaryForm({ staff }: { staff: Staff }) {
  const paySalary = usePaySalary(staff.id);
  
  const handlePay = () => {
    paySalary.mutate({
      amount: Number(staff.salary),
      payment_method: 'bank_transfer',
      payment_status: 'completed',
      notes: `${new Date().toLocaleString('uz', { month: 'long' })} oyi ish haqi`,
    });
  };
  
  return (
    <div>
      <h3>Oylik to'lash: {staff.user.first_name} {staff.user.last_name}</h3>
      <p>Maosh: {formatCurrency(staff.salary)}</p>
      <p>Joriy balans: {formatCurrency(staff.balance)}</p>
      
      <button onClick={handlePay} disabled={paySalary.isPending}>
        {paySalary.isPending ? 'Kutilmoqda...' : 'To\'lash'}
      </button>
    </div>
  );
}
```

---

## Error Handling

```typescript
// Global error handler
const handleApiError = (error: any) => {
  if (error.response) {
    // Server responded with error
    const status = error.response.status;
    const data = error.response.data;
    
    if (status === 401) {
      // Unauthorized - redirect to login
      localStorage.removeItem('token');
      window.location.href = '/login';
    } else if (status === 403) {
      toast.error('Ruxsat yo\'q');
    } else if (status === 404) {
      toast.error('Ma\'lumot topilmadi');
    } else if (status === 400) {
      // Validation errors
      Object.entries(data).forEach(([field, messages]) => {
        toast.error(`${field}: ${messages}`);
      });
    } else {
      toast.error('Server xatosi');
    }
  } else if (error.request) {
    // No response from server
    toast.error('Server javob bermadi');
  } else {
    toast.error(error.message);
  }
};

// Usage with React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      onError: handleApiError,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
    mutations: {
      onError: handleApiError,
    },
  },
});
```

---

## Utility Functions

```typescript
// Format currency
const formatCurrency = (amount: string | number) => {
  return new Intl.NumberFormat('uz-UZ', {
    style: 'currency',
    currency: 'UZS',
    minimumFractionDigits: 0,
  }).format(Number(amount));
};

// Format date
const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString('uz-UZ', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
};

// Get employment type label
const getEmploymentTypeLabel = (type: string) => {
  const labels = {
    full_time: 'To\'liq stavka',
    part_time: 'Yarim stavka',
    contract: 'Shartnoma',
    intern: 'Amaliyotchi',
  };
  return labels[type as keyof typeof labels] || type;
};

// Get balance status color
const getBalanceStatusColor = (status: string) => {
  const colors = {
    positive: 'green',
    negative: 'red',
    zero: 'gray',
  };
  return colors[status as keyof typeof colors] || 'gray';
};
```

---

## Complete Example: Staff Management Page

```typescript
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

function StaffManagementPage() {
  const [filters, setFilters] = useState({
    status: 'active',
    page: 1,
  });
  
  const [selectedStaff, setSelectedStaff] = useState<string | null>(null);
  
  const queryClient = useQueryClient();
  
  // Queries
  const { data: staffList, isLoading } = useStaffList(filters);
  const { data: stats } = useStaffStats();
  const { data: staffDetail } = useStaffDetail(selectedStaff || '');
  
  // Mutations
  const createStaff = useCreateStaff();
  const updateStaff = useUpdateStaff(selectedStaff || '');
  const deleteStaff = useDeleteStaff();
  
  return (
    <div className="staff-management">
      {/* Header with stats */}
      <header>
        <h1>Xodimlar Boshqaruvi</h1>
        <StatsOverview stats={stats} />
      </header>
      
      {/* Filters */}
      <div className="filters">
        <SearchInput
          value={filters.search}
          onChange={(search) => setFilters({ ...filters, search })}
        />
        <Select
          value={filters.status}
          onChange={(status) => setFilters({ ...filters, status })}
          options={[
            { value: 'active', label: 'Faol' },
            { value: 'terminated', label: 'Ishdan chiqqan' },
          ]}
        />
      </div>
      
      {/* Staff list */}
      <div className="content">
        <div className="list">
          {isLoading ? (
            <LoadingSpinner />
          ) : (
            <StaffTable
              data={staffList?.results}
              onSelect={setSelectedStaff}
              selected={selectedStaff}
            />
          )}
        </div>
        
        {/* Detail panel */}
        {selectedStaff && staffDetail && (
          <div className="detail">
            <StaffDetail
              staff={staffDetail}
              onUpdate={(data) => updateStaff.mutate(data)}
              onDelete={() => {
                if (confirm('Rostdan ham o\'chirmoqchimisiz?')) {
                  deleteStaff.mutate(selectedStaff, {
                    onSuccess: () => setSelectedStaff(null),
                  });
                }
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default StaffManagementPage;
```

---

## Best Practices

1. **Always invalidate queries after mutations**
   ```typescript
   onSuccess: () => {
     queryClient.invalidateQueries({ queryKey: ['staff'] });
   }
   ```

2. **Use optimistic updates for better UX**
   ```typescript
   onMutate: async (newData) => {
     await queryClient.cancelQueries({ queryKey: ['staff'] });
     const previous = queryClient.getQueryData(['staff']);
     queryClient.setQueryData(['staff'], (old) => [...old, newData]);
     return { previous };
   },
   onError: (err, variables, context) => {
     queryClient.setQueryData(['staff'], context.previous);
   },
   ```

3. **Handle loading and error states**
   ```typescript
   if (isLoading) return <Spinner />;
   if (error) return <ErrorAlert />;
   ```

4. **Debounce search inputs**
   ```typescript
   const [search, setSearch] = useState('');
   const debouncedSearch = useDebounce(search, 500);
   const { data } = useStaffList({ search: debouncedSearch });
   ```

5. **Cache and revalidate appropriately**
   ```typescript
   staleTime: 5 * 60 * 1000, // 5 minutes
   cacheTime: 10 * 60 * 1000, // 10 minutes
   ```
