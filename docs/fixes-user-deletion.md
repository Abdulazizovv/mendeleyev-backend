# User O'chirish Muammosi Tuzatildi

## Muammo

User o'chirilganda quyidagi xatolik sodir bo'lardi:
```
IntegrityError: update or delete on table "users_user" violates foreign key constraint 
"users_userbranch_user_id_da0431d7_fk_users_user_id" on table "users_userbranch"
```

## Sabab

Database'da hali ham eski `users_userbranch` jadvali mavjud bo'lishi mumkin, garchi u allaqachon migratsiya orqali o'chirilgan bo'lsa ham. Bu jadval User bilan bog'liq constraint'ga ega.

## Yechim

`UserAdmin.delete_model()` metodida eski jadvalni tekshirish va agar mavjud bo'lsa, uni tozalash qo'shildi.

## Bajarilgan O'zgarishlar

1. **auth/users/admin.py** - `delete_model()` metodi qo'shildi
   - Eski `users_userbranch` jadvalini tekshiradi
   - Agar mavjud bo'lsa, User bilan bog'liq yozuvlarni o'chiradi
   - Keyin oddiy o'chirishni davom ettiradi

## Qo'shimcha Yechim

Agar muammo davom etsa, database'da quyidagi SQL so'rovni bajarish mumkin:

```sql
-- Eski jadvalni to'liq o'chirish (agar mavjud bo'lsa)
DROP TABLE IF EXISTS users_userbranch CASCADE;
```

Yoki migratsiyani qayta ishga tushirish:
```bash
python manage.py migrate users 0005 --fake
```

