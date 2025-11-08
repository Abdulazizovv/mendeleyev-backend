# Frontend Auth Integration Guide

This guide summarizes how to integrate the Mendeleyev backend auth + branch flow in a frontend (SPA or mobile). It assumes a password-based login after one-time phone verification.

## States
The phone check endpoint returns one of:
- `NOT_FOUND` – User does not exist (admin must provision; show contact message)
- `NOT_VERIFIED` – User exists but phone not confirmed
- `NEEDS_PASSWORD` – Phone verified but no password set yet
- `READY` – Can login immediately
- `NO_BRANCH` – User has no active branch membership (contact admin)
- `MULTI_BRANCH` – User must choose a branch before receiving tokens

## High-Level Flow
1. User enters phone → call `/api/v1/auth/phone/check`
2. Based on `state`:
   - `NOT_FOUND`: stop, show admin contact
   - `NOT_VERIFIED`: request verification OTP, confirm it, then proceed (might need password set)
   - `NEEDS_PASSWORD`: show password set form
   - `READY`: go to login form
3. Login `/api/v1/auth/login` with phone + password (optionally `branch_id` for multi-branch)
4. If response `state=MULTI_BRANCH`: show branch list and re-post with selected `branch_id`.
5. Store tokens; add `Authorization: Bearer <access>` header for protected requests.
6. On expiration, refresh tokens with `/api/v1/auth/refresh`.
7. To change branch later, call `/api/v1/auth/branch/switch`.

## Token Handling
- Access token lifetime default ~15 minutes (configurable); refresh ~30 days.
- Store both tokens securely (HTTP-only cookie or secure storage). Avoid localStorage for security unless hardened.
- Refresh proactively (silent refresh) or on 401 responses.

### Token Claims
If branch-scoped:
```json
{
  "br": "<branch-id>",
  "br_role": "teacher" | "branch_admin" | ...
}
```
Global (admin/superuser without branch) will omit `br`.

## Branch Selection UI
- After initial login attempt, if `MULTI_BRANCH`, API returns:
```json
{
  "state": "MULTI_BRANCH",
  "branches": [
    {"id": "...", "name": "Alpha", "role": "teacher"},
    {"id": "...", "name": "Beta", "role": "branch_admin"}
  ]
}
```
Render list and send second login with chosen `branch_id`.

## Password Reset
1. User requests reset: POST `/api/v1/auth/password/reset/request-otp` { phone }
2. Always returns 200 (no enumeration). If account exists + verified, OTP sent.
3. User confirms: POST `/api/v1/auth/password/reset/confirm` { phone, code, new_password }
4. Receives fresh tokens.

## Initial Password Set (after verification)
- POST `/api/v1/auth/password/set` with phone + password.
- Response includes tokens and `state=READY`.

## Error Handling Patterns
- 400: validation/invalid credentials.
- 401: token invalid/refresh fails (maybe branch revoked or inactive) → force re-login.
- 403: membership missing when trying to switch branch.
- 429: OTP request cooldown.

## Recommended UX
- Disable OTP request button until cooldown ends; show countdown from `expires_in` if provided.
- Mask phone number on confirmation screens for privacy.
- Provide branch badge or selector once logged in (show current `br_role`).
- On refresh 401 due to branch issues, prompt user to re-select branch if still multi-branch.

## Security Tips
- Use HTTPS everywhere.
- Prefer HTTP-only secure cookies for refresh token; store access in memory (if using web SPA) to reduce XSS risk.
- Implement inactivity auto-logout (e.g., 30 min) and manual logout that discards tokens.

## Sample Pseudo-code (Login Flow)
```ts
async function login(phone: string, password: string) {
  const r = await api.post('/api/v1/auth/login/', { phone_number: phone, password });
  if (r.state === 'NOT_VERIFIED') return { step: 'verify-phone' };
  if (r.state === 'NEEDS_PASSWORD') return { step: 'set-password' };
  if (r.state === 'MULTI_BRANCH') return { step: 'choose-branch', branches: r.branches };
  if (r.state === 'NO_BRANCH') return { step: 'contact-admin' };
  // success
  saveTokens(r.access, r.refresh);
  return { step: 'done', user: r.user, branch: r.br, role: r.br_role };
}
```

## Switching Branch
```ts
async function switchBranch(refresh: string, branchId: string) {
  const r = await api.post('/api/v1/auth/branch/switch/', { refresh, branch_id: branchId });
  saveTokens(r.access, r.refresh);
  return r.br;
}
```

## Refresh
```ts
async function refreshToken(refresh: string) {
  const r = await api.post('/api/v1/auth/refresh/', { refresh });
  saveAccess(r.access); // keep existing refresh or replace if rotation enabled
}
```

---
Stay aligned with backend updates and adjust UI as states evolve.
