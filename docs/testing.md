# Testing Strategy

## How to Run
Docker:
```bash
make test
```
Specific module/class/test:
```bash
docker compose exec django python manage.py test auth.users.tests.test_auth_flow -v 2
docker compose exec django python manage.py test auth.users.tests.test_branch_jwt -v 2
docker compose exec django python manage.py test auth.users.tests.test_auth_flow.AuthFlowTests.test_login_gating_and_success -v 2
```

Local (SQLite) quick run:
```bash
USE_SQLITE=1 DJANGO_SECRET_KEY=dev-key python manage.py test -v 2
```

## Scope
- Auth flow tests (phone check, verification, password set, login gating, reset/confirm, change).
- Branch JWT tests (single vs multi-branch, switch, refresh revoke/archived, my branches, admin global/scoped).

## OTP Isolation
Tests clear OTP Redis keys per phone/purpose to avoid 429 due to cooldown and to ensure deterministic verification logic. See helpers in `auth/users/tests/test_auth_flow.py`.

## Celery in Tests
`CELERY_TASK_ALWAYS_EAGER=True` ensures tasks run inline; external services (Telegram) are mocked or no-op in most paths; logs may contain "Unclosed client session" informational lines that can be silenced later via a test stub.

## Coverage (Optional)
```bash
docker compose exec django pip install coverage
docker compose exec django coverage run manage.py test
docker compose exec django coverage html
```
Open `htmlcov/index.html` for a report.

## CI (Planned)
- GitHub Actions workflow triggering on PRs: build, migrate, run tests, upload coverage to artifact.
- Lint: `flake8` and possibly `ruff`.
