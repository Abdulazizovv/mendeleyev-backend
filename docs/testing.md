# Testlash

- Framework: `unittest` (default), kelajakda `pytest`ga o'tish mumkin.
- Mavjud testlar: `apps/botapp/tests/test_webhook.py`

## Tavsiya etilgan testlar (MVP)

- Auth: OTP request/verify, JWT refresh
- RBAC: super_admin vs branch_admin kirish farqlari
- Branch API: CRUD + permission checklar

## Ishga tushirish

```bash
make test
```
