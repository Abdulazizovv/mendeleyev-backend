# 🚀 SECURE DEPLOYMENT GUIDE

## ⚠️ MUHIM O'ZGARISHLAR

### Nima o'zgardi:
1. ✅ **Postgres (5533 port) - YOPILDI** → Faqat internal network
2. ✅ **Redis (6479 port) - YOPILDI** → Faqat internal network  
3. ✅ **Django (8101 port) - YOPILDI** → Faqat Nginx orqali
4. ✅ **Nginx (8180 port)** → Yagona public entrypoint
5. ✅ Security hardening qo'shildi (caps, read-only, resource limits)
6. ✅ Non-root user (django:django) container ichida
7. ✅ Healthcheck'lar va log rotation

### Bu nima degani?
- **Oldin**: Har kim internetdan Postgres va Redis'ga kirishga harakat qilishi mumkin edi
- **Hozir**: Faqat Nginx orqali Django'ga kirish mumkin, DB va Redis butunlay yashirin

---

## 📋 DEPLOY QADAMLARI

### 1️⃣ PRE-FLIGHT CHECKS (Majburiy!)

```bash
cd /home/itacademy/Desktop/projects/mendeleyev-backend

# Hozirgi holatni backup qilish
docker compose ps > backup_state_$(date +%Y%m%d_%H%M%S).txt

# Config tekshirish
docker compose config --quiet && echo "✅ Config to'g'ri" || echo "❌ Xato bor!"

# .env permissions
ls -la .env
# Agar 644 yoki ochiqroq bo'lsa:
chmod 600 .env
```

### 2️⃣ ZERO-DOWNTIME DEPLOY (Tavsiya etiladi)

```bash
# Image'larni oldin build qilish
docker compose build --no-cache

# Servislarni birin-ketin restart qilish
echo "🔄 Updating database..."
docker compose up -d --no-deps --build mendeleyev_db
sleep 10

echo "🔄 Updating Redis..."
docker compose up -d --no-deps --build mendeleyev_redis
sleep 5

echo "🔄 Updating Django..."
docker compose up -d --no-deps --build mendeleyev_django
sleep 5

echo "🔄 Updating Celery..."
docker compose up -d --no-deps --build mendeleyev_celery
docker compose up -d --no-deps --build mendeleyev_celery_beat
sleep 5

echo "🔄 Updating Nginx..."
docker compose up -d --no-deps --build mendeleyev_nginx

echo "✅ Deploy tugadi!"
```

### 3️⃣ QUICK DEPLOY (2-3 daqiqa downtime)

```bash
# Hammasini to'xtatish va qayta ishga tushirish
docker compose down
docker compose up -d --build

# Loglarni kuzatish
docker compose logs -f --tail=100
```

---

## ✅ TEKSHIRISH (Majburiy!)

### A) Containerlar ishlayaptimi?

```bash
# Barchasi "Up" va "healthy" bo'lishi kerak
docker compose ps

# Kutilgan natija:
# mendeleyev_db         Up (healthy)
# mendeleyev_redis      Up (healthy)  
# mendeleyev_django     Up (healthy)
# mendeleyev_celery     Up
# mendeleyev_celery_beat Up
# mendeleyev_nginx      Up (healthy)
```

### B) Portlar yopildimi? (KRITIK!)

```bash
# Ochiq portlarni tekshirish
sudo ss -tunlp | grep -E ":5533|:6479|:8101"

# Natija: HECH NARSA ko'rinmasligi kerak!
# Agar biror narsa chiqsa → XAVFLI, qaytadan tekshiring
```

```bash
# Faqat 8180 ochiq bo'lishi kerak
sudo ss -tunlp | grep :8180

# Natija: docker-proxy ... 0.0.0.0:8180
```

### C) Django Nginx orqali ishlaydimi?

```bash
# Ichkaridan (serverda)
curl -I http://localhost:8180/admin/login/
# Kutilgan: HTTP/1.1 200 OK yoki 302 Found

# Tashqaridan (sizning kompyuteringizdan)
curl -I http://eduapi.mendeleyev.uz/admin/login/
# Kutilgan: HTTP/1.1 200 OK yoki 302 Found
```

### D) Django to'g'ridan to'g'ri ochiq emasmi?

```bash
# Bu MUVAFFAQIYATSIZ bo'lishi kerak
curl -I http://localhost:8101/ 2>&1

# Kutilgan natija: "Connection refused" yoki "Failed to connect"
# Agar 200 OK chiqsa → MUAMMO, port hali ochiq!
```

### E) Resource usage

```bash
docker stats --no-stream

# Tekshiring:
# - Django: ~500MB-1.5GB RAM (limit: 1536MB)
# - Postgres: ~256MB-1GB RAM (limit: 1024MB)
# - Redis: ~50-200MB RAM (limit: 512MB)
# - Agar limit'ga yetib restart bo'lsa → limit'ni oshirish kerak
```

