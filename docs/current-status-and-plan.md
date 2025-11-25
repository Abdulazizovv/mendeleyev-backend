# Loyiha Holati va Davom Ettirish Rejasi

## ✅ Tayyor bo'lgan modullar

### 1. Asosiy Infrastruktura
- ✅ **Auth System**: OTP verifikatsiya, parol o'rnatish, JWT tokenlar
- ✅ **Branch App**: Filiallar boshqaruvi, rollar, a'zoliklar
- ✅ **RBAC**: Branch-scoped permissions, rollar (super_admin, branch_admin, teacher, student, parent)
- ✅ **Admin Profiles**: AdminProfile modeli, signals integratsiyasi
- ✅ **Common App**: OTP service, logging, Celery tasks
- ✅ **Bot App**: Telegram webhook integratsiyasi
- ✅ **Swagger/OpenAPI**: drf-spectacular konfiguratsiyasi

### 2. School Module - Academic
- ✅ **AcademicYear model**: Akademik yillar boshqaruvi
- ✅ **Quarter model**: Choraklar boshqaruvi
- ✅ **API Endpoints**: CRUD operatsiyalar, joriy akademik yil
- ✅ **Serializers**: To'liq serializerlar
- ✅ **Views**: List, Detail, Create, Update, Delete
- ✅ **URLs**: Routing tayyor

## ❌ Qolgan ishlar

### 1. School Module - Qolgan Modullar

#### 1.1. Classes Module (Sinflar) - **PRIORITY 1**
**Status**: Bo'sh directory mavjud, hech narsa yozilmagan

