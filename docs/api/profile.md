# Profile API

This document describes the global user profile and role-aware (branch) profile.

## Global Profile (one per user)

Model fields:
- avatar: Image URL
- date_of_birth: YYYY-MM-DD
- gender: male|female|other|unspecified
- language: e.g. "uz"
- timezone: e.g. "Asia/Tashkent"
- bio: string
- address: string
- socials: JSON object, e.g. {"telegram":"@user","instagram":"u"}

Endpoints:
- GET /api/v1/profile/me/
- PATCH /api/v1/profile/me/ (application/json or multipart/form-data for avatar)

Example GET response:
```
{
  "id": "uuid",
  "avatar": "/media/avatars/u123.png",
  "date_of_birth": "2000-05-17",
  "gender": "unspecified",
  "language": "uz",
  "timezone": "Asia/Tashkent",
  "bio": "Physics enthusiast",
  "address": "Tashkent",
  "socials": {"telegram":"@user"},
  "created_at": "2025-11-04T08:00:00Z",
  "updated_at": "2025-11-04T08:05:00Z"
}
```

## Role Profile (per branch membership)

Attached to the user's membership in a specific branch (UserBranch).

Fields:
- display_name: string
- title: string (e.g., "Physics Teacher", "9A Student")
- about: string
- contacts: JSON (e.g., {"phone":"+998...","email":"..."})

Endpoints:
- GET /api/v1/profile/branch/<branch_id>/
- PATCH /api/v1/profile/branch/<branch_id>/

Rules:
- Requires authentication.
- Returns 403 if user is not a member of the branch.
- GET returns 404 if the role profile doesn’t exist yet (PATCH will create it automatically).

## Integration Tips
- Use global profile for account/settings pages (avatar, language, timezone).
- Use role profile for branch dashboards (title, branch-specific display name/contacts).
- Always pass a valid JWT (Bearer token) from the OTP login flow.
- For avatar upload, use multipart/form-data and include only changed fields.

## Future Enhancements
- Validation schemas for socials/contacts JSON.
- Per-role permissions to edit specific fields.
- File storage on S3/GCS in production.
