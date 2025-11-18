# Auth Me Endpoint (/api/v1/auth/me/)

Enhanced endpoint returning comprehensive authenticated user context.

## Summary
Provides core user fields, global profile, current branch context (if token scoped), all active branch memberships (with role-specific profile data), and high-level auth state.

## Response Shape
```jsonc
{
  "user": {
    "id": "uuid",
    "phone_number": "+998901234567",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "is_staff": false,
    "date_joined": "2024-01-01T00:00:00Z"
  },
  "profile": {
    "id": "uuid",          // nullable if profile not created yet
    "avatar": "/media/avatars/u123.png",
    "date_of_birth": "2000-05-17",
    "gender": "male",
    "language": "uz",
    "timezone": "Asia/Tashkent",
    "bio": "Physics teacher",
    "address": "Tashkent",
    "socials": {"telegram": "@john"},
    "created_at": "...",
    "updated_at": "..."
  },
  "current_branch": {
    "branch_id": "uuid",
    "branch_name": "Chilonzor Branch",
    "branch_type": "school|center",
    "branch_status": "active",
    "role": "teacher",
    "title": "Math Teacher",
    "role_data": { // role-specific profile fields (may be null)
      "subject": "Mathematics",
      "experience_years": 5,
      "bio": "..."
    }
  },
  "memberships": [
    {
      "branch_id": "uuid",
      "branch_name": "Chilonzor Branch",
      "branch_type": "school|center",
      "branch_status": "active",
      "role": "teacher",
      "title": "Math Teacher",
      "role_data": {"subject": "Mathematics", "experience_years": 5, "bio": "..."}
    }
  ],
  "auth_state": "READY|NOT_VERIFIED|NEEDS_PASSWORD|NO_BRANCH|MULTI_BRANCH"
}
```

## Branch Context Logic
- `current_branch` derives from JWT claim `br`. If absent (global admin token or not scoped), this field is null.
- Role is taken from token `br_role` claim; if role changed since token issuance, DB role overrides.

## Memberships
- Lists active branch memberships only (`branch.status == active`).
- Each membership includes `role_data` resolved from specialized profile models:
  - `teacher` → `TeacherProfile`
  - `student` → `StudentProfile`
  - `parent`  → `ParentProfile`
  - `branch_admin` / `super_admin` → `AdminProfile`
- If a specialized profile does not exist yet, `role_data` is null.

## Performance Notes
- Single query for memberships with `select_related` on `branch` and role profiles (`teacher_profile`, `student_profile`, `parent_profile`, `admin_profile`).
- Avoids N+1 when serializing `role_data`.
- Profile fetched via one-to-one relation; safe even if missing.

## Auth State
Derived from `User.auth_state` property:
- `NOT_VERIFIED` — phone not verified.
- `NEEDS_PASSWORD` — no usable password set yet.
- `READY` — fully authenticated user.
(Other transient states such as `NO_BRANCH`, `MULTI_BRANCH` may appear in login flow responses, not here.)

## Error Handling
- Endpoint always returns 200 for authenticated requests.
- Missing profile or memberships produce `null` / empty list fields; no errors.

## Caching & Frontend Usage
- Recommended to call on app bootstrap after token acquisition.
- Safe to cache for session lifetime; refresh token does not change membership set unless roles updated server-side.

## Future Extensions
- Add `permissions` array (aggregated from role).
- Include `unread_notifications_count`.
- Branch-scoped feature flags.

---
Last updated: 2025-11-13
