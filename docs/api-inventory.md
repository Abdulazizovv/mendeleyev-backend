# API Endpointlar Inventarizatsiyasi

Bu hujjat barcha mavjud API endpointlarini ro'yxatga oladi va ularning holatini ko'rsatadi.

## Auth API (`/api/v1/auth/`)

### ✅ Ishlayapti va test qilingan

1. **POST** `/api/v1/auth/refresh/` - Token yangilash
   - View: `RefreshTokenView`
   - Test: ✅ `test_refresh_view.py`

2. **GET** `/api/v1/auth/me/` - Joriy foydalanuvchi ma'lumotlari
   - View: `MeView`
   - Test: ✅ `test_me_view.py`
   - Yangilandi: `effective_role`, `salary`, `balance` qo'shildi

3. **POST** `/api/v1/auth/login/` - Login
   - View: `LoginView`
   - Test: ✅ `test_auth_flow.py`, `test_branch_jwt.py`

4. **POST** `/api/v1/auth/password/reset/request-otp/` - Parol tiklash uchun OTP so'rash
   - View: `PasswordResetRequestView`
   - Test: ✅ `test_auth_flow.py`

5. **POST** `/api/v1/auth/password/reset/confirm/` - Parol tiklashni tasdiqlash
   - View: `PasswordResetConfirmView`
   - Test: ✅ `test_auth_flow.py`

6. **POST** `/api/v1/auth/password/change/` - Parolni o'zgartirish
   - View: `PasswordChangeView`
   - Test: ✅ `test_auth_flow.py`

7. **POST** `/api/v1/auth/phone/check/` - Telefon raqamini tekshirish
   - View: `PhoneCheckView`
   - Test: ✅ `test_auth_flow.py`

8. **POST** `/api/v1/auth/phone/verification/request/` - OTP so'rash
   - View: `PhoneVerificationRequestView`
   - Test: ✅ `test_auth_flow.py`

9. **POST** `/api/v1/auth/phone/verification/confirm/` - OTP tasdiqlash
   - View: `PhoneVerificationConfirmView`
   - Test: ✅ `test_auth_flow.py`

10. **POST** `/api/v1/auth/password/set/` - Parol o'rnatish
    - View: `PasswordSetView`
    - Test: ✅ `test_auth_flow.py`

11. **GET** `/api/v1/auth/branches/mine/` - Foydalanuvchining filiallari
    - View: `MyBranchesView`
    - Test: ✅ `test_branch_jwt.py`
    - Yangilandi: `effective_role`, `salary`, `balance` qo'shildi

12. **POST** `/api/v1/auth/branch/switch/` - Filialni o'zgartirish
    - View: `SwitchBranchView`
    - Test: ✅ `test_branch_jwt.py`

### ⚠️ Eslatma: Register endpointlari

13. **POST** `/api/v1/auth/register/request-otp/` - Ro'yxatdan o'tish uchun OTP so'rash
    - View: `RegisterRequestOTPView`
    - Test: ❓ Test yo'q

14. **POST** `/api/v1/auth/register/confirm/` - Ro'yxatdan o'tishni tasdiqlash
    - View: `RegisterConfirmView`
    - Test: ❓ Test yo'q

### ❓ Eski endpointlar (tekshirish kerak)

15. **POST** `/api/v1/auth/request-otp/` - Eski OTP so'rash endpointi
    - View: `RequestOTPView`
    - Eslatma: Bu endpoint hali ham mavjud, lekin yangi flowda `phone/verification/request` ishlatiladi
    - Tavsiya: Deprecate qilish yoki o'chirish

16. **POST** `/api/v1/auth/verify-otp/` - Eski OTP tasdiqlash endpointi
    - View: `VerifyOTPView`
    - Eslatma: Bu endpoint hali ham mavjud, lekin yangi flowda `phone/verification/confirm` ishlatiladi
    - Tavsiya: Deprecate qilish yoki o'chirish

## Profile API (`/api/v1/profile/`)

### ✅ Ishlayapti

1. **GET** `/api/v1/profile/me/` - Global profil
   - View: `MyProfileView`
   - Test: ❓ Test yo'q

