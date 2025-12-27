# O'quvchi To'lovlari API - To'liq Qo'llanma

## 📚 Mundarija

1. [Tizim Arxitekturasi](#tizim-arxitekturasi)
2. [API Endpointlar](#api-endpointlar)
3. [Modellar](#modellar)
4. [O'quvchi To'lovi Jarayoni](#oqcuvchi-tolovi-jarayoni)
5. [Frontend Integratsiyasi](#frontend-integratsiyasi)
6. [Misollar](#misollar)

---

## 🏗️ Tizim Arxitekturasi

### Asosiy Komponentlar

```
┌─────────────────────┐
│  StudentProfile     │
│  (O'quvchi)         │
└──────┬──────────────┘
       │ 1:1
       ▼
┌─────────────────────┐
│  StudentBalance     │ ← Auto-created
│  (Balans)           │
└──────┬──────────────┘
       │
       │ 1:N
       ▼
┌─────────────────────┐      ┌──────────────────┐
│  Payment            │──────│SubscriptionPlan  │
│  (To'lov)           │  N:1 │ (Abonement)      │
└──────┬──────────────┘      └──────────────────┘
       │
       │ 1:1
       ▼
┌─────────────────────┐
│  Transaction        │
│  (Tranzaksiya)      │
└─────────────────────┘
```

### Ma'lumot Oqimi

```
1. O'quvchi yaratiladi → StudentBalance avtomatik yaratiladi (signal)
2. To'lov qabul qilinadi → Payment yaratiladi
3. Payment yaratilganda:
   - Transaction avtomatik yaratiladi (INCOME)
   - StudentBalance yangilanadi (+amount)
   - CashRegister balance yangilanadi (+amount)
```

---

## 📡 API Endpointlar

### Base URL
```
/api/v1/school/finance/
```

### 1️⃣ **O'quvchi Balanslari**

#### GET /student-balances/
O'quvchilar balanslari ro'yxati

**Query Parametrlar:**
- `branch_id` (UUID) - Filial ID (optional, JWT/header'dan avtomatik)
- `search` (string) - O'quvchi nomi yoki shaxsiy raqami
- `ordering` - `balance`, `-balance`, `created_at`, `-created_at`
- `page` (int) - Sahifa raqami
- `page_size` (int) - Sahifadagi elementlar soni (default: 20)

**Response:**
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/v1/school/finance/student-balances/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "student_profile": "uuid",
      "student_name": "Ali Valiyev",
      "student_personal_number": "ST-2024-001",
      "balance": 1500000,
      "notes": "",
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-12-22T15:30:00Z"
    }
  ]
}
```

#### GET /student-balances/{id}/
Bitta o'quvchi balansi

**Response:**
```json
{
  "id": "uuid",
  "student_profile": "uuid",
  "student_name": "Ali Valiyev",
  "student_personal_number": "ST-2024-001",
  "balance": 1500000,
  "notes": "Dekabr oyi to'lovi qabul qilindi",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-12-22T15:30:00Z"
}
```

---

### 2️⃣ **Abonement Tariflari**

#### GET /subscription-plans/
Abonement tariflari ro'yxati

**Query Parametrlar:**
- `branch_id` (UUID) - Filial ID
- `is_active` (boolean) - Faqat faol tariflar
- `search` (string) - Tarif nomi yoki tavsif
- `ordering` - `price`, `-price`, `grade_level_min`

**Response:**
```json
{
  "count": 5,
  "results": [
    {
      "id": "uuid",
      "branch": "uuid",
      "branch_name": "Filial 1",
      "name": "Boshlang'ich sinflar",
      "description": "1-4 sinflar uchun oylik to'lov",
      "grade_level_min": 1,
      "grade_level_max": 4,
      "grade_level_range": "1-4",
      "period": "monthly",
      "period_display": "Oylik",
      "price": 1400000,
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-12-01T10:00:00Z"
    },
    {
      "id": "uuid",
      "branch": "uuid",
      "branch_name": "Filial 1",
      "name": "O'rta sinflar",
      "description": "5-9 sinflar uchun oylik to'lov",
      "grade_level_min": 5,
      "grade_level_max": 9,
      "grade_level_range": "5-9",
      "period": "monthly",
      "period_display": "Oylik",
      "price": 1900000,
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-12-01T10:00:00Z"
    }
  ]
}
```

#### POST /subscription-plans/
Yangi abonement tarifi yaratish

**Request Body:**
```json
{
  "branch": "uuid",  // optional - bo'sh bo'lsa global
  "name": "Boshlang'ich sinflar",
  "description": "1-4 sinflar uchun",
  "grade_level_min": 1,
  "grade_level_max": 4,
  "period": "monthly",
  "price": 1400000,
  "is_active": true
}
```

**Validatsiya:**
- `grade_level_min` va `grade_level_max`: 1-11 orasida
- `grade_level_min <= grade_level_max`
- `price > 0`

#### GET /subscription-plans/{id}/
#### PUT/PATCH /subscription-plans/{id}/
#### DELETE /subscription-plans/{id}/

---

### 3️⃣ **Chegirmalar**

#### GET /discounts/
Chegirmalar ro'yxati

**Response:**
```json
{
  "results": [
    {
      "id": "uuid",
      "branch": "uuid",
      "branch_name": "Filial 1",
      "name": "Yangi yil chegirmasi",
      "discount_type": "percentage",
      "discount_type_display": "Foiz",
      "amount": 10,
      "discount_display": "10%",
      "is_active": true,
      "valid_from": "2024-12-01T00:00:00Z",
      "valid_until": "2025-01-15T23:59:59Z",
      "description": "Yangi yil bayramiga maxsus chegirma",
      "conditions": {},
      "is_valid": true,
      "created_at": "2024-11-25T10:00:00Z",
      "updated_at": "2024-11-25T10:00:00Z"
    }
  ]
}
```

**Chegirma Turlari:**
- `percentage` - Foiz (1-100%)
- `fixed` - Aniq summa (so'm)

---

### 4️⃣ **To'lovlar** ⭐ ASOSIY

#### GET /payments/
To'lovlar ro'yxati

**Query Parametrlar:**
- `branch_id` (UUID) - Filial ID
- `student_profile` (UUID) - O'quvchi ID
- `period_start` (date) - Sanadan (YYYY-MM-DD)
- `period_end` (date) - Sanagacha (YYYY-MM-DD)
- `search` (string) - Qidirish
- `ordering` - `payment_date`, `-payment_date`, `final_amount`

**Response:**
```json
{
  "count": 250,
  "results": [
    {
      "id": "uuid",
      "student_profile": "uuid",
      "student_name": "Ali Valiyev",
      "student_personal_number": "ST-2024-001",
      "branch": "uuid",
      "branch_name": "Filial 1",
      "subscription_plan": "uuid",
      "subscription_plan_name": "Boshlang'ich sinflar (1-4)",
      "base_amount": 1400000,
      "discount_amount": 140000,
      "final_amount": 1260000,
      "discount": "uuid",
      "discount_name": "Yangi yil chegirmasi (10%)",
      "payment_method": "cash",
      "payment_method_display": "Naqd pul",
      "period": "monthly",
      "period_display": "Oylik",
      "payment_date": "2024-12-22T10:30:00Z",
      "period_start": "2024-12-01",
      "period_end": "2024-12-31",
      "transaction": "uuid",
      "notes": "Dekabr oyi uchun to'lov",
      "created_at": "2024-12-22T10:30:00Z",
      "updated_at": "2024-12-22T10:30:00Z"
    }
  ]
}
```

#### POST /payments/ ⭐
To'lov qabul qilish

**Request Body:**
```json
{
  "student_profile": "uuid",
  "branch": "uuid",  // optional - JWT'dan avtomatik
  "subscription_plan": "uuid",  // optional
  "base_amount": 1400000,
  "discount": "uuid",  // optional
  "payment_method": "cash",
  "period": "monthly",
  "payment_date": "2024-12-22T10:30:00Z",  // optional - default: hozir
  "period_start": "2024-12-01",
  "period_end": "2024-12-31",
  "cash_register": "uuid",  // kerak!
  "notes": "Dekabr oyi uchun to'lov"
}
```

**Validatsiya:**
- `base_amount > 0`
- `cash_register` majburiy
- `student_profile` mavjud bo'lishi kerak
- Agar `discount` berilgan bo'lsa, faol va valid bo'lishi kerak

**Avtomatik Hisoblashlar:**
```javascript
discount_amount = discount ? discount.calculate_discount(base_amount) : 0
final_amount = base_amount - discount_amount
```

**Backend Jarayoni:**
```python
1. Payment yaratiladi
2. Transaction yaratiladi:
   - type: INCOME
   - amount: final_amount
   - student_profile: student
   - status: COMPLETED (Branch Admin) yoki PENDING
3. StudentBalance yangilanadi:
   - balance += final_amount
4. CashRegister balance yangilanadi:
   - balance += final_amount
```

#### GET /payments/{id}/
Bitta to'lov ma'lumotlari

---

## 🗄️ Modellar

### StudentBalance
```python
{
  "student_profile": UUID,  # OneToOne
  "balance": Integer,       # so'm
  "notes": Text,
  "created_at": DateTime,
  "updated_at": DateTime
}
```

**Signal:** O'quvchi yaratilganda avtomatik yaratiladi (balance=0)

**Metodlar:**
- `add_amount(amount)` - Balansga qo'shish
- `subtract_amount(amount)` - Balansdan ayirish (tekshiradi)

---

### SubscriptionPlan
```python
{
  "branch": UUID | null,           # null=global
  "name": String(255),
  "description": Text,
  "grade_level_min": Integer(1-11),
  "grade_level_max": Integer(1-11),
  "period": String,                # monthly, quarterly, yearly
  "price": BigInteger,             # so'm
  "is_active": Boolean,
  "created_at": DateTime,
  "updated_at": DateTime
}
```

**Period Choices:**
- `monthly` - Oylik
- `quarterly` - Choraklik (3 oy)
- `yearly` - Yillik

---

### Discount
```python
{
  "branch": UUID | null,
  "name": String(255),
  "discount_type": String,  # percentage / fixed
  "amount": Integer,        # foiz yoki so'm
  "is_active": Boolean,
  "valid_from": DateTime | null,
  "valid_until": DateTime | null,
  "description": Text,
  "conditions": JSON,
  "created_at": DateTime,
  "updated_at": DateTime
}
```

**Metodlar:**
- `calculate_discount(base_amount)` → Integer
- `is_valid()` → Boolean (sana tekshiradi)

---

### Payment
```python
{
  "student_profile": UUID,
  "branch": UUID,
  "subscription_plan": UUID | null,
  "base_amount": BigInteger,
  "discount_amount": BigInteger,
  "final_amount": BigInteger,
  "discount": UUID | null,
  "payment_method": String,
  "period": String,
  "payment_date": DateTime,
  "period_start": Date,
  "period_end": Date,
  "transaction": UUID | null,  # auto-created
  "notes": Text,
  "cash_register": UUID,
  "created_at": DateTime,
  "updated_at": DateTime
}
```

**Payment Methods:**
- `cash` - Naqd pul
- `card` - Karta
- `bank_transfer` - Bank o'tkazmasi
- `mobile_payment` - Mobil to'lov (Click, Payme)

---

## 💰 O'quvchi To'lovi Jarayoni

### 1. To'lov Qabul Qilish (Standard)

```javascript
// Frontend
const payment = {
  student_profile: studentId,
  subscription_plan: planId,
  base_amount: 1400000,
  discount: discountId,  // optional
  payment_method: "cash",
  period: "monthly",
  period_start: "2024-12-01",
  period_end: "2024-12-31",
  cash_register: cashRegisterId,
  notes: "Dekabr oyi uchun to'lov"
};

const response = await fetch('/api/v1/school/finance/payments/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'X-Branch-Id': branchId,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(payment)
});

const result = await response.json();
// result.id - payment ID
// result.transaction - tranzaksiya ID
// result.final_amount - yakuniy summa
```

### 2. Backend Processing

```python
# 1. Chegirmani hisoblash
if discount:
    discount_amount = discount.calculate_discount(base_amount)
else:
    discount_amount = 0

final_amount = base_amount - discount_amount

# 2. Payment yaratish
payment = Payment.objects.create(
    student_profile=student,
    branch=branch,
    subscription_plan=plan,
    base_amount=base_amount,
    discount_amount=discount_amount,
    final_amount=final_amount,
    discount=discount,
    payment_method=payment_method,
    period=period,
    payment_date=payment_date,
    period_start=period_start,
    period_end=period_end,
    cash_register=cash_register,
    notes=notes
)

# 3. Transaction yaratish
transaction = Transaction.objects.create(
    branch=branch,
    cash_register=cash_register,
    transaction_type=TransactionType.INCOME,
    status=TransactionStatus.COMPLETED,  # yoki PENDING
    amount=final_amount,
    payment_method=payment_method,
    student_profile=student,
    description=f"O'quvchi to'lovi: {student.full_name}",
    reference_number=f"PAY-{payment.id}"
)

# 4. Balanslarni yangilash
# StudentBalance
student.balance.add_amount(final_amount)

# CashRegister balance (atomic)
cash_register.update_balance(final_amount, TransactionType.INCOME)

# 5. Payment'ga transaction'ni bog'lash
payment.transaction = transaction
payment.save(update_fields=['transaction'])
```

---

## 🎨 Frontend Integratsiyasi

### 1. O'quvchi Tanlash

```javascript
// O'quvchilar ro'yxatini olish
const getStudents = async () => {
  const response = await fetch('/api/v1/school/students/', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Branch-Id': branchId
    }
  });
  return await response.json();
};

// O'quvchi balansini ko'rsatish
const getStudentBalance = async (studentId) => {
  const response = await fetch(
    `/api/v1/school/students/${studentId}/`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Branch-Id': branchId
      }
    }
  );
  const student = await response.json();
  return student.balance;  // { balance: 1500000, ... }
};
```

### 2. Abonement Tanlash

```javascript
// Abonement tariflarini olish
const getSubscriptionPlans = async () => {
  const response = await fetch(
    '/api/v1/school/finance/subscription-plans/?is_active=true',
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Branch-Id': branchId
      }
    }
  );
  return await response.json();
};

