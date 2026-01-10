# Branch Dashboard Statistics API

Branch adminlar uchun asosiy sahifa statistika API. Bu endpoint branch haqida to'liq ma'lumotlarni taqdim etadi.

## Endpoint

**GET** `/api/v1/branches/school/dashboard/statistics/`

## Headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | Yes | Bearer token |
| `X-Branch-ID` | UUID | Yes | Branch ID |

## Permissions

- Faqat `branch_admin` yoki `super_admin` rollariga ega foydalanuvchilar kirish huquqiga ega
- Branch a'zoligi active bo'lishi kerak

## Response

### Success (200 OK)

```json
{
  "branch_id": "550e8400-e29b-41d4-a716-446655440000",
  "branch_name": "Chilonzor filiali",
  "students": {
    "total": 150,
    "active": 145,
    "with_debt": 23,
    "total_debt_amount": 15000000
  },
  "staff": {
    "total": 18,
    "teachers": 12,
    "admins": 2,
    "other": 4
  },
  "lessons": {
    "today": 45,
    "this_week": 210,
    "completed_today": 38
  },
  "finance": {
    "total_balance": 25000000,
    "this_month_income": 75000000,
    "this_month_expenses": 50000000,
    "recent_payments_count": 145
  }
}
```

## Response Fields

### Branch Info
- `branch_id` (UUID) - Branch ID
- `branch_name` (string) - Branch nomi

