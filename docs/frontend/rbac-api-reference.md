# RBAC API Reference for Frontend

This guide explains how React/Next.js clients should consume the Mendeleyev Backend RBAC APIs.

## Overview

- A user can belong to multiple branches. Each membership has a role.
- JWT tokens can be global or branch-scoped. When scoped, the payload includes the selected branch and role.

Example JWT values (response body fields):

```json
{
  "access": "...",
  "refresh": "...",
  "br": "<uuid>",
  "br_role": "teacher"
}
```

- Canonical membership model: `apps.branch.models.BranchMembership`
- Legacy `auth.users.models.UserBranch` is deprecated but still readable.

## Branch switching

Endpoint: `POST /api/v1/auth/branch/switch/`

Request:

```json
{
  "refresh": "<refresh-token>",
  "branch_id": "<uuid>"
}
```

Response (new scoped tokens):

```json
{
  "access": "<access>",
  "refresh": "<refresh>",
  "br": "<uuid>",
  "br_role": "teacher" // present for regular users with a role
}
```

Client guidance:
- Always replace both access and refresh with the returned values.
- Persist `br` and `br_role` in app state for role-based UI.

## Profiles

Endpoints:
- `GET /api/v1/auth/my-profile/` → Global user profile
- `GET /api/v1/profiles/my-branch/<branch_id>/` → Role-aware branch profile
- `PATCH /api/v1/profiles/my-branch/<branch_id>/` → Create or update role-aware profile

Role-aware data surface via `BranchMembershipSerializer.role_data` in membership lists and can be fetched directly via the profile endpoints.

Example role_data structures:

- Teacher
```json
{
  "subject": "Physics",
  "experience_years": 7,
  "bio": "..."
}
```

- Student
```json
{
  "grade": "9A",
  "parent_name": "Parent Name"
}
```

- Parent
```json
{
  "notes": "...",
  "related_students": [
    {"id": "...", "grade": "9A"}
  ]
}
```

- AdminProfile (branch_admin)
```json
{
  "is_super_admin": false,
  "managed_branches": [
    {"id": "<uuid>", "name": "Tashkent"},
    {"id": "<uuid>", "name": "Samarkand"}
  ],
  "title": "Filial boshligi",
  "notes": "Responsible for morning shifts"
}
```

- AdminProfile (super_admin)
```json
{
  "is_super_admin": true,
  "managed_branches": [],
  "title": "System Administrator",
  "notes": "Global access"
}
```

## Permissions in UI

Simple client-side guards can improve UX (server remains source of truth):

```js
if (user.br_role === 'teacher') {
  // show teacher dashboard
}
if (user.br_role === 'branch_admin') {
  // show branch admin management
}
if (user.br_role === 'super_admin') {
  // show platform-wide admin UI
}
```

### UI suggestion for admins

If `role_data.managed_branches` is provided, render a branch selector in admin dashboards to quickly filter by branch:

```js
function renderAdminSidebar(user) {
  if (!user || (user.br_role !== 'branch_admin' && user.br_role !== 'super_admin')) return null;
  const branches = user.role_data?.managed_branches || [];
  return (
    <aside>
      <h4>Admin</h4>
      {branches.length > 0 && (
        <select>
          {branches.map(b => (
            <option key={b.id} value={b.id}>{b.name}</option>
          ))}
        </select>
      )}
    </aside>
  );
}
```

Recommended mapping:
- super_admin/branch_admin: admin dashboards, user management, configuration
- teacher: class/journal management, materials
- student: timetable, homework, grades
- parent: student overview, communications

## Diagram

```

## Role helpers (examples)

```tsx
// RoleGuard component example
export function RoleGuard({ role, user, children }) {
  if (!user) return null;
  return user.br_role === role ? children : null;
}

// Admin sidebar using managed_branches
export function renderAdminSidebar(user) {
  if (!user || (user.br_role !== 'branch_admin' && user.br_role !== 'super_admin')) return null;
  const branches = user.role_data?.managed_branches || [];
  // ...render as needed
}
```
User → BranchMembership → Branch → Role → RoleProfile (Teacher/Student/Parent/Admin)
```

## Changelog

- `UserBranch` (auth.users.models) is deprecated.
- `BranchMembership` (apps.branch.models) is the canonical model for RBAC.
- JWT branch claims remain the same: `br` and `br_role`.
- AdminProfile added for admin-class roles (branch_admin, super_admin), surfaced via membership role_data.

## Yangi Imkoniyatlar (2025-01)

### Role Model
- Har bir filial uchun konfiguratsiyalanadigan rollar
- Maosh turi: oylik, soatlik, har bir uchun
- JSON formatida ruxsatlar

### Balance Management
- Har bir xodimning balansi
- Balansni qo'shish/ayirish
- Ish haqini ko'rish va boshqarish

### Audit Trail
- `created_by` — kim yaratdi
- `updated_by` — kim o'zgartirdi

Batafsil ma'lumot uchun: [rbac-salary-balance.md](./rbac-salary-balance.md)

## Managed Branches (Admin Access)

Endpoint: `/api/branches/managed/`

### SuperAdmin
- GET → Returns all active branches.
- PATCH → Updates any user's managed branches list.

### BranchAdmin
- GET → Returns only branches assigned to current admin (via admin memberships or their managed list when configured).

### Example Response

```json
[
  {"id": "<uuid>", "name": "Downtown Campus", "status": "active"},
  {"id": "<uuid>", "name": "North Campus", "status": "active"}
]
```

### UI Behavior
- BranchAdmin dashboard: display list of managed branches (read-only).
- SuperAdmin dashboard: table with all branches, editable assignment modal (sets role_data.managed_branches for a selected admin).
