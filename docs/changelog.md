# Changelog

## 2024-12-02 - Shaxsiy Raqam Generatsiyasi Takomillashtirildi

### Yangi Xususiyatlar

1. **Shaxsiy Raqam Format O'zgartirildi**
   - **Eski format**: `ST-YYYY-NNNN` (masalan: ST-2024-0001)
   - **Yangi format**: `{BRANCH_CODE}-{ACADEMIC_YEAR_SHORT}-{ORDER}` (masalan: TAS-24-0001)
   - Har bir filial uchun alohida raqamlar
   - Har bir akademik yil uchun alohida raqamlar
   - Format tushuntirish:
     - `BRANCH_CODE`: Filial kodi (masalan: TAS, SAM, BUK) - agar yo'q bo'lsa, "ST" ishlatiladi
     - `ACADEMIC_YEAR_SHORT`: Akademik yil qisqa versiyasi (masalan: "2024-2025" -> "24")
     - `ORDER`: Tartib raqami (4 xonali, masalan: 0001, 0002)

2. **Branch Modeliga `code` Field Qo'shildi**
   - `code` (CharField, max_length=10, unique=True)
   - Filial kodi (masalan: TAS, SAM, BUK)
   - Shaxsiy raqam generatsiyasi uchun ishlatiladi
   - Migration: `0010_add_branch_code.py`

### O'zgarishlar

1. **StudentProfile.generate_personal_number()** yangilandi
   - Filial va akademik yil bo'yicha raqamlar generatsiya qiladi
   - Joriy akademik yilni avtomatik aniqlaydi
   - Agar akademik yil bo'lmasa, joriy yilni ishlatadi

### Migration

```bash
python manage.py makemigrations branch --name add_branch_code
python manage.py migrate branch
```

---

## 2024-11-27 - O'quvchi Yaratish API Yaxshilandi

### Yangi Xususiyatlar

1. **Abonement Tanlash**
   - O'quvchi yaratishda `subscription_plan_id` orqali abonement tanlash mumkin
   - Abonement tanlansa, avtomatik `Payment` va `Transaction` yaratiladi
   - Agar kassa bo'lmasa, avtomatik "Asosiy kassa" yaratiladi

2. **Yaqinlar Avtomatik Yaratish**
   - Yaqinlar belgilanganda har bir yaqin uchun:
     - `User` yaratiladi/yangilanadi
     - `BranchMembership` (role=PARENT) yaratiladi
     - `StudentRelative` yaratiladi
   - Agar yaqin allaqachon boshqa rolda bo'lsa, xatolik qaytariladi

3. **Hujjat Ma'lumotlari**
   - `birth_certificate` - Tu'gilganlik guvohnoma rasmi (file)
   - `passport_number` - Pasport yoki ID karta raqami
   - `nationality` - Millati
   - `additional_fields` - Qo'shimcha hujjat ma'lumotlari (JSON)

4. **Hujjatlar Yangilash Endpointi**
   - `PATCH /api/v1/school/students/{student_id}/documents/` - O'quvchi hujjatlarini yangilash
   - `StudentDocumentsUpdateSerializer` yaratildi

### Tuzatilgan Muammolar

1. **IntegrityError Tuzatildi**
   - O'quvchi yaratishda `BranchMembership` unique constraint xatosi tuzatildi
   - Endi barcha roldagi membershiplar tekshiriladi
   - Agar user o'sha branchda boshqa rolda bo'lsa, aniq xatolik xabari qaytariladi

### API O'zgarishlari

**StudentCreateSerializer:**
- `subscription_plan_id` (UUID, optional) - Abonement tarifi ID
- `relatives` (List[Dict], optional) - Yaqinlar ro'yxati
- `birth_certificate` (File, optional) - Tu'gilganlik guvohnoma rasmi
- `passport_number` (String, optional) - Pasport raqami
- `nationality` (String, optional) - Millati

**Yangi Endpoint:**
- `PATCH /api/v1/school/students/{student_id}/documents/` - Hujjatlar yangilash

---

## Phase 4 (RBAC Admin Profiles)

- Added AdminProfile model for admin-class memberships (branch_admin, super_admin).
- Auto-provision AdminProfile via signals on membership save (both legacy UserBranch and canonical BranchMembership).
- Integrated AdminProfile into BranchMembershipSerializer.role_data for admin roles.
- Registered AdminProfile in Django admin and as inline on BranchMembership admin.
- Frontend docs updated with AdminProfile examples and UI guidance (managed_branches selector).
- Backward compatible: no schema changes required; relations continue to target the shared membership table via legacy concrete model.
