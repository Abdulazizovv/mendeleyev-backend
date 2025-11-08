# Mendeleyev Backend — Documentation

Ushbu hujjatlar arxitektura, API, xavfsizlik, testlar va ekspluatatsiya bo'yicha to'liq ko'rsatma beradi. Frontend va AI-agentlar uchun integratsiya bo'limlari ham mavjud. Qisqa tavsif va Quickstart uchun root `README.md` ni ko'ring.

## Navigatsiya

- Arxitektura
  - [Umumiy ko'rinish](./architecture/overview.md)
  - [Xizmatlar va komponentlar](./architecture/services.md)
  - [Ma'lumotlar modeli (ER)](./architecture/data-model.md)
  - [Auth & Branch flow diagrammalari](./architecture/auth-flow.md)
- API
  - [Index (v1)](./api/index.md)
  - [Umumiy qoidalar](./api/overview.md)
  - [Auth (OTP, parol, branch-scoped JWT)](./api/auth.md)
  - [Branch](./api/branch.md)
  - [Profile](./api/profile.md)
- Integratsiya
  - [Frontend auth integratsiyasi](./frontend/auth-integration.md)
- Ishga tushirish va infra
  - [Setup (Docker Compose, env)](./setup.md)
  - [Deployment](./deployment.md)
  - [Testlar va coverage](./testing.md)
  - [Logging](./logging.md)
  - [Celery](./celery.md)
  - [Telegram bot](./bot.md)
  - [Xavfsizlik](./security.md)
- Jamiyat va jarayon
  - [Contributing](./contributing.md)
  - [Makefile qo'llanma](./makefile.md)
  - [Roadmap](./roadmap.md)