---

## 🚨 AGAR MUAMMO BO'LSA

### Muammo: Container ishga tushmayapti

```bash
# Loglarni ko'rish
docker compose logs mendeleyev_django --tail=100
docker compose logs mendeleyev_db --tail=100

# Umumiy muammolar:
# 1. Permission denied → USER django yo'q (Dockerfile rebuild kerak)
# 2. Can't connect to DB → healthcheck kutish (10-20 soniya kuting)
# 3. Migration error → Manual migration kerak
```

**Yechim - Permission error (non-root user)**:
```bash
# Agar "USER django" muammo qilsa, vaqtincha o'chirib qo'ying
# Dockerfile'da oxirgi qatorni comment qiling:
# USER django

# Rebuild
docker compose build --no-cache
docker compose up -d
```

### Muammo: Portlar hali ochiq ko'rinmoqda

```bash
# Docker compose'ni to'liq to'xtatish
docker compose down

# Eski containerlarni tozalash
docker container prune -f

# Qaytadan ishga tushirish
docker compose up -d

# Tekshirish
sudo ss -tunlp | grep -E ":5533|:6479|:8101"
```

### Muammo: Nginx Django'ga ulanolmayapti

```bash
# Network'larni tekshirish
docker network ls
docker network inspect mendeleyev-backend_nginx_network
docker network inspect mendeleyev-backend_internal

# Django qaysi network'larga ulangan?
docker inspect mendeleyev_django | grep -A 20 Networks

# Kutilgan: "internal" va "nginx_network" ko'rinishi kerak
```

**Yechim**:
```bash
# Django'ni network'larga qo'shish
docker network connect mendeleyev-backend_internal mendeleyev_django
docker network connect mendeleyev-backend_nginx_network mendeleyev_django

# Nginx'ni restart qilish
docker compose restart mendeleyev_nginx
```

---

## 🔄 ROLLBACK (Eski holatga qaytish)

Agar yangi konfiguratsiya ishlamasa:

```bash
# 1. Git orqali eski faylga qaytish
git diff docker-compose.yml  # O'zgarishlarni ko'rish
git checkout HEAD~1 docker-compose.yml  # Eski versiyaga qaytish

# 2. Eski containerlarni ishga tushirish
docker compose down
docker compose up -d

# 3. Tekshirish
docker compose ps
```

**DIQQAT**: Eski holatda DB va Redis yana internetga ochiq bo'ladi! Tezda muammoni hal qiling va qaytadan secure deploy qiling.

---

## 📊 POST-DEPLOYMENT MONITORING

### Doimiy monitoring (birinchi 24 soat)

```bash
# Har 5 daqiqada tekshirish
watch -n 300 'docker compose ps && echo "---" && docker stats --no-stream'

# Restart count (0 bo'lishi kerak)
docker inspect mendeleyev_django --format='Restarts: {{.RestartCount}}'
docker inspect mendeleyev_db --format='Restarts: {{.RestartCount}}'

# Agar restart count ko'payib borsa → log'larni tekshiring
```

### Haftalik tekshirish

```bash
# 1. Barcha sog'lommi?
docker compose ps | grep -q "Up (healthy)" && echo "✅ OK" || echo "❌ Issue"

# 2. Log hajmi
du -sh logs/
# Agar >100MB bo'lsa: find logs/ -type f -mtime +7 -delete

# 3. Disk space
df -h
```

---

## 🔐 QOLGAN HARDENING (TODO)

### 1. Host UFW + Docker Integration

```bash
# Docker UFW bypass'ni to'xtatish
# /etc/ufw/after.rules ga qo'shish kerak:

sudo nano /etc/ufw/after.rules
# Eng pastga qo'shing:
# *filter
# :DOCKER-USER - [0:0]
# -A DOCKER-USER -j RETURN
# COMMIT

sudo ufw reload
```

### 2. Tashqi Nginx (Host level) SSL

Sizning tashqi nginx konfiguratsiyangizda:
```nginx
# /etc/nginx/sites-available/eduapi.mendeleyev.uz

upstream docker_backend {
    server 127.0.0.1:8180;
}

server {
    listen 80;
    server_name eduapi.mendeleyev.uz;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name eduapi.mendeleyev.uz;

    ssl_certificate /etc/letsencrypt/live/eduapi.mendeleyev.uz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/eduapi.mendeleyev.uz/privkey.pem;

    location / {
        proxy_pass http://docker_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Automatic Security Updates

```bash
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## 📞 YORDAM KERAKMI?

**Aloqa**:
- Telegram: @your_username
- Email: admin@mendeleyev.uz

**Foydali havolalar**:
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [OWASP Docker Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html)

**Oxirgi yangilanish**: 2026-02-14
