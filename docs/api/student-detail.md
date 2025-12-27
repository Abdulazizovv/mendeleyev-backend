# Student Detail API - To'liq Hujjat

Bu hujjatda o'quvchi detail (tafsilotlar) API'si to'liq tushuntiriladi.

## Versiya Ma'lumotlari

### v2.2.0 (2025-12-23)
**Yangiliklar:**
- ✅ **Oxirgi tranzaksiyalar** (`recent_transactions`)
  - Oxirgi 10 ta tranzaksiya
  - To'liq employee ma'lumotlari (avatar, role)
  - To'liq kategori va kassa ma'lumotlari
- ✅ Context flag: `include_recent_transactions: true`
- 📝 To'liq ma'lumot: [transactions.md](./transactions.md)

### v2.1.0 (2025-12-23)
- Abonement sanalarini qo'lda belgilash
- Chegirmalar tizimi
- Moslashuvchan sana boshqaruvi

### v2.0.0 (2025-01-20)
- Student Detail API
- Subscriptions va Payment Due
- Relatives ma'lumotlari

## Mundarija

1. [Endpoint Ma'lumotlari](#endpoint-malumotlari)
2. [Response Strukturasi](#response-strukturasi)
3. [Ma'lumot Qismlari](#malumot-qismlari)
4. [Frontend Integratsiya](#frontend-integratsiya)
5. [Misollar](#misollar)

---

## Endpoint Ma'lumotlari

### Student Detail

**URL:** `GET /api/v1/school/students/{student_id}/`

**Authentication:** JWT Token (required)

**Permissions:** 
- Super Admin
- Branch Admin (o'z filialidagi o'quvchilar)
- Teacher (o'z sinfidagi o'quvchilar)

**Response Status:**
- `200 OK` - Muvaffaqiyatli
- `404 NOT FOUND` - O'quvchi topilmadi
- `403 FORBIDDEN` - Ruxsat yo'q

---

## Response Strukturasi

```typescript
interface StudentDetailResponse {
  // Asosiy ma'lumotlar
  id: string;
  personal_number: string;
  user_id: string;
  phone_number: string;
  first_name: string;
  last_name: string;
  middle_name: string;
  full_name: string;
  email: string;
  
  // Filial ma'lumotlari
  branch_id: string;
  branch_name: string;
  
  // Shaxsiy ma'lumotlar
  gender: 'male' | 'female' | 'other' | 'unspecified';
  status: 'active' | 'archived' | 'suspended' | 'graduated' | 'transferred';
  status_display: string;
  date_of_birth: string | null;
  address: string;
  
  // Rasmlar
  avatar: string | null;
  avatar_url: string | null;
  birth_certificate: string | null;
  birth_certificate_url: string | null;
  
  // Qo'shimcha
  additional_fields: Record<string, any> | null;
  
  // Sinf ma'lumotlari
  current_class: {
    id: string;
    name: string;
    academic_year: string;
  } | null;
  
  // Yaqinlar
  relatives_count: number;
  relatives: Relative[] | null;
  
  // Moliyaviy ma'lumotlar
  balance: BalanceDetails;
  
  // Abonement ma'lumotlari (YANGI)
  subscriptions: Subscription[] | null;
  
  // To'lov xulosa (YANGI)
  payment_due: PaymentDueSummary | null;
  
  // Oxirgi tranzaksiyalar (YANGI v2.2.0)
  recent_transactions: Transaction[] | null;
  
  // Timestamps
  created_at: string;
  updated_at: string;
}
```

---

## Ma'lumot Qismlari

### 1. Asosiy Ma'lumotlar

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "personal_number": "TAS-25-0001",
  "user_id": "660e8400-e29b-41d4-a716-446655440000",
  "phone_number": "+998901234567",
  "first_name": "Ali",
  "last_name": "Valiyev",
  "middle_name": "Olim o'g'li",
  "full_name": "Ali Olim o'g'li Valiyev",
  "email": "ali@example.com",
  "branch_id": "770e8400-e29b-41d4-a716-446655440000",
  "branch_name": "Markaziy filial"
}
```

### 2. Sinf Ma'lumotlari

```json
{
  "current_class": {
    "id": "880e8400-e29b-41d4-a716-446655440000",
    "name": "5-A",
    "academic_year": "2024-2025"
  }
}
```

### 3. Yaqinlar (Relatives)

**Context flag:** `include_relatives: true` (detail view'da avtomatik)

```json
{
  "relatives_count": 2,
  "relatives": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440000",
      "relationship_type": "father",
      "relationship_type_display": "Otasi",
      "first_name": "Olim",
      "middle_name": "Karim o'g'li",
      "last_name": "Valiyev",
      "full_name": "Olim Karim o'g'li Valiyev",
      "phone_number": "+998901234568",
      "email": "olim@example.com",
      "gender": "male",
      "date_of_birth": "1985-03-15",
      "address": "Toshkent shahri, Chilonzor tumani",
      "workplace": "IT Kompaniya",
      "position": "Dasturchi",
      "passport_number": "AB1234567",
      "photo": "/media/relatives/photo.jpg",
      "photo_url": "http://localhost:8000/media/relatives/photo.jpg",
      "is_primary_contact": true,
      "is_guardian": true,
      "additional_info": {},
      "notes": "",
      "created_at": "2025-01-01T10:00:00Z",
      "updated_at": "2025-01-15T10:00:00Z"
    },
    {
      "id": "aa0e8400-e29b-41d4-a716-446655440000",
      "relationship_type": "mother",
      "relationship_type_display": "Onasi",
      "full_name": "Nodira Karim qizi Valiyeva",
      "phone_number": "+998901234569",
      "is_primary_contact": false,
      "is_guardian": true,
      "...": "..."
    }
  ]
}
```

**Relationship Types:**
- `father` - Otasi
- `mother` - Onasi
- `brother` - Akasi/Ukasi
- `sister` - Opasi/Singili
- `guardian` - Vasiy
- `grandfather` - Bobosi
- `grandmother` - Buvisi
- `uncle` - Amakisi/Tog'asi
- `aunt` - Xolasi/Ammasi
- `other` - Boshqa

### 4. Moliyaviy Ma'lumotlar (Balance)

**Context flag:** `include_finance_details: true` (detail view'da avtomatik)

```json
{
  "balance": {
    "id": "bb0e8400-e29b-41d4-a716-446655440000",
    "balance": 2500000,
    "notes": "To'lovlar muntazam",
    "updated_at": "2025-01-20T10:00:00Z",
    "transactions_summary": {
      "total_income": 3000000,
      "total_expense": 500000,
      "net_balance": 2500000,
      "transactions_count": 6
    },
    "payments_summary": {
      "total_payments": 3000000,
      "payments_count": 6,
      "last_payment": {
        "id": "cc0e8400-e29b-41d4-a716-446655440000",
        "amount": 500000,
        "date": "2025-01-15T10:00:00Z",
        "period": "monthly",
        "period_display": "Oylik"
      }
    }
  }
}
```

**Agar balance bo'lmasa:**
```json
{
  "balance": {
    "id": null,
    "balance": 0,
    "notes": "",
    "updated_at": null,
    "transactions_summary": {
      "total_income": 0,
      "total_expense": 0,
      "net_balance": 0,
      "transactions_count": 0
    },
    "payments_summary": {
      "total_payments": 0,
      "payments_count": 0,
      "last_payment": null
    }
  }
}
```

### 5. Abonement Ma'lumotlari (Subscriptions) - YANGI! 🎉

**Context flag:** `include_subscriptions: true` (detail view'da avtomatik)

**Chegirmasiz abonement:**
```json
{
  "subscriptions": [
    {
      "id": "dd0e8400-e29b-41d4-a716-446655440000",
      "subscription_plan": {
        "id": "ee0e8400-e29b-41d4-a716-446655440000",
        "name": "5-sinf (oylik)",
        "price": 500000,
        "period": "monthly",
        "period_display": "Oylik"
      },
      "discount": null,
      "is_active": true,
      "start_date": "2025-01-01",
      "end_date": null,
      "next_payment_date": "2025-02-01",
      "last_payment_date": "2025-01-01",
      "total_debt": 0,
      "notes": "",
      "created_at": "2025-01-01T10:00:00Z"
    }
  ]
}
```

**Chegirmali abonement:**
```json
{
  "subscriptions": [
    {
      "id": "dd0e8400-e29b-41d4-a716-446655440000",
      "subscription_plan": {
        "id": "ee0e8400-e29b-41d4-a716-446655440000",
        "name": "5-sinf (oylik)",
        "price": 500000,
        "period": "monthly",
        "period_display": "Oylik"
      },
      "discount": {
        "id": "ff0e8400-e29b-41d4-a716-446655440000",
        "name": "Yangi o'quvchilar uchun chegirma",
        "discount_type": "percentage",
        "discount_type_display": "Foiz",
        "amount": 20,
        "is_active": true,
        "is_valid": true
      },
      "is_active": true,
      "start_date": "2025-12-23",
      "end_date": null,
      "next_payment_date": "2026-01-23",
      "last_payment_date": null,
      "total_debt": 0,
      "notes": "O'quvchi yaratilganda abonement biriktirildi",
      "created_at": "2025-12-23T10:00:00Z"
    }
  ]
}
```

**Agar abonement bo'lmasa:**
```json
{
  "subscriptions": []
}
```

### 6. To'lov Xulosa (Payment Due) - YANGI! 🎉

**Context flag:** `include_payment_due: true` (detail view'da avtomatik)

**Chegirmasiz abonement:**
```json
{
  "payment_due": {
    "has_subscription": true,
    "total_amount": 1500000,
    "subscriptions": [
      {
        "subscription_id": "dd0e8400-e29b-41d4-a716-446655440000",
        "subscription_plan_name": "5-sinf (oylik)",
        "subscription_period": "Oylik",
        "subscription_price": 500000,
        "current_amount": 500000,
        "discount_amount": 0,
        "amount_after_discount": 500000,
        "has_discount": false,
        "debt_amount": 1000000,
        "total_amount": 1500000,
        "next_due_date": "2025-02-01",
        "overdue_months": 2,
        "is_expired": false,
        "is_overdue": true
      }
    ]
  }
}
```

**Chegirmali abonement:**
```json
{
  "payment_due": {
    "has_subscription": true,
    "total_amount": 400000,
    "subscriptions": [
      {
        "subscription_id": "dd0e8400-e29b-41d4-a716-446655440000",
        "subscription_plan_name": "5-sinf (oylik)",
        "subscription_period": "Oylik",
        "subscription_price": 500000,
        "current_amount": 500000,
        "discount_amount": 100000,
        "amount_after_discount": 400000,
        "has_discount": true,
        "debt_amount": 0,
        "total_amount": 400000,
        "next_due_date": "2026-01-23",
        "overdue_months": 0,
        "is_expired": false,
        "is_overdue": true
      }
    ]
  }
}
```

**Abonement yo'q:**
```json
{
  "payment_due": {
    "has_subscription": false,
    "total_amount": 0,
    "subscriptions": []
  }
}
```

### 7. Oxirgi Tranzaksiyalar (Recent Transactions) - YANGI! 🎉 (v2.2.0)

**Context flag:** `include_recent_transactions: true` (detail view'da avtomatik)

**Oxirgi 10 ta tranzaksiya:**
```json
{
  "recent_transactions": [
    {
      "id": "aa0e8400-e29b-41d4-a716-446655440000",
      "transaction_type": "payment",
      "transaction_type_display": "To'lov",
      "status": "completed",
      "status_display": "Bajarilgan",
      "amount": 500000,
      "payment_method": "cash",
      "payment_method_display": "Naqd pul",
      "description": "Dekabr oylik to'lovi",
      "reference_number": "PAY-2025-001",
      "transaction_date": "2025-12-23T10:30:00Z",
      "cash_register": {
        "id": "bb0e8400-e29b-41d4-a716-446655440000",
        "name": "Asosiy kassa"
      },
      "category": {
        "id": "cc0e8400-e29b-41d4-a716-446655440000",
        "name": "O'quvchi to'lovlari",
        "type": "income"
      },
      "employee": {
        "id": "dd0e8400-e29b-41d4-a716-446655440000",
        "user_id": "ee0e8400-e29b-41d4-a716-446655440000",
        "full_name": "Aziza Karimova",
        "phone_number": "+998901234999",
        "role": "cashier",
        "role_display": "Kassir",
        "avatar": "/media/profiles/avatar123.jpg"
      }
    },
    {
      "id": "ff0e8400-e29b-41d4-a716-446655440000",
      "transaction_type": "income",
      "transaction_type_display": "Kirim",
      "status": "completed",
      "status_display": "Bajarilgan",
      "amount": 300000,
      "payment_method": "card",
      "payment_method_display": "Karta",
      "description": "Qo'shimcha to'lov",
      "reference_number": "",
      "transaction_date": "2025-12-20T14:15:00Z",
      "cash_register": {
        "id": "bb0e8400-e29b-41d4-a716-446655440000",
        "name": "Asosiy kassa"
      },
      "category": null,
      "employee": null
    }
  ]
}
```

**Agar tranzaksiya bo'lmasa:**
```json
{
  "recent_transactions": []
}
```

---

## Frontend Integratsiya

### React TypeScript Interface

```typescript
// types/student.ts

export interface Student {
  // Asosiy
  id: string;
  personal_number: string;
  user_id: string;
  phone_number: string;
  first_name: string;
  last_name: string;
  middle_name: string;
  full_name: string;
  email: string;
  branch_id: string;
  branch_name: string;
  
  // Shaxsiy
  gender: 'male' | 'female' | 'other' | 'unspecified';
  status: 'active' | 'archived' | 'suspended' | 'graduated' | 'transferred';
  status_display: string;
  date_of_birth: string | null;
  address: string;
  
  // Rasmlar
  avatar: string | null;
  avatar_url: string | null;
  birth_certificate: string | null;
  birth_certificate_url: string | null;
  
  // Qo'shimcha
  additional_fields: Record<string, any> | null;
  
  // Sinf
  current_class: {
    id: string;
    name: string;
    academic_year: string;
  } | null;
  
  // Yaqinlar
  relatives_count: number;
  relatives: Relative[] | null;
  
  // Moliya
  balance: BalanceDetails;
  subscriptions: Subscription[] | null;
  payment_due: PaymentDueSummary | null;
  
  // Timestamps
  created_at: string;
  updated_at: string;
}

export interface Relative {
  id: string;
  relationship_type: string;
  relationship_type_display: string;
  first_name: string;
  middle_name: string;
  last_name: string;
  full_name: string;
  phone_number: string;
  email: string;
  gender: string;
  date_of_birth: string | null;
  address: string;
  workplace: string;
  position: string;
  passport_number: string;
  photo: string | null;
  photo_url: string | null;
  is_primary_contact: boolean;
  is_guardian: boolean;
  additional_info: Record<string, any> | null;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface BalanceDetails {
  id: string | null;
  balance: number;
  notes: string;
  updated_at: string | null;
  transactions_summary: {
    total_income: number;
    total_expense: number;
    net_balance: number;
    transactions_count: number;
  };
  payments_summary: {
    total_payments: number;
    payments_count: number;
    last_payment: {
      id: string;
      amount: number;
      date: string;
      period: string;
      period_display: string;
    } | null;
  };
}

export interface Subscription {
  id: string;
  subscription_plan: {
    id: string;
    name: string;
    price: number;
    period: string;
    period_display: string;
  };
  discount: {
    id: string;
    name: string;
    discount_type: string;
    discount_type_display: string;
    amount: number;
    is_active: boolean;
    is_valid: boolean;
  } | null;
  is_active: boolean;
  start_date: string;
  end_date: string | null;
  next_payment_date: string;
  last_payment_date: string | null;
  total_debt: number;
  notes: string;
  created_at: string;
}

export interface Transaction {
  id: string;
  transaction_type: string;
  transaction_type_display: string;
  status: string;
  status_display: string;
  amount: number;
  payment_method: string;
  payment_method_display: string;
  description: string;
  reference_number: string;
  transaction_date: string;
  cash_register: {
    id: string;
    name: string;
  } | null;
  category: {
    id: string;
    name: string;
    type: string;
  } | null;
  employee: {
    id: string;
    user_id: string;
    full_name: string;
    phone_number: string;
    role: string;
    role_display: string;
    avatar: string | null;
  } | null;
}

export interface PaymentDueSummary {
  has_subscription: boolean;
  total_amount: number;
  subscriptions: {
    subscription_id: string;
    subscription_plan_name: string;
    subscription_period: string;
    subscription_price: number;
    current_amount: number;
    discount_amount: number;
    amount_after_discount: number;
    has_discount: boolean;
    debt_amount: number;
    total_amount: number;
    next_due_date: string | null;
    overdue_months: number;
    is_expired: boolean;
    is_overdue: boolean;
  }[];
}
```

### React Component - Student Detail Page

```tsx
// pages/students/[id].tsx

import React, { useState, useEffect } from 'react';
import { Student } from '@/types/student';

const StudentDetailPage: React.FC<{ studentId: string }> = ({ studentId }) => {
  const [student, setStudent] = useState<Student | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStudentDetail();
  }, [studentId]);

  const fetchStudentDetail = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `/api/v1/school/students/${studentId}/`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-Branch-Id': branchId,
          }
        }
      );
      
      if (!response.ok) {
        throw new Error('O\'quvchi topilmadi');
      }
      
      const data = await response.json();
      setStudent(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Xatolik yuz berdi');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;
  if (!student) return <NotFound />;

  return (
    <div className="student-detail">
      {/* Header */}
      <StudentHeader student={student} />
      
      {/* Tabs */}
      <StudentTabs>
        {/* Ma'lumotlar */}
        <Tab label="Ma'lumotlar">
          <StudentInfo student={student} />
        </Tab>
        
        {/* Yaqinlar */}
        <Tab label={`Yaqinlar (${student.relatives_count})`}>
          <RelativesList relatives={student.relatives || []} />
        </Tab>
        
        {/* Moliya */}
        <Tab label="Moliya">
          <FinanceDetails 
            balance={student.balance}
            subscriptions={student.subscriptions || []}
            paymentDue={student.payment_due}
          />
        </Tab>
      </StudentTabs>
    </div>
  );
};