### Students (O'quvchilar)
- `total` (integer) - Jami o'quvchilar soni
- `active` (integer) - Faol o'quvchilar soni
- `with_debt` (integer) - Qarzdor o'quvchilar soni
- `total_debt_amount` (integer) - Jami qarz miqdori (so'm)

### Staff (Xodimlar)
- `total` (integer) - Jami xodimlar soni (o'qituvchi, admin, boshqalar)
- `teachers` (integer) - O'qituvchilar soni
- `admins` (integer) - Adminlar soni (branch_admin + super_admin)
- `other` (integer) - Boshqa xodimlar (qorovul, oshpaz, va h.k.)

### Lessons (Darslar)
- `today` (integer) - Bugungi darslar soni
- `this_week` (integer) - Bu haftalik darslar soni (dushanbadan bugungi kungacha)
- `completed_today` (integer) - Bugun tugallangan darslar soni

### Finance (Moliya)
- `total_balance` (integer) - Branch balans (so'm)
- `this_month_income` (integer) - Joriy oy daromadi (so'm)
- `this_month_expenses` (integer) - Joriy oy xarajatlari (maosh to'lovlari) (so'm)
- `recent_payments_count` (integer) - Oxirgi 30 kundagi to'lovlar soni

## Error Responses

### 400 Bad Request
```json
{
  "error": "X-Branch-ID header is required"
}
```

### 403 Forbidden
```json
{
  "error": "Permission denied. Branch admin role required."
}
```

### 404 Not Found
```json
{
  "error": "Branch not found"
}
```

## Usage Examples

### cURL

```bash
curl -X GET \
  'http://localhost:8000/api/v1/branches/dashboard/statistics/' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'X-Branch-ID: 550e8400-e29b-41d4-a716-446655440000'
```

### JavaScript (Axios)

```javascript
import axios from 'axios';

const fetchDashboardStats = async (branchId) => {
  try {
    const response = await axios.get(
      '/api/v1/branches/dashboard/statistics/',
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Branch-ID': branchId,
        },
      }
    );
    return response.data;
  } catch (error) {
    console.error('Error fetching stats:', error);
    throw error;
  }
};
```

### Python (requests)

```python
import requests

def get_dashboard_statistics(branch_id, token):
    url = 'http://localhost:8000/api/v1/branches/dashboard/statistics/'
    headers = {
        'Authorization': f'Bearer {token}',
        'X-Branch-ID': branch_id,
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f'Error: {response.json()}')
```

## TypeScript Interface

```typescript
interface DashboardStatistics {
  branch_id: string;
  branch_name: string;
  students: {
    total: number;
    active: number;
    with_debt: number;
    total_debt_amount: number;
  };
  staff: {
    total: number;
    teachers: number;
    admins: number;
    other: number;
  };
  lessons: {
    today: number;
    this_week: number;
    completed_today: number;
  };
  finance: {
    total_balance: number;
    this_month_income: number;
    this_month_expenses: number;
    recent_payments_count: number;
  };
}
```

## React Hook Example

```typescript
import { useState, useEffect } from 'react';
import axios from 'axios';

export const useDashboardStatistics = (branchId: string) => {
  const [stats, setStats] = useState<DashboardStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        const response = await axios.get(
          '/api/v1/branches/dashboard/statistics/',
          {
            headers: {
              'X-Branch-ID': branchId,
            },
          }
        );
        setStats(response.data);
        setError(null);
      } catch (err: any) {
        setError(err.response?.data?.error || 'Failed to fetch statistics');
      } finally {
        setLoading(false);
      }
    };

    if (branchId) {
      fetchStats();
    }
  }, [branchId]);

  return { stats, loading, error };
};
```

## React Component Example

```typescript
import React from 'react';
import { useDashboardStatistics } from './hooks/useDashboardStatistics';

const DashboardPage: React.FC<{ branchId: string }> = ({ branchId }) => {
  const { stats, loading, error } = useDashboardStatistics(branchId);

  if (loading) return <div>Yuklanmoqda...</div>;
  if (error) return <div>Xato: {error}</div>;
  if (!stats) return null;

  return (
    <div className="dashboard">
      <h1>{stats.branch_name} - Asosiy Sahifa</h1>
      
      {/* O'quvchilar */}
      <div className="stats-section">
        <h2>O'quvchilar</h2>
        <div className="stats-grid">
          <StatCard 
            title="Jami o'quvchilar" 
            value={stats.students.total} 
            icon="👥"
          />
          <StatCard 
            title="Faol o'quvchilar" 
            value={stats.students.active} 
            icon="✅"
          />
          <StatCard 
            title="Qarzdorlar" 
            value={stats.students.with_debt} 
            icon="⚠️"
            alert={stats.students.with_debt > 0}
          />
          <StatCard 
            title="Jami qarz" 
            value={formatMoney(stats.students.total_debt_amount)} 
            icon="💰"
            alert={stats.students.total_debt_amount > 0}
          />
        </div>
      </div>

      {/* Xodimlar */}
      <div className="stats-section">
        <h2>Xodimlar</h2>
        <div className="stats-grid">
          <StatCard title="Jami xodimlar" value={stats.staff.total} icon="👔" />
          <StatCard title="O'qituvchilar" value={stats.staff.teachers} icon="👨‍🏫" />
          <StatCard title="Adminlar" value={stats.staff.admins} icon="👨‍💼" />
          <StatCard title="Boshqalar" value={stats.staff.other} icon="🔧" />
        </div>
      </div>

      {/* Darslar */}
      <div className="stats-section">
        <h2>Darslar</h2>
        <div className="stats-grid">
          <StatCard title="Bugungi darslar" value={stats.lessons.today} icon="📚" />
          <StatCard title="Bu hafta" value={stats.lessons.this_week} icon="📅" />
          <StatCard 
            title="Bugun tugallandi" 
            value={stats.lessons.completed_today} 
            icon="✔️"
          />
        </div>
      </div>

      {/* Moliya */}
      <div className="stats-section">
        <h2>Moliya</h2>
        <div className="stats-grid">
          <StatCard 
            title="Balans" 
            value={formatMoney(stats.finance.total_balance)} 
            icon="🏦"
          />
          <StatCard 
            title="Bu oy daromad" 
            value={formatMoney(stats.finance.this_month_income)} 
            icon="📈"
          />
          <StatCard 
            title="Bu oy xarajat" 
            value={formatMoney(stats.finance.this_month_expenses)} 
            icon="📉"
          />
          <StatCard 
            title="Oxirgi 30 kun to'lovlari" 
            value={stats.finance.recent_payments_count} 
            icon="⏳"
          />
        </div>
      </div>
    </div>
  );
};

const StatCard: React.FC<{
  title: string;
  value: string | number;
  icon: string;
  alert?: boolean;
}> = ({ title, value, icon, alert }) => (
  <div className={`stat-card ${alert ? 'alert' : ''}`}>
    <div className="icon">{icon}</div>
    <div className="content">
      <div className="title">{title}</div>
      <div className="value">{value}</div>
    </div>
  </div>
);

const formatMoney = (amount: number) => {
  return new Intl.NumberFormat('uz-UZ', {
    style: 'currency',
    currency: 'UZS',
    minimumFractionDigits: 0,
  }).format(amount);
};
```

## Notes

1. **Performance**: Query optimizatsiya qilingan, minimal database hit bilan ishlaydi
2. **Caching**: Frontend'da statistikani 5-10 daqiqa keshlash tavsiya etiladi
3. **Real-time**: Real-time yangilanish kerak bo'lsa, WebSocket yoki polling ishlatish mumkin
4. **Permissions**: Faqat branch adminlar va super adminlar kirish huquqiga ega
5. **Branch Context**: X-Branch-ID header orqali branch tanlanadi

## Related Endpoints

- [Students API](/api/v1/school/students/)
- [Staff API](/api/v1/branches/staff/)
- [Lessons API](/api/v1/school/schedule/lessons/)
- [Finance API](/api/v1/school/finance/)
