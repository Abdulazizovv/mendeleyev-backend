# Auth and Branch Flow

Below are concise diagrams that show how the system works: phone verification, password setup, login with branch selection, token refresh, and branch switching. Use them as a quick reference when wiring the frontend.

## Legend
- FE = Frontend client
- API = Django REST API
- OTP = OTP service (Redis + Celery)
- RBAC = Roles via UserBranch

## 1) Phone check → verify → set password
```mermaid
sequenceDiagram
  participant FE
  participant API
  participant OTP

  FE->>API: POST /api/v1/auth/phone/check { phone }
  API-->>FE: 200 { state: NOT_FOUND | NOT_VERIFIED | NEEDS_PASSWORD | READY }

  alt NOT_VERIFIED
    FE->>API: POST /api/v1/auth/phone/verification/request { phone }
    API->>OTP: request_code(purpose=verify)
    API-->>FE: 200 { detail: "OTP sent" }

    FE->>API: POST /api/v1/auth/phone/verification/confirm { phone, code }
    API->>OTP: verify_code(purpose=verify)
    API-->>FE: 200 { state: NEEDS_PASSWORD | READY, [access, refresh] }

    alt NEEDS_PASSWORD
      FE->>API: POST /api/v1/auth/password/set { phone, password }
      API-->>FE: 200 { state: READY, access, refresh }
    end
  end
```

Notes:
- Unknown phone triggers a Telegram admin notify in the background (throttled).
- If the user already has a password when confirming verification, the API returns tokens immediately.

## 2) Login with branch selection
```mermaid
sequenceDiagram
  participant FE
  participant API

  FE->>API: POST /api/v1/auth/login { phone, password, [branch_id] }
  alt superuser/staff
    alt no branch_id
      API-->>FE: 200 { access, refresh, user }  // global token
    else with branch_id
      API-->>FE: 200 { access, refresh, user, br }
    end
  else regular user
    API->>API: memberships = active branches of user
    alt memberships == 0
      API-->>FE: 200 { state: NO_BRANCH }
    else memberships == 1
      API-->>FE: 200 { access, refresh, user, br, br_role }
    else >1 (multi)
      API-->>FE: 200 { state: MULTI_BRANCH, branches: [...] }
      FE->>API: POST /api/v1/auth/login { phone, password, branch_id }
      API-->>FE: 200 { access, refresh, user, br, br_role }
    end
  end
```

Notes:
- For regular users, tokens are branch-scoped. Claims include `br` and `br_role`.
- Superusers/staff get global tokens by default (no `br`), but can request a scoped token by passing `branch_id`.

## 3) Refresh token (scope preserved)
```mermaid
sequenceDiagram
  participant FE
  participant API

  FE->>API: POST /api/v1/auth/refresh { refresh }
  API->>API: decode refresh → read br/br_role
  alt br present
    API->>API: Validate branch is active AND membership still exists
    alt valid
      API-->>FE: 200 { access, refresh } // br preserved in access
    else invalid (revoked/archived)
      API-->>FE: 401 { detail }
    end
  else no br
    API-->>FE: 200 { access, refresh } // global
  end
```

## 4) Switch branch (re-issue scoped tokens)
```mermaid
sequenceDiagram
  participant FE
  participant API

  FE->>API: POST /api/v1/auth/branch/switch { refresh, branch_id }
  alt superuser/staff
    API->>API: Ensure target branch is active
    API-->>FE: 200 { access, refresh, br }
  else regular user
    API->>API: Ensure target branch is active and user has membership
    alt ok
      API-->>FE: 200 { access, refresh, br }
    else fail
      API-->>FE: 400/403 { detail }
    end
  end
```

---

## Frontend integration cheat-sheet

1) Phone check before any auth action
   - Call `/api/v1/auth/phone/check` and branch based on `state`.
2) Verification and password set
   - For `NOT_VERIFIED`: request + confirm OTP; if response `NEEDS_PASSWORD`, call password set.
3) Login
   - Call `/api/v1/auth/login` with `phone` and `password`.
   - Handle `MULTI_BRANCH` by showing branch list and re-posting with `branch_id`.
4) Token storage
   - Store `access` (short-lived) and `refresh` (long-lived).
   - On API requests, use `Authorization: Bearer <access>`.
5) Refresh flow
   - When access expires, call `/api/v1/auth/refresh` with `refresh`.
   - If 401 due to branch/membership issues, re-login (and/or re-select branch).
6) Switch branch (if multi-branch)
   - Call `/api/v1/auth/branch/switch` with the current `refresh` and a new `branch_id`.
   - Replace tokens with the new pair from the response.

### Claims and headers
- Access token may contain:
  - `br`: current branch id (string)
  - `br_role`: role in that branch (for regular users)
- Permissions on the backend first read `br` from the token; avoid custom headers unless absolutely necessary.