// Components

const StudentHeader: React.FC<{ student: Student }> = ({ student }) => (
  <div className="header">
    <div className="avatar">
      {student.avatar_url ? (
        <img src={student.avatar_url} alt={student.full_name} />
      ) : (
        <div className="avatar-placeholder">
          {student.first_name[0]}{student.last_name[0]}
        </div>
      )}
    </div>
    
    <div className="info">
      <h1>{student.full_name}</h1>
      <div className="meta">
        <span className="personal-number">{student.personal_number}</span>
        <span className={`status status-${student.status}`}>
          {student.status_display}
        </span>
      </div>
      <div className="contacts">
        <span>📞 {student.phone_number}</span>
        {student.email && <span>📧 {student.email}</span>}
      </div>
      {student.current_class && (
        <div className="class">
          🎓 {student.current_class.name} ({student.current_class.academic_year})
        </div>
      )}
    </div>
  </div>
);

const FinanceDetails: React.FC<{
  balance: BalanceDetails;
  subscriptions: Subscription[];
  paymentDue: PaymentDueSummary | null;
}> = ({ balance, subscriptions, paymentDue }) => (
  <div className="finance-details">
    {/* To'lov Xulosa */}
    {paymentDue && paymentDue.has_subscription && (
      <div className="payment-due-card">
        <h3>💰 To'lov Xulosa</h3>
        <div className="total">
          Jami to'lanishi kerak: 
          <strong>{formatMoney(paymentDue.total_amount)}</strong>
        </div>
        
        {paymentDue.subscriptions.map((sub) => (
          <div key={sub.subscription_id} className="subscription-due">
            <h4>{sub.subscription_plan_name}</h4>
            
            {sub.is_overdue && (
              <div className="alert alert-danger">
                ⚠️ {sub.overdue_months} oy kechiktirilgan!
              </div>
            )}
            
            <div className="amounts">
              <div>Joriy oy: {formatMoney(sub.current_amount)}</div>
              {sub.debt_amount > 0 && (
                <div className="debt">
                  Qarz: {formatMoney(sub.debt_amount)}
                </div>
              )}
              <div className="total">
                Jami: {formatMoney(sub.total_amount)}
              </div>
            </div>
            
            <div className="dates">
              <div>Keyingi to'lov: {formatDate(sub.next_due_date)}</div>
            </div>
            
            <button 
              className="btn btn-primary"
              onClick={() => handlePayment(sub)}
            >
              To'lov qilish ({formatMoney(sub.total_amount)})
            </button>
          </div>
        ))}
      </div>
    )}
    
    {/* Abonementlar */}
    <div className="subscriptions-card">
      <h3>📋 Abonementlar</h3>
      {subscriptions.length > 0 ? (
        subscriptions.map((sub) => (
          <div key={sub.id} className="subscription-item">
            <div className="plan-name">{sub.subscription_plan.name}</div>
            <div className="plan-price">
              {formatMoney(sub.subscription_plan.price)} / {sub.subscription_plan.period_display}
            </div>
            <div className="dates">
              <span>Boshlanish: {formatDate(sub.start_date)}</span>
              <span>Keyingi to'lov: {formatDate(sub.next_payment_date)}</span>
            </div>
            {sub.total_debt > 0 && (
              <div className="debt-badge">
                Qarz: {formatMoney(sub.total_debt)}
              </div>
            )}
          </div>
        ))
      ) : (
        <div className="empty">Abonement yo'q</div>
      )}
    </div>
    
    {/* Balans */}
    <div className="balance-card">
      <h3>💳 Balans</h3>
      <div className="balance-amount">
        {formatMoney(balance.balance)}
      </div>
      
      <div className="stats">
        <div className="stat">
          <span>Kirim:</span>
          <span>{formatMoney(balance.transactions_summary.total_income)}</span>
        </div>
        <div className="stat">
          <span>Chiqim:</span>
          <span>{formatMoney(balance.transactions_summary.total_expense)}</span>
        </div>
        <div className="stat">
          <span>Tranzaksiyalar:</span>
          <span>{balance.transactions_summary.transactions_count}</span>
        </div>
      </div>
      
      {balance.payments_summary.last_payment && (
        <div className="last-payment">
          <h4>Oxirgi to'lov</h4>
          <div>
            {formatMoney(balance.payments_summary.last_payment.amount)}
            {' - '}
            {formatDate(balance.payments_summary.last_payment.date)}
          </div>
        </div>
      )}
    </div>
  </div>
);

