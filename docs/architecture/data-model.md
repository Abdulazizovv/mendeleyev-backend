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


Qo'shimcha entitilar (keyinchalik): darslar, fanlar, jadval, baholash, to'lovlar va h.k.

### BranchMembership (Finalized Model)

- Replaces legacy `UserBranch` as the canonical RBAC link between User, Branch, and Role.
- Compatible with JWT branch claims (`br`, `br_role`) and server-side permissions.
- Used by role-specific profiles: TeacherProfile, StudentProfile, ParentProfile, AdminProfile.
  Existing profile relations continue functioning via the shared membership row.

#### AdminProfile

- One-to-one with membership row (linked via legacy `users.UserBranch` concrete model for compatibility).
- Fields:
  - is_super_admin: bool — true when role is `super_admin`.
  - managed_branches: M2M to Branch — optional UI scoping list for branch_admins.
  - title, notes: optional display fields.
- Provisioning strategy: auto-created by signals on membership save if role in {branch_admin, super_admin}.
  Role transitions are handled idempotently; previous role profiles are kept. TODO: future soft-delete policy.
