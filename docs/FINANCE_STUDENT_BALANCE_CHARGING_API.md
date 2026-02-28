# Student Balance → Subscription Charging (API + Celery)

Bu hujjat student balansidan abonement to'lovini avtomatik (Celery) va qo'lda (API) yechish oqimini tushuntiradi.

## Avtomatik yechish (Celery)

- Periodik task: `finance.charge_due_subscriptions`
- Schedule: har kuni `00:05` (server timezone) — `core/settings.py` dagi `CELERY_BEAT_SCHEDULE` orqali.

Logika (har bir `StudentSubscription` uchun):

1) `next_payment_date <= bugun` bo'lsa charge qilinadi  
2) `StudentBalance.balance >= due_amount` bo'lsa:
   - balansdan yechiladi
   - `last_payment_date = bugun`
   - `next_payment_date` keyingi davrga suriladi
3) Yetarli balans bo'lmasa:
   - balansdan yechilmaydi
   - `total_debt += due_amount`
   - `next_payment_date` keyingi davrga suriladi
4) Har urinish audit uchun `StudentBalanceTransaction` yozadi

## Qo'lda yechish (API)

### 1) Abonementni charge qilish (manual trigger)

`POST /api/v1/school/finance/student-subscriptions/{subscription_id}/charge/`

Headers:
- `X-Branch-Id: <branch_uuid>`

Body:
```json
{
  "force": false
}
```

Izoh:
- `force=true` bo'lsa, `next_payment_date` kelmagan bo'lsa ham charge qiladi.

Response (misol):
```json
{
  "result": {
    "ok": true,
    "charged": true,
    "amount": 1000000,
    "reason": "debited",
    "message": "Charged from balance",
    "debt_added": 0
  },
  "subscription": {
    "id": "…",
    "student_profile": "…",
    "subscription_plan": "…",
    "next_payment_date": "2026-03-28",
    "last_payment_date": "2026-02-28",
    "total_debt": 0
  },
  "student_balance": {
    "id": "…",
    "balance": 500000
  }
}
```

### 2) Student balans audit tranzaksiyalari

`GET /api/v1/school/finance/student-balances/{student_balance_id}/transactions/`

Headers:
- `X-Branch-Id: <branch_uuid>`

Response: pagination bilan `StudentBalanceTransaction` ro'yxati.

## Audit modeli

Model: `apps/school/finance/models.py` → `StudentBalanceTransaction`

- `transaction_type`: `credit`/`debit`
- `status`: `completed`/`failed`
- `reason`: `subscription_charge`, `payment_topup`, `manual_adjustment`, `other`
- `subscription`: (ixtiyoriy) qaysi abonement uchun
- `previous_balance/new_balance`: snapshot (audit uchun)

