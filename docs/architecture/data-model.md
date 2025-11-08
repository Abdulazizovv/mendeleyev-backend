# Ma'lumotlar modeli (ER)

Quyida asosiy entitilar va ularning bog'liqliklari keltirilgan. UUID PK ishlatiladi.

```mermaid
erDiagram
  USERS ||--o{ USER_BRANCH : has
  BRANCH ||--o{ USER_BRANCH : has

  USERS {
    uuid id PK
    string phone_number
    bool phone_verified
    string first_name
    string last_name
    string email
    datetime date_joined
  }

  BRANCH {
    uuid id PK
    string name
    string slug
    enum type
    enum status
    string address
    string phone_number
    string email
  }

  USER_BRANCH {
    uuid id PK
    uuid user_id FK -> USERS.id
    uuid branch_id FK -> BRANCH.id
    enum role
    string title
  }
```

- `User.phone_number` — unique, login identifikatori.
- `User.phone_verified` — OTP tasdiqlash flagi.
- `Branch.status` — `pending|active|inactive|archived`. JWT scope faqat `active` uchun.
- `UserBranch.role` — `super_admin|branch_admin|teacher|student|parent`.

Qo'shimcha entitilar (keyinchalik): darslar, fanlar, jadval, baholash, to'lovlar va h.k.
