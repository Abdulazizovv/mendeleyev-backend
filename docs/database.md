# Ma'lumotlar bazasi dizayni

Asosiy jadvallar va munosabatlar:

```mermaid
erDiagram
  USER ||--o{ USER_BRANCH : has
  BRANCH ||--o{ USER_BRANCH : has

  USER {
    uuid id PK
    string phone_number UNIQUE
    string first_name
    string last_name
    bool is_active
    datetime created_at
    datetime updated_at
    datetime deleted_at nullable
  }

  BRANCH {
    uuid id PK
    string name
    enum type  // school | learning_center
    string slug UNIQUE
    string location
    datetime created_at
    datetime updated_at
    datetime deleted_at nullable
  }

  USER_BRANCH {
    uuid id PK
    uuid user FK -> USER.id
    uuid branch FK -> BRANCH.id
    enum role // super_admin? (yo'q, global), branch_admin | teacher | student
    bool is_active
    datetime created_at
  }
```

- Soft delete: `deleted_at` orqali
- Indexlar: `phone_number`, `slug`, `(user, branch)` unique constraint

Amaldagi kodlar: `apps/branch`, `apps/common`, `auth/users`, `auth/profiles`.