// Helper functions
const formatMoney = (amount: number) => {
  return new Intl.NumberFormat('uz-UZ').format(amount) + ' so\'m';
};

const formatDate = (dateStr: string | null) => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString('uz-UZ');
};
```

---

## Misollar

### 1. Student Detail Request

```bash
curl -X GET "http://localhost:8000/api/v1/school/students/550e8400-e29b-41d4-a716-446655440000/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Branch-Id: BRANCH_UUID"
```

### 2. To'liq Response Misoli

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "personal_number": "TAS-25-0001",
  "user_id": "660e8400-e29b-41d4-a716-446655440000",
  "phone_number": "+998901234567",
  "first_name": "Ali",
  "last_name": "Valiyev",
  "middle_name": "Olim o'g'li",
  "full_name": "Ali Olim o'g'li Valiyev",
  "email": "ali@example.com",
  "branch_id": "770e8400-e29b-41d4-a716-446655440000",
  "branch_name": "Markaziy filial",
  "gender": "male",
  "status": "active",
  "status_display": "Aktiv",
  "date_of_birth": "2010-05-15",
  "address": "Toshkent shahri, Chilonzor tumani",
  "avatar": "/media/avatars/ali.jpg",
  "avatar_url": "http://localhost:8000/media/avatars/ali.jpg",
  "birth_certificate": "/media/certificates/birth.pdf",
  "birth_certificate_url": "http://localhost:8000/media/certificates/birth.pdf",
  "additional_fields": {
    "passport_number": "AB1234567",
    "nationality": "UZ"
  },
  "current_class": {
    "id": "880e8400-e29b-41d4-a716-446655440000",
    "name": "5-A",
    "academic_year": "2024-2025"
  },
  "relatives_count": 2,
  "relatives": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440000",
      "relationship_type": "father",
      "relationship_type_display": "Otasi",
      "full_name": "Olim Karim o'g'li Valiyev",
      "phone_number": "+998901234568",
      "is_primary_contact": true,
      "is_guardian": true
    }
  ],
  "balance": {
    "id": "bb0e8400-e29b-41d4-a716-446655440000",
    "balance": 2500000,
    "transactions_summary": {
      "total_income": 3000000,
      "total_expense": 500000,
      "net_balance": 2500000,
      "transactions_count": 6
    },
    "payments_summary": {
      "total_payments": 3000000,
      "payments_count": 6,
      "last_payment": {
        "amount": 500000,
        "date": "2025-01-15T10:00:00Z",
        "period": "monthly"
      }
    }
  },
  "subscriptions": [
    {
      "id": "dd0e8400-e29b-41d4-a716-446655440000",
      "subscription_plan": {
        "name": "5-sinf (oylik)",
        "price": 500000,
        "period_display": "Oylik"
      },
      "is_active": true,
      "next_payment_date": "2025-02-01",
      "total_debt": 0
    }
  ],
  "payment_due": {
    "has_subscription": true,
    "total_amount": 500000,
    "subscriptions": [
      {
        "subscription_plan_name": "5-sinf (oylik)",
        "current_amount": 500000,
        "debt_amount": 0,
        "total_amount": 500000,
        "overdue_months": 0,
        "is_overdue": false
      }
    ]
  },
  "created_at": "2025-01-01T10:00:00Z",
  "updated_at": "2025-01-20T10:00:00Z"
}
```