// O'quvchi sinfiga mos tarifni tanlash
const selectPlanForStudent = (plans, gradeLevel) => {
  return plans.results.find(plan => 
    plan.grade_level_min <= gradeLevel && 
    gradeLevel <= plan.grade_level_max
  );
};
```

### 3. Chegirma Tanlash (Optional)

```javascript
// Faol chegirmalarni olish
const getActiveDiscounts = async () => {
  const response = await fetch(
    '/api/v1/school/finance/discounts/?is_active=true',
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Branch-Id': branchId
      }
    }
  );
  return await response.json();
};

// Chegirmani hisoblash (frontend preview)
const calculateDiscount = (discount, baseAmount) => {
  if (discount.discount_type === 'percentage') {
    return Math.floor((baseAmount * discount.amount) / 100);
  }
  return Math.min(discount.amount, baseAmount);
};
```

### 4. To'lov Shakli

```jsx
import React, { useState, useEffect } from 'react';

function PaymentForm({ studentId, onSuccess }) {
  const [student, setStudent] = useState(null);
  const [plans, setPlans] = useState([]);
  const [discounts, setDiscounts] = useState([]);
  const [cashRegisters, setCashRegisters] = useState([]);
  
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [selectedDiscount, setSelectedDiscount] = useState(null);
  const [cashRegister, setCashRegister] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [baseAmount, setBaseAmount] = useState(0);
  
  useEffect(() => {
    // Ma'lumotlarni yuklash
    loadStudent();
    loadPlans();
    loadDiscounts();
    loadCashRegisters();
  }, [studentId]);
  
  const discountAmount = selectedDiscount 
    ? calculateDiscount(selectedDiscount, baseAmount)
    : 0;
  
  const finalAmount = baseAmount - discountAmount;
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const payment = {
      student_profile: studentId,
      subscription_plan: selectedPlan?.id,
      base_amount: baseAmount,
      discount: selectedDiscount?.id,
      payment_method: paymentMethod,
      period: 'monthly',
      period_start: new Date().toISOString().split('T')[0],
      period_end: new Date(Date.now() + 30*24*60*60*1000)
        .toISOString().split('T')[0],
      cash_register: cashRegister,
      notes: `${selectedPlan?.name} - to'lov`
    };
    
    try {
      const response = await fetch('/api/v1/school/finance/payments/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Branch-Id': branchId,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payment)
      });
      
      if (response.ok) {
        const result = await response.json();
        onSuccess(result);
        alert('To\'lov muvaffaqiyatli qabul qilindi!');
      } else {
        const error = await response.json();
        alert('Xatolik: ' + JSON.stringify(error));
      }
    } catch (error) {
      alert('Server xatolik: ' + error.message);
    }
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <h2>To'lov Qabul Qilish</h2>
      
      {/* O'quvchi ma'lumotlari */}
      <div>
        <strong>{student?.full_name}</strong>
        <p>Joriy balans: {student?.balance?.balance?.toLocaleString()} so'm</p>
      </div>
      
      {/* Abonement tarifi */}
      <select 
        value={selectedPlan?.id} 
        onChange={(e) => {
          const plan = plans.find(p => p.id === e.target.value);
          setSelectedPlan(plan);
          setBaseAmount(plan?.price || 0);
        }}
        required
      >
        <option value="">Tarif tanlang</option>
        {plans.map(plan => (
          <option key={plan.id} value={plan.id}>
            {plan.name} - {plan.price.toLocaleString()} so'm
          </option>
        ))}
      </select>
      
      {/* Chegirma */}
      <select 
        value={selectedDiscount?.id || ''} 
        onChange={(e) => {
          const discount = discounts.find(d => d.id === e.target.value);
          setSelectedDiscount(discount || null);
        }}
      >
        <option value="">Chegirmasiz</option>
        {discounts.map(discount => (
          <option key={discount.id} value={discount.id}>
            {discount.name} ({discount.discount_display})
          </option>
        ))}
      </select>
      
      {/* Summa */}
      <div>
        <label>Asosiy summa:</label>
        <input 
          type="number" 
          value={baseAmount}
          onChange={(e) => setBaseAmount(Number(e.target.value))}
          required
        />
      </div>
      
      {/* Chegirma summasi */}
      {discountAmount > 0 && (
        <div>
          <label>Chegirma:</label>
          <span>-{discountAmount.toLocaleString()} so'm</span>
        </div>
      )}
      
      {/* Yakuniy summa */}
      <div>
        <label>Yakuniy summa:</label>
        <strong>{finalAmount.toLocaleString()} so'm</strong>
      </div>
      
      {/* To'lov usuli */}
      <select 
        value={paymentMethod}
        onChange={(e) => setPaymentMethod(e.target.value)}
        required
      >
        <option value="cash">Naqd pul</option>
        <option value="card">Karta</option>
        <option value="bank_transfer">Bank o'tkazmasi</option>
        <option value="mobile_payment">Mobil to'lov</option>
      </select>
      
      {/* Kassa */}
      <select 
        value={cashRegister}
        onChange={(e) => setCashRegister(e.target.value)}
        required
      >
        <option value="">Kassa tanlang</option>
        {cashRegisters.map(cr => (
          <option key={cr.id} value={cr.id}>
            {cr.name} - {cr.balance.toLocaleString()} so'm
          </option>
        ))}
      </select>
      
      <button type="submit">To'lovni Qabul Qilish</button>
    </form>
  );
}
```

---

## 📋 Misollar

### Misol 1: Standart To'lov (Chegirmasiz)

```bash
POST /api/v1/school/finance/payments/
Content-Type: application/json
Authorization: Bearer <token>
X-Branch-Id: <branch-uuid>

