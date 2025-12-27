# O'quvchi Abonementlari va To'lov Xulosa API

Bu hujjatda o'quvchilar uchun abonement tizimi va to'lov xulosasi API'lari haqida ma'lumot berilgan.

## Mundarija

1. [Umumiy Ma'lumot](#umumiy-malumot)
2. [StudentSubscription Modeli](#studentsubscription-modeli)
3. [Abonement API](#abonement-api)
4. [To'lov Xulosa API](#tolov-xulosa-api)
5. [Frontend Integratsiya](#frontend-integratsiya)
6. [Misollar](#misollar)

---

## Umumiy Ma'lumot

### Tizim Arxitekturasi

```
StudentProfile
    ↓
StudentSubscription (o'quvchi abonementi)
    ↓
calculate_payment_due() → To'lov xulosasi
    ↓
Payment → Transaction → CashRegister + StudentBalance
```

### Asosiy Tushunchalar

1. **StudentSubscription** - O'quvchining abonement tarifi
   - Har bir o'quvchida bir yoki bir nechta abonement bo'lishi mumkin
   - Abonement uchun to'lov davrini va qarzlarni boshqaradi
   - Avtomatik to'lov sanasini yangilaydi

2. **Payment Due Summary** - To'lov xulosa
   - O'quvchi qancha to'lashi kerakligini ko'rsatadi
   - Joriy davr + qarz summasi
   - Kechikkan oylar sonini hisoblaydi

---

## StudentSubscription Modeli

### Model Ma'lumotlari

```python
class StudentSubscription(BaseModel):
    """O'quvchining abonement tariflari."""
    
    student_profile: ForeignKey[StudentProfile]
    subscription_plan: ForeignKey[SubscriptionPlan]
    branch: ForeignKey[Branch]
    
    # Holat
    is_active: bool  # Abonement faolmi?
    
    # Davriy to'lov
    start_date: date  # Abonement boshlanish sanasi
    end_date: date | None  # Tugash sanasi (None = cheksiz)
    next_payment_date: date  # Keyingi to'lov sanasi
    
    # Qarzdorlik
    total_debt: int  # To'lanmagan summalar (so'm)
    last_payment_date: date | None  # Oxirgi to'lov sanasi
    
    notes: str  # Qo'shimcha eslatmalar
```

### Metodlar

#### `calculate_payment_due()`

O'quvchi qancha to'lashi kerakligini hisoblaydi.

**Returns:**
```python
{
    'current_amount': 500000,      # Joriy davr uchun summa
    'debt_amount': 1000000,        # Qarz summasi
    'total_amount': 1500000,       # Jami to'lanishi kerak
    'next_due_date': date(2025, 1, 1),  # Keyingi to'lov sanasi
    'overdue_months': 2,           # Necha oy kechikkan
    'is_expired': False,           # Abonement tugaganmi?
}
```

#### `update_next_payment_date()`

To'lovdan keyin keyingi to'lov sanasini yangilaydi.

```python
# Oylik: +1 oy
# Choraklik: +3 oy
# Yillik: +1 yil
```

#### `add_debt(amount)` / `reduce_debt(amount)`

Qarzni boshqarish (F() expressions bilan).

```python
subscription.add_debt(500000)     # Qarz qo'shish
subscription.reduce_debt(200000)  # Qarzni kamaytirish
```

---

## Abonement API

### 1. Abonementlar Ro'yxati

**Endpoint:** `GET /api/v1/school/finance/student-subscriptions/`

**Headers:**
```
Authorization: Bearer <token>
X-Branch-Id: <branch_uuid>
```

**Query Parameters:**
- `student_profile` (UUID) - O'quvchi profili ID
- `subscription_plan` (UUID) - Abonement tarifi ID
- `is_active` (bool) - Faol abonementlar
- `search` - O'quvchi ismi bo'yicha qidiruv
- `ordering` - Tartiblash (`created_at`, `-next_payment_date`, `total_debt`)

**Response:**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "student_profile": "uuid",
      "student_name": "Ali Valiyev",
      "subscription_plan": "uuid",
      "subscription_plan_name": "5-sinf (oylik)",
      "subscription_plan_price": 500000,
      "period_display": "Oylik",
      "branch": "uuid",
      "branch_name": "Markaziy filial",
      "is_active": true,
      "start_date": "2025-01-01",
      "end_date": null,
      "next_payment_date": "2025-02-01",
      "total_debt": 1000000,
      "last_payment_date": "2024-12-01",
      "notes": "",
      "created_at": "2025-01-01T10:00:00Z",
      "updated_at": "2025-01-15T10:00:00Z"
    }
  ]
}
```

**Frontend Misol:**
```typescript
// Abonementlar ro'yxatini olish
const fetchSubscriptions = async (studentProfileId?: string) => {
  const params = new URLSearchParams();
  if (studentProfileId) {
    params.append('student_profile', studentProfileId);
  }
  params.append('is_active', 'true');
  
  const response = await fetch(
    `/api/v1/school/finance/student-subscriptions/?${params}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Branch-Id': branchId,
      }
    }
  );
  
  return await response.json();
};
```

---

### 2. Abonement Yaratish

**Endpoint:** `POST /api/v1/school/finance/student-subscriptions/`

**Request Body:**
```json
{
  "student_profile": "uuid",
  "subscription_plan": "uuid",
  "branch": "uuid",
  "start_date": "2025-01-01",
  "end_date": null,
  "next_payment_date": "2025-02-01",
  "notes": "Oylik to'lov"
}
```

**Validation:**
- O'quvchi bu filialga tegishli bo'lishi kerak
- Tarif bu filial uchun mavjud bo'lishi kerak
- O'quvchida bu tarif allaqachon faol bo'lmasligi kerak

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "student_profile": "uuid",
  "subscription_plan": "uuid",
  ...
}
```

**Frontend Misol:**
```typescript
// Yangi abonement yaratish
const createSubscription = async (data: {
  student_profile: string;
  subscription_plan: string;
  start_date: string;
  next_payment_date: string;
}) => {
  const response = await fetch(
    '/api/v1/school/finance/student-subscriptions/',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Branch-Id': branchId,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data)
    }
  );
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Xatolik yuz berdi');
  }
  
  return await response.json();
};
```

---

### 3. Abonement Tafsilotlari

**Endpoint:** `GET /api/v1/school/finance/student-subscriptions/{id}/`

**Response:**
```json
{
  "id": "uuid",
  "student_profile": "uuid",
  "student_name": "Ali Valiyev",
  ...
}
```

---

### 4. Abonementni Yangilash

**Endpoint:** `PUT /api/v1/school/finance/student-subscriptions/{id}/`

**Request Body:**
```json
{
  "is_active": false,
  "end_date": "2025-12-31",
  "notes": "Abonement to'xtatildi"
}
```

---

## To'lov Xulosa API

### O'quvchi To'lov Xulosasi

**Endpoint:** `GET /api/v1/school/finance/payment-due-summary/`

**Query Parameters:**
- `student_profile_id` (UUID, **required**) - O'quvchi profili ID

**Response:**
```json
[
  {
    "student_profile_id": "uuid",
    "student_name": "Ali Valiyev",
    "subscription_id": "uuid",
    "subscription_plan_name": "5-sinf (oylik)",
    "subscription_period": "Oylik",
    "subscription_price": 500000,
    "current_amount": 500000,
    "debt_amount": 1000000,
    "total_amount": 1500000,
    "next_due_date": "2025-02-01",
    "last_payment_date": "2024-12-01",
    "overdue_months": 2,
    "is_expired": false,
    "is_overdue": true
  }
]
```

**Maydonnlar Tushuntirish:**

| Maydon | Turi | Tavsif |
|--------|------|--------|
| `current_amount` | int | Joriy davr uchun summa |
| `debt_amount` | int | To'lanmagan qarz summasi |
| `total_amount` | int | Jami to'lanishi kerak (`debt + current`) |
| `next_due_date` | date | Keyingi to'lov sanasi |
| `overdue_months` | int | Necha oy kechikkan (0 = kechiktirmagan) |
| `is_expired` | bool | Abonement tugaganmi? |
| `is_overdue` | bool | To'lov muddati o'tganmi? |

**Error Responses:**

```json
// student_profile_id yo'q
{
  "error": "student_profile_id parametri talab qilinadi"
}

// O'quvchi topilmadi
{
  "error": "O'quvchi profili topilmadi"
}

// Faol abonement yo'q
{
  "error": "O'quvchida faol abonement topilmadi"
}
```

---

## Frontend Integratsiya

### React Component - Payment Summary

```typescript
import React, { useState, useEffect } from 'react';

interface PaymentDue {
  student_profile_id: string;
  student_name: string;
  subscription_plan_name: string;
  subscription_price: number;
  current_amount: number;
  debt_amount: number;
  total_amount: number;
  next_due_date: string;
  last_payment_date: string | null;
  overdue_months: number;
  is_expired: boolean;
  is_overdue: boolean;
}

const PaymentDueSummary: React.FC<{ studentProfileId: string }> = ({ 
  studentProfileId 
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [paymentDue, setPaymentDue] = useState<PaymentDue[]>([]);

  useEffect(() => {
    fetchPaymentDue();
  }, [studentProfileId]);

  const fetchPaymentDue = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `/api/v1/school/finance/payment-due-summary/?student_profile_id=${studentProfileId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-Branch-Id': branchId,
          }
        }
      );
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Xatolik yuz berdi');
      }
      
      const data = await response.json();
      setPaymentDue(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Xatolik');
    } finally {
      setLoading(false);
    }
  };

  const formatMoney = (amount: number) => {
    return new Intl.NumberFormat('uz-UZ').format(amount) + ' so\'m';
  };

  if (loading) return <div>Yuklanmoqda...</div>;
  if (error) return <div className="error">{error}</div>;
  if (paymentDue.length === 0) {
    return <div>O'quvchida faol abonement yo'q</div>;
  }

  return (
    <div className="payment-due-summary">
      {paymentDue.map((due) => (
        <div key={due.subscription_plan_name} className="payment-card">
          <h3>{due.subscription_plan_name}</h3>
          
          {/* Xabar */}
          {due.is_expired && (
            <div className="alert alert-warning">
              Abonement tugagan
            </div>
          )}
          {due.is_overdue && !due.is_expired && (
            <div className="alert alert-danger">
              To'lov {due.overdue_months} oy kechiktirilgan
            </div>
          )}
          
          {/* Summalar */}
          <div className="payment-amounts">
            <div className="amount-row">
              <span>Joriy davr:</span>
              <strong>{formatMoney(due.current_amount)}</strong>
            </div>
            
            {due.debt_amount > 0 && (
              <div className="amount-row debt">
                <span>Qarz:</span>
                <strong className="text-danger">
                  {formatMoney(due.debt_amount)}
                </strong>
              </div>
            )}
            
            <div className="amount-row total">
              <span>Jami to'lanishi kerak:</span>
              <strong className="text-primary">
                {formatMoney(due.total_amount)}
              </strong>
            </div>
          </div>
          
          {/* Sanalar */}
          <div className="payment-dates">
            <div>
              <small>Keyingi to'lov:</small>
              <div>{new Date(due.next_due_date).toLocaleDateString('uz-UZ')}</div>
            </div>
            {due.last_payment_date && (
              <div>
                <small>Oxirgi to'lov:</small>
                <div>{new Date(due.last_payment_date).toLocaleDateString('uz-UZ')}</div>
              </div>
            )}
          </div>
          
          {/* To'lov tugmasi */}
          <button 
            className="btn btn-primary"
            onClick={() => handlePayment(due)}
          >
            To'lov qilish ({formatMoney(due.total_amount)})
          </button>
        </div>
      ))}
    </div>
  );
};
```

### CSS Styles

```css
.payment-due-summary {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
  padding: 1rem;
}

.payment-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.payment-card h3 {
  margin: 0 0 1rem 0;
  color: #333;
  font-size: 1.25rem;
}

.alert {
  padding: 0.75rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.alert-warning {
  background: #fff3cd;
  border: 1px solid #ffc107;
  color: #856404;
}

.alert-danger {
  background: #f8d7da;
  border: 1px solid #f5c2c7;
  color: #842029;
}

.payment-amounts {
  margin: 1rem 0;
}

.amount-row {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f0f0f0;
}

.amount-row.total {
  border-bottom: none;
  border-top: 2px solid #007bff;
  padding-top: 1rem;
  font-size: 1.1rem;
}

.text-danger {
  color: #dc3545;
}

.text-primary {
  color: #007bff;
}

.payment-dates {
  display: flex;
  gap: 2rem;
  margin: 1rem 0;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.payment-dates small {
  color: #6c757d;
  font-size: 0.8rem;
}

.btn {
  width: 100%;
  padding: 0.75rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover {
  background: #0056b3;
}
```

---

## Misollar

### 1. O'quvchi Abonement Yaratish

```bash
curl -X POST https://api.example.com/api/v1/school/finance/student-subscriptions/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Branch-Id: BRANCH_UUID" \
  -H "Content-Type: application/json" \
  -d '{
    "student_profile": "550e8400-e29b-41d4-a716-446655440000",
    "subscription_plan": "660e8400-e29b-41d4-a716-446655440000",
    "branch": "770e8400-e29b-41d4-a716-446655440000",
    "start_date": "2025-01-01",
    "next_payment_date": "2025-02-01"
  }'
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "student_profile": "550e8400-e29b-41d4-a716-446655440000",
  "student_name": "Ali Valiyev",
  "subscription_plan": "660e8400-e29b-41d4-a716-446655440000",
  "subscription_plan_name": "5-sinf (oylik)",
  "subscription_plan_price": 500000,
  "period_display": "Oylik",
  "branch": "770e8400-e29b-41d4-a716-446655440000",
  "branch_name": "Markaziy filial",
  "is_active": true,
  "start_date": "2025-01-01",
  "end_date": null,
  "next_payment_date": "2025-02-01",
  "total_debt": 0,
  "last_payment_date": null,
  "notes": "",
  "created_at": "2025-01-01T10:00:00Z",
  "updated_at": "2025-01-01T10:00:00Z"
}
```

---

### 2. To'lov Xulosasini Olish

```bash
curl -X GET "https://api.example.com/api/v1/school/finance/payment-due-summary/?student_profile_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Branch-Id: BRANCH_UUID"
```

**Response:**
```json
[
  {
    "student_profile_id": "550e8400-e29b-41d4-a716-446655440000",
    "student_name": "Ali Valiyev",
    "subscription_id": "123e4567-e89b-12d3-a456-426614174000",
    "subscription_plan_name": "5-sinf (oylik)",
    "subscription_period": "Oylik",
    "subscription_price": 500000,
    "current_amount": 500000,
    "debt_amount": 1000000,
    "total_amount": 1500000,
    "next_due_date": "2025-02-01",
    "last_payment_date": "2024-12-01",
    "overdue_months": 2,
    "is_expired": false,
    "is_overdue": true
  }
]
```

**Tushuntirish:**
- O'quvchi 2 oy kechiktirgan (`overdue_months: 2`)
- Qarz: 1,000,000 so'm (2 oylik)
- Joriy oy: 500,000 so'm
- **Jami to'lanishi kerak: 1,500,000 so'm**

---

### 3. To'lov Jarayoni (Full Flow)

#### 1-qadam: To'lov xulosasini olish

```typescript
const paymentDue = await fetchPaymentDue(studentProfileId);
const totalAmount = paymentDue[0].total_amount; // 1,500,000
```

#### 2-qadam: To'lov qilish (Payment API)

```typescript
const payment = await createPayment({
  student_profile: studentProfileId,
  subscription_plan: subscriptionPlanId,
  base_amount: totalAmount,
  final_amount: totalAmount,
  cash_register: cashRegisterId,
  period_start: '2025-01-01',
  period_end: '2025-01-31',
});
```

#### 3-qadam: Abonementni yangilash

To'lov yaratilgandan keyin, backend avtomatik:
- `StudentSubscription.reduce_debt(amount)` - qarzni kamaytiradi
- `StudentSubscription.update_next_payment_date()` - keyingi sanani yangilaydi
- `StudentBalance.add_amount(amount)` - balansni yangilaydi
- `CashRegister.update_balance(amount)` - kassani yangilaydi

---

## Best Practices

### 1. To'lov Xulosa Ko'rsatish

```typescript
// ❌ Yomon: Faqat joriy davr summasi
<div>To'lov: {formatMoney(subscription.subscription_price)}</div>

// ✅ Yaxshi: To'liq xulosa API dan
const paymentDue = await fetchPaymentDue(studentProfileId);
<div>
  <div>Joriy: {formatMoney(paymentDue.current_amount)}</div>
  {paymentDue.debt_amount > 0 && (
    <div>Qarz: {formatMoney(paymentDue.debt_amount)}</div>
  )}
  <div>Jami: {formatMoney(paymentDue.total_amount)}</div>
</div>
```

### 2. Kechikkan To'lovlar

```typescript
// Kechikkan oylar sonini ko'rsatish
if (paymentDue.is_overdue) {
  return (
    <div className="alert alert-danger">
      ⚠️ To'lov {paymentDue.overdue_months} oy kechiktirilgan!
      <br />
      Jami qarzdorlik: {formatMoney(paymentDue.debt_amount)}
    </div>
  );
}
```

### 3. Abonement Holati

```typescript
// Abonement tugagan
if (paymentDue.is_expired) {
  return (
    <div className="alert alert-warning">
      Abonement tugagan. Yangilash uchun admin bilan bog'laning.
    </div>
  );
}
```

---

## Troubleshooting

### Xato: "O'quvchida faol abonement topilmadi"

**Sabab:** O'quvchi uchun abonement yaratilmagan yoki faol emas.

**Yechim:**
1. Abonement yaratish: `POST /student-subscriptions/`
2. Yoki mavjud abonementni faollashtirish: `PUT /student-subscriptions/{id}/` → `is_active: true`

---

### Xato: "Bu abonement turi allaqachon mavjud"

**Sabab:** O'quvchida bu tarif allaqachon faol.

**Yechim:**
1. Mavjud abonementni yangilash
2. Yoki boshqa tarif tanlash

---

### To'lov Xulosasi Bo'sh Qaytadi

**Sabab:** `is_active=False` yoki `deleted_at IS NOT NULL`

**Yechim:**
```sql
-- Database tekshirish
SELECT * FROM finance_studentsubscription 
WHERE student_profile_id = 'uuid' 
  AND is_active = true 
  AND deleted_at IS NULL;
```

---

## Qo'shimcha Resurslar

- [Student Payment API](./student-payments-api.md) - To'lov qilish jarayoni
- [Finance Optimization](./finance-optimization-guide.md) - Performance tuning
- [Transaction API](./transaction-api.md) - Tranzaksiya tizimi

---

## API Xulosa

| Endpoint | Method | Tavsif |
|----------|--------|--------|
| `/student-subscriptions/` | GET | Abonementlar ro'yxati |
| `/student-subscriptions/` | POST | Yangi abonement yaratish |
| `/student-subscriptions/{id}/` | GET | Abonement tafsilotlari |
| `/student-subscriptions/{id}/` | PUT | Abonementni yangilash |
| `/student-subscriptions/{id}/` | DELETE | Abonementni o'chirish |
| `/payment-due-summary/` | GET | O'quvchi to'lov xulosasi |

---

**Muallif:** Mendeleyev Backend Team  
**Sanasi:** 2025-12-23  
**Versiya:** 1.0