---

## API O'zgarishlari (Changelog)

### v2.0.0 (2025-12-23) - YANGI QO'SHILDI

1. **Subscriptions** - O'quvchi abonementlari ro'yxati
   - `subscriptions` maydoni qo'shildi
   - Abonement tariflari, narxlar, sanalar
   - Aktiv/Aktiv emas holati

2. **Payment Due** - To'lov xulosa
   - `payment_due` maydoni qo'shildi
   - Joriy oy + qarz = jami to'lov
   - Kechikkan oylar sonini ko'rsatish
   - Har bir abonement uchun alohida xulosa

3. **Relatives** - Yaqinlar ro'yxati
   - `relatives` maydoni qo'shildi (detail view'da)
   - To'liq yaqin ma'lumotlari
   - `relatives_count` saqlanib qoldi

4. **Context Flags** - Yangi parametrlar
   - `include_relatives: true` - Yaqinlar ro'yxati
   - `include_subscriptions: true` - Abonementlar
   - `include_payment_due: true` - To'lov xulosa
   - Detail view'da barchasi avtomatik `true`

---

## Qo'shimcha Resurslar

- [Student Payments API](../student-payments-api.md) - To'lov qilish
- [Student Subscription API](../student-subscription-api.md) - Abonement boshqarish
- [Finance API](./finance.md) - Moliya tizimi

---

**Muallif:** Mendeleyev Backend Team  
**Sanasi:** 2025-12-23  
**Versiya:** 2.0.0
