# 📚 Staff Management API Documentation

Xodimlar boshqaruvi uchun to'liq API dokumentatsiyasi va frontend integratsiya qo'llanmasi.

## 📄 Hujjatlar

### 1. [API Reference - hr.md](./hr.md)
**Maqsad:** Backend API endpoint'larining to'liq texnik hujjatlari

**Mavzular:**
- API endpoints (CRUD operations)
- Request/Response schemas
- Query parameters
- Business logic
- Permissions
- Validation rules
- Error handling

**Kimga kerak:** Backend developers, API consumers

---

### 2. [Frontend Integration Guide - hr-frontend-integration.md](./hr-frontend-integration.md)
**Maqsad:** Frontend dasturchilar uchun praktik integratsiya qo'llanmasi

**Mavzular:**
- TypeScript type definitions
- React Query hooks
- Complete component examples
- Error handling patterns
- State management
- Utility functions
- Best practices

**Kimga kerak:** Frontend developers (React, TypeScript)

---

### 3. [Staff Management Design - staff-management.md](./staff-management.md)
**Maqsad:** API'ning tushuntirilgan versiyasi (README format)

**Mavzular:**
- Architecture overview
- Model relationships
- API endpoints summary
- Integration examples
- Migration guide

**Kimga kerak:** Full-stack developers, project managers

---

## 🚀 Quick Start

### Backend Developer
```bash
# API hujjatlarini o'qing
cat docs/api/hr.md

# Django serverni ishga tushiring (Docker)
docker compose restart django

# API'ni test qiling
curl -H "Authorization: Bearer TOKEN" http://localhost:8000/api/v1/branches/staff/
```

### Frontend Developer
```bash
# Frontend integration guide'ni o'qing
cat docs/api/hr-frontend-integration.md

# TypeScript types'ni copy qiling
# React Query hooks'ni implement qiling
# Example components'dan foydalaning
```

---

## 🎯 API Response Optimization

**⚡ List API** - Ixcham ma'lumotlar (faqat zarur maydonlar)
```
GET /api/v1/branches/staff/
→ 13 fields per staff (fast, efficient)
```

**📊 Detail API** - To'liq ma'lumotlar (barcha tegishli ma'lumotlar)
```
GET /api/v1/branches/staff/{id}/
→ 35+ fields + transactions + payments (complete)
```

**Benefits:**
- ✅ 60-70% smaller list responses
- ✅ Single request for complete details
- ✅ No multiple API calls needed
- ✅ Optimized for mobile and web

See: [Staff API Optimization](./staff-api-optimization.md)

---

## 📊 Architecture Summary

```
User → BranchMembership (Single Source of Truth)
           ↓
    Role (Position/Job Title)
           ↓
    BalanceTransaction (Financial Operations)
           ↓
    SalaryPayment (Payment Records)
```

**Key Features:**
- ✅ Unified model architecture (no duplication)
- ✅ Complete employment tracking
- ✅ Atomic balance operations
- ✅ Soft delete support
- ✅ Comprehensive audit trail
- ✅ RESTful API design
- ✅ Full TypeScript support

---

## 🔗 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/branches/staff/` | Xodimlar ro'yxati |
| POST | `/api/v1/branches/staff/` | Yangi xodim qo'shish |
| GET | `/api/v1/branches/staff/{id}/` | Xodim tafsilotlari |
| PATCH | `/api/v1/branches/staff/{id}/` | Xodim yangilash |
| DELETE | `/api/v1/branches/staff/{id}/` | Xodim o'chirish |
| GET | `/api/v1/branches/staff/stats/` | Statistika |
| POST | `/api/v1/branches/staff/{id}/add_balance/` | Balans qo'shish |
| POST | `/api/v1/branches/staff/{id}/pay_salary/` | Oylik to'lash |

**Base URL:** `/api/v1/branches/staff/`  
**Auth:** Bearer token required

---

## 💡 Examples

### Fetch Staff List (React)
```typescript
const { data } = useQuery({
  queryKey: ['staff'],
  queryFn: async () => {
    const res = await fetch('/api/v1/branches/staff/', { headers });
    return res.json();
  },
});
```

### Create Staff (React)
```typescript
const createStaff = useMutation({
  mutationFn: async (data) => {
    const res = await fetch('/api/v1/branches/staff/', {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    });
    return res.json();
  },
});
```

---

## 📚 Related Documentation

- [Models Architecture](../models-architecture.md)
- [Permissions & RBAC](../permissions-rbac.md)
- [Branch Management](./branch.md)
- [Frontend Auth Integration](../frontend/auth-integration.md)

---

## 🔄 Migration Notes

**Date:** 2024-12-13

**Changes:**
- ❌ HR app removed (StaffRole, StaffProfile deprecated)
- ✅ BranchMembership enhanced (complete staff data)
- ✅ Role enhanced (salary ranges)
- ✅ BalanceTransaction added
- ✅ SalaryPayment added
- ✅ API endpoints moved to `/api/branch/staff/`

**Action Required:** Update frontend to use new endpoints

---

## 🆘 Support

**Issues?** Check troubleshooting sections in:
- `hr.md` - Backend issues
- `hr-frontend-integration.md` - Frontend issues

**Contact:** Mendeleyev Backend Team

---

**Last Updated:** 2024-12-13  
**Version:** 2.0.0