{
  "student_profile": "550e8400-e29b-41d4-a716-446655440000",
  "subscription_plan": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "base_amount": 1400000,
  "payment_method": "cash",
  "period": "monthly",
  "period_start": "2024-12-01",
  "period_end": "2024-12-31",
  "cash_register": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "notes": "Dekabr oyi uchun to'lov"
}
```

**Response:**
```json
{
  "id": "new-payment-uuid",
  "final_amount": 1400000,
  "discount_amount": 0,
  "transaction": "new-transaction-uuid",
  "...": "..."
}
```

**Natija:**
- StudentBalance: +1,400,000 so'm
- CashRegister: +1,400,000 so'm
- Transaction yaratildi (COMPLETED)

---

### Misol 2: Chegirmali To'lov

```bash
POST /api/v1/school/finance/payments/

{
  "student_profile": "uuid",
  "subscription_plan": "uuid",
  "base_amount": 1400000,
  "discount": "discount-uuid",  // 10% chegirma
  "payment_method": "card",
  "period": "monthly",
  "period_start": "2024-12-01",
  "period_end": "2024-12-31",
  "cash_register": "uuid",
  "notes": "Yangi yil chegirmasi bilan"
}
```

**Response:**
```json
{
  "id": "new-payment-uuid",
  "base_amount": 1400000,
  "discount_amount": 140000,
  "final_amount": 1260000,
  "discount_name": "Yangi yil chegirmasi (10%)",
  "...": "..."
}
```

**Natija:**
- StudentBalance: +1,260,000 so'm
- CashRegister: +1,260,000 so'm

---

### Misol 3: O'quvchi To'lovlar Tarixi

```bash
GET /api/v1/school/finance/payments/?student_profile=<student-uuid>&ordering=-payment_date
Authorization: Bearer <token>
```

**Response:**
```json
{
  "count": 12,
  "results": [
    {
      "id": "uuid-1",
      "payment_date": "2024-12-22T10:30:00Z",
      "final_amount": 1260000,
      "period_display": "Oylik",
      "...": "..."
    },
    {
      "id": "uuid-2",
      "payment_date": "2024-11-20T14:15:00Z",
      "final_amount": 1400000,
      "period_display": "Oylik",
      "...": "..."
    }
  ]
}
```

---

## 🔒 Ruxsatlar (Permissions)

### CanManageFinance Permission

**Branch Admin:** ✅ To'liq ruxsat
- To'lov qabul qilish
- Balanslarni ko'rish
- Tariflar va chegirmalar boshqarish

**Super Admin:** ✅ To'liq ruxsat (barcha filiallar)

**Cashier:** ⚠️ Cheklangan
- To'lov qabul qilish
- Balanslarni ko'rish (faqat o'qish)

**Teacher/Student/Parent:** ❌ Ruxsat yo'q

---

## 🚨 Xatolar va Troubleshooting

### 400 Bad Request

```json
{
  "base_amount": ["Summa 1 dan katta bo'lishi kerak"]
}
```

```json
{
  "discount": ["Bu chegirma faol emas yoki muddati o'tgan"]
}
```

```json
{
  "cash_register": ["Bu maydon majburiy"]
}
```

### 404 Not Found

```json
{
  "detail": "O'quvchi topilmadi"
}
```

### 403 Forbidden

```json
{
  "detail": "Sizda bu operatsiyaga ruxsat yo'q"
}
```

---

## 📊 Dashboard Statistikasi

### Kunlik To'lovlar

```bash
GET /api/v1/school/finance/payments/?period_start=2024-12-22&period_end=2024-12-22
```

### Oylik Statistika

```javascript
const getMonthlyStats = async (year, month) => {
  const startDate = `${year}-${month.toString().padStart(2, '0')}-01`;
  const endDate = new Date(year, month, 0).toISOString().split('T')[0];
  
  const response = await fetch(
    `/api/v1/school/finance/payments/?period_start=${startDate}&period_end=${endDate}`,
    { headers: { ... } }
  );
  
  const data = await response.json();
  
  // Jami summa
  const totalAmount = data.results.reduce(
    (sum, payment) => sum + payment.final_amount, 
    0
  );
  
  return {
    count: data.count,
    totalAmount: totalAmount,
    payments: data.results
  };
};
```

---

## 🎓 Best Practices

### 1. Balansni Real-time Ko'rsatish

```javascript
// WebSocket yoki Polling
const updateBalance = setInterval(async () => {
  const balance = await getStudentBalance(studentId);
  setBalance(balance.balance);
}, 5000);  // Har 5 soniyada
```

### 2. Form Validatsiya

```javascript
// Chegirma va summa hisoblashni real-time ko'rsatish
useEffect(() => {
  if (selectedDiscount && baseAmount > 0) {
    const discount = calculateDiscount(selectedDiscount, baseAmount);
    setDiscountAmount(discount);
    setFinalAmount(baseAmount - discount);
  }
}, [selectedDiscount, baseAmount]);
```

### 3. Xatoliklarni Boshqarish

```javascript
try {
  const response = await createPayment(payment);
  if (!response.ok) {
    const error = await response.json();
    // Field-specific errors
    Object.keys(error).forEach(field => {
      showFieldError(field, error[field]);
    });
  }
} catch (error) {
  showGlobalError('Tarmoq xatolik. Qaytadan urinib ko\'ring.');
}
```

### 4. Tasdiqlash (Confirmation)

```javascript
const confirmPayment = (amount) => {
  return window.confirm(
    `${amount.toLocaleString()} so'm to'lovni qabul qilishni tasdiqlaysizmi?`
  );
};

if (confirmPayment(finalAmount)) {
  await createPayment(payment);
}
```

---

## 📚 Qo'shimcha Resurslar

- [Transaction API Documentation](./finance-transactions-api.md)
- [Finance Optimization Guide](./finance-optimization-guide.md)
- [Load Testing Guide](./load-testing-guide.md)

---

**API Versiya:** 1.0  
**Oxirgi Yangilanish:** 2024-12-23  
**Backend:** Django 5.2.6 + DRF + PostgreSQL  
**Authentication:** JWT + X-Branch-Id Header