**Kerakli ishlar:**
- [ ] `Class` model yaratish
- [ ] `ClassStudent` through model (o'quvchilarni sinfga biriktirish)
- [ ] Serializers (ClassSerializer, ClassCreateSerializer, ClassStudentSerializer)
- [ ] Views (ListCreate, RetrieveUpdateDestroy, Students management)
- [ ] URLs routing
- [ ] Admin panel integratsiyasi
- [ ] Testlar

**API Endpoints:**
- `GET/POST /api/school/branches/{branch_id}/classes/`
- `GET/PATCH/DELETE /api/school/branches/{branch_id}/classes/{id}/`
- `GET/POST /api/school/classes/{id}/students/`
- `DELETE /api/school/classes/{id}/students/{student_id}/`

**Kutilgan vaqt**: 2-3 kun

---

#### 1.2. Subjects Module (Fanlar) - **PRIORITY 1**
**Status**: Bo'sh directory mavjud

**Kerakli ishlar:**
- [ ] `Subject` model yaratish
- [ ] `ClassSubject` model (sinfga fan biriktirish, o'qituvchi tayinlash)
- [ ] Serializers
- [ ] Views
- [ ] URLs
- [ ] Admin panel
- [ ] Testlar

**API Endpoints:**
- `GET/POST /api/school/branches/{branch_id}/subjects/`
- `GET/PATCH/DELETE /api/school/branches/{branch_id}/subjects/{id}/`
- `GET/POST /api/school/classes/{class_id}/subjects/`
- `DELETE /api/school/classes/{class_id}/subjects/{id}/`

**Kutilgan vaqt**: 2-3 kun

---

#### 1.3. Rooms Module (Bino va Xonalar) - **PRIORITY 2**
**Status**: Bo'sh directory mavjud

**Kerakli ishlar:**
- [ ] `Building` model
- [ ] `Room` model
- [ ] Serializers
- [ ] Views
- [ ] URLs
- [ ] Admin panel
- [ ] Testlar

**Kutilgan vaqt**: 1-2 kun

---

#### 1.4. Schedule Module (Dars Jadvali) - **PRIORITY 2**
**Status**: Bo'sh directory mavjud

**Kerakli ishlar:**
- [ ] `Schedule` model
- [ ] Jadval validatsiyasi (vaqt to'qnashuvi, xona bandligi)
- [ ] Serializers
- [ ] Views (sinf, o'qituvchi, xona bo'yicha filter)
- [ ] URLs
- [ ] Admin panel
- [ ] Testlar

**Kutilgan vaqt**: 3-4 kun

---

#### 1.5. Attendance Module (Davomat) - **PRIORITY 3**
**Status**: Bo'sh directory mavjud

**Kerakli ishlar:**
- [ ] `Attendance` model
- [ ] Bulk attendance operations
- [ ] Serializers
- [ ] Views
- [ ] URLs
- [ ] Admin panel
- [ ] Testlar

**Kutilgan vaqt**: 2-3 kun

---

#### 1.6. Grades Module (Baholash) - **PRIORITY 3**
**Status**: Bo'sh directory mavjud

**Kerakli ishlar:**
- [ ] `Grade` model
- [ ] `GradeSummary` model (yoki computed property)
- [ ] Baho hisoblash logikasi (o'rtacha, foiz)
- [ ] Serializers
- [ ] Views
- [ ] URLs
- [ ] Admin panel
- [ ] Testlar

**Kutilgan vaqt**: 4-5 kun

---

#### 1.7. Finance Module (Moliya) - **PRIORITY 4**
**Status**: Bo'sh directory mavjud

**Kerakli ishlar:**
- [ ] `SubscriptionPlan` model
- [ ] `StudentSubscription` model
- [ ] `Payment` model
- [ ] `Discount` model
- [ ] Serializers
- [ ] Views
- [ ] URLs
- [ ] Admin panel
- [ ] Testlar

**Kutilgan vaqt**: 5-6 kun

---

### 2. Super Admin API - **PRIORITY 1**
**Status**: Faqat `IsSuperAdmin` permission class mavjud, API endpointlar yo'q

**Kerakli ishlar:**
- [ ] `apps/super_admin/` package yaratish
- [ ] Dashboard stats endpoint
- [ ] Filiallar CRUD (barcha filiallar)
- [ ] Foydalanuvchilar CRUD (barcha foydalanuvchilar)
- [ ] A'zoliklar CRUD (barcha a'zoliklar)
- [ ] Rollar CRUD
- [ ] Moliya statistika
- [ ] Hisobotlar
- [ ] Serializers
- [ ] URLs
- [ ] Testlar

**Kutilgan vaqt**: 5-7 kun

---

## 📋 Davom Ettirish Rejasi (Tavsiya etilgan tartib)

### Bosqich 1: Asosiy School Modullari (1-2 hafta)
1. **Classes Module** (2-3 kun)
   - Sinflar boshqaruvi
   - O'quvchilarni sinfga biriktirish
   
2. **Subjects Module** (2-3 kun)
   - Fanlar boshqaruvi
   - Sinfga fan biriktirish
   
3. **Rooms Module** (1-2 kun)
   - Binolar va xonalar
   - Schedule uchun asos

### Bosqich 2: Jadval va Davomat (1 hafta)
4. **Schedule Module** (3-4 kun)
   - Dars jadvali
   - Validatsiyalar

5. **Attendance Module** (2-3 kun)
   - Davomat belgilash
   - Bulk operations

### Bosqich 3: Baholash va Moliya (1.5 hafta)
6. **Grades Module** (4-5 kun)
   - Baholar
   - Hisob-kitoblar

7. **Finance Module** (5-6 kun)
   - Abonementlar
   - To'lovlar
   - Chegirmalar

### Bosqich 4: Super Admin API (1 hafta)
8. **Super Admin API** (5-7 kun)
   - Dashboard
   - CRUD operatsiyalar
   - Statistika va hisobotlar

### Bosqich 5: Integration va Test (3-5 kun)
9. **Integration**
   - Barcha modullarni integratsiya
   - Integration testlar
   - Performance optimizatsiya

---

## 🎯 Keyingi Qadam (Hozirgi vazifa)

**Tavsiya**: **Classes Module** dan boshlash

**Sabab:**
1. Academic modul tayyor, Classes unga bog'liq
2. Subjects va Schedule ham Classes ga bog'liq
3. Asosiy modul, boshqalar unga tayanadi

**Keyingi vazifalar:**
1. Classes Module implementatsiya
2. Subjects Module implementatsiya
3. Rooms Module implementatsiya
4. Keyin Schedule, Attendance, Grades, Finance

---

## 📝 Eslatmalar

- Barcha modullar `apps/common/models.py` dagi `BaseModel` dan meros oladi
- Barcha viewlar `HasBranchRole` permission ishlatadi
- Barcha viewlar `AuditTrailMixin` ishlatadi
- Swagger dokumentatsiya `drf_spectacular` bilan yoziladi
- Testlar har bir modul uchun yozilishi kerak

---

## 🔄 Roadmap Status

### MVP (boshlang'ich)
- [x] Branch app (tayyor)
- [x] Auth: OTP flow, SimpleJWT integratsiyasi
- [x] RBAC: UserBranch through modeli, minimal permissionlar
- [x] Swagger: drf-spectacular konfiguratsiyasi
- [x] Docker dev/CI ishga tushirish skriptlari

### v1 kengaytmalar
- [ ] School Module (qisman: Academic tayyor, qolganlari yo'q)
- [ ] Super Admin API
- [ ] Payment (Stripe) integratsiyasi
- [ ] Attendance (AI/yuz tanish) PoC
- [ ] LMS modul: kurslar, darslar, topshiriqlar
- [ ] Audit loglar va soft-delete recovery
- [ ] Multi-tenant optimizatsiyalar