2. **PATCH** `/api/v1/profile/me/` - Global profilni yangilash
   - View: `MyProfileView`
   - Test: ❓ Test yo'q

3. **GET** `/api/v1/profile/branch/<branch_id>/` - Filialga xos profil
   - View: `MyBranchProfileView`
   - Test: ❓ Test yo'q

4. **PATCH** `/api/v1/profile/branch/<branch_id>/` - Filialga xos profilni yangilash
   - View: `MyBranchProfileView`
   - Test: ❓ Test yo'q

## Branch API (`/api/branches/`)

### ✅ Yangi endpointlar (yangi yaratilgan)

1. **GET** `/api/branches/managed/` - Admin uchun boshqariladigan filiallar
   - View: `ManagedBranchesView`
   - Test: ✅ `test_managed_branches.py`

2. **PATCH** `/api/branches/managed/` - Managed branches ro'yxatini yangilash (SuperAdmin)
   - View: `ManagedBranchesView`
   - Test: ✅ `test_managed_branches.py`

3. **GET** `/api/branches/<branch_id>/roles/` - Filialdagi rollar ro'yxati
   - View: `RoleListView`
   - Test: ❓ Test yo'q (YANGI)

4. **POST** `/api/branches/<branch_id>/roles/` - Yangi rol yaratish
   - View: `RoleListView`
   - Test: ❓ Test yo'q (YANGI)

5. **GET** `/api/branches/<branch_id>/roles/<id>/` - Rol detallari
   - View: `RoleDetailView`
   - Test: ❓ Test yo'q (YANGI)

6. **PATCH** `/api/branches/<branch_id>/roles/<id>/` - Rolni tahrirlash
   - View: `RoleDetailView`
   - Test: ❓ Test yo'q (YANGI)

7. **DELETE** `/api/branches/<branch_id>/roles/<id>/` - Rolni o'chirish
   - View: `RoleDetailView`
   - Test: ❓ Test yo'q (YANGI)

8. **GET** `/api/branches/<branch_id>/memberships/` - Filialdagi a'zoliklar ro'yxati
   - View: `MembershipListView`
   - Test: ❓ Test yo'q (YANGI)

9. **POST** `/api/branches/<branch_id>/memberships/<membership_id>/balance/` - Balansni yangilash
   - View: `BalanceUpdateView`
   - Test: ❓ Test yo'q (YANGI)

## Students API (`/api/v1/school/students/`)

### ✅ Ishlayapti

1. **GET** `/api/v1/school/students/` - O'quvchilar ro'yxati
   - View: `StudentListView`
   - Test: ❓ Test yo'q
   - Features: Pagination, filtering, search, ordering

2. **POST** `/api/v1/school/students/create/` - O'quvchi yaratish
   - View: `StudentCreateView`
   - Test: ❓ Test yo'q
   - Features: 
     - Abonement tanlash (`subscription_plan_id`)
     - Yaqinlarni belgilash (avtomatik user/parent membership yaratish)
     - Hujjat ma'lumotlarini kiritish (passport, birth_certificate, nationality)
     - Sinfga biriktirish

3. **GET** `/api/v1/school/students/{student_id}/` - O'quvchi ma'lumotlari
   - View: `StudentDetailView`
   - Test: ❓ Test yo'q
   - Features: To'liq moliyaviy ma'lumotlar (balance, transactions, payments)

4. **PATCH** `/api/v1/school/students/{student_id}/documents/` - Hujjatlar yangilash
   - View: `StudentDocumentsUpdateView`
   - Test: ❓ Test yo'q
   - Features: Birth certificate, passport, nationality yangilash

5. **GET** `/api/v1/school/students/{student_id}/relatives/` - O'quvchi yaqinlari
   - View: `StudentRelativeListView`
   - Test: ❓ Test yo'q

6. **POST** `/api/v1/school/students/{student_id}/relatives/` - Yaqin qo'shish
   - View: `StudentRelativeListView`
   - Test: ❓ Test yo'q

7. **GET** `/api/v1/school/students/check-user/` - User mavjudligini tekshirish
   - View: `UserCheckView`
   - Test: ❓ Test yo'q

8. **POST** `/api/v1/school/students/check-user/` - User mavjudligini tekshirish
   - View: `UserCheckView`
   - Test: ❓ Test yo'q

9. **GET** `/api/v1/school/students/check-relative/` - Yaqin mavjudligini tekshirish
   - View: `StudentRelativeCheckView`
   - Test: ❓ Test yo'q

10. **POST** `/api/v1/school/students/check-relative/` - Yaqin mavjudligini tekshirish
    - View: `StudentRelativeCheckView`
    - Test: ❓ Test yo'q

## Bot API

1. **POST** `/api/telegram/webhook/<token>/` - Telegram webhook
   - View: `telegram_webhook`
   - Test: ✅ `test_webhook.py`

2. **GET** `/health/` - Health check
   - View: `health_check`
   - Test: ❓ Test yo'q

3. **GET** `/bot-status/` - Bot holati
   - View: `bot_status`
   - Test: ❓ Test yo'q

## API Docs

1. **GET** `/api/schema/` - OpenAPI schema
2. **GET** `/api/docs/` - Swagger UI
3. **GET** `/api/redoc/` - ReDoc

## Xulosa

### ✅ Tuzatilgan muammolar

1. **Syntax xatosi** - `apps/branch/admin.py` da 93-qatorda ortiqcha "k" belgisi o'chirildi
2. **UserBranch import xatolari** - Barcha test fayllarda `UserBranch` → `BranchMembership` ga o'zgartirildi
3. **BranchMembershipSerializer JSON serialization** - `from_membership` metodida `_membership` key o'chirildi, faqat dict qaytaradi
4. **Eski endpointlar o'chirildi** - `RequestOTPView` va `VerifyOTPView` views.py dan olib tashlandi (urls.py da allaqachon yo'q edi)
5. **MembershipListView POST** - Create qilishni bloklash uchun 405 qaytaradi

### ✅ Test natijalari

**Barcha testlar o'tdi: 38/38 ✅**

- `auth.users.tests` - ✅ 15/15
- `auth.profiles.tests` - ✅ 9/9
- `apps.branch.tests` - ✅ 10/10
- `apps.botapp.tests` - ✅ 4/4

### ⚠️ Test yo'q endpointlar (test yozish kerak)

1. **Register endpointlari**:
   - `POST /api/v1/auth/register/request-otp/`
   - `POST /api/v1/auth/register/confirm/`

2. **Profile endpointlari**:
   - `GET /api/v1/profile/me/`
   - `PATCH /api/v1/profile/me/`
   - `GET /api/v1/profile/branch/<branch_id>/`
   - `PATCH /api/v1/profile/branch/<branch_id>/`

3. **Yangi Role va Membership endpointlari** (9 ta):
   - `GET /api/branches/<branch_id>/roles/`
   - `POST /api/branches/<branch_id>/roles/`
   - `GET /api/branches/<branch_id>/roles/<id>/`
   - `PATCH /api/branches/<branch_id>/roles/<id>/`
   - `DELETE /api/branches/<branch_id>/roles/<id>/`
   - `GET /api/branches/<branch_id>/memberships/`
   - `POST /api/branches/<branch_id>/memberships/<membership_id>/balance/`

4. **Health check va bot status**:
   - `GET /health/`
   - `GET /bot-status/`

### 📝 API holati

**Jami endpointlar**: 40+
- ✅ **Ishlayapti va test qilingan**: 20+
- ⚠️ **Ishlayapti, lekin test yo'q**: 20+ (Students API, Profile API, va boshqalar)
- ❌ **O'chirilgan**: 2 (RequestOTPView, VerifyOTPView)

### 🔧 Keyingi qadamlarni tavsiya

1. **Testlar yozish** - Yangi endpointlar uchun testlar
2. **API hujjatlashtirish** - Swagger/ReDoc da barcha endpointlar to'liq ko'rsatilgan
3. **Performance testing** - Katta ma'lumotlar bilan test qilish
4. **Security audit** - Permissions va authentication to'g'ri ishlashini tekshirish

