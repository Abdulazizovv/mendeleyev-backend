# 🛡️ SECURITY CHECKLIST - Mendeleyev Backend

## ✅ Docker Compose Security (Implemented)

### Network Isolation
- [x] **DB (Postgres)**: No external port, internal network only
- [x] **Redis**: No external port, internal network only  
- [x] **Django**: No external port (8101 removed), accessible only via Nginx
- [x] **Nginx**: Only public service (8180:80)
- [x] **Internal network**: DB/Redis/Celery isolated, no internet access

### Security Hardening
- [x] `no-new-privileges:true` - prevents privilege escalation
- [x] `cap_drop: ALL` + minimal `cap_add` - least privilege
- [x] `read_only: true` (Nginx, Redis) - immutable containers
- [x] `tmpfs` - writable temporary storage without persistence
- [x] Resource limits (CPU, memory) - prevent DoS
- [x] Log rotation - prevent disk filling
- [x] Healthchecks - automatic restart on failure

### Dependencies
- [x] Service dependencies with conditions (`service_healthy`)
- [x] Postgres health check
- [x] Redis health check
- [x] Django health check
- [x] Nginx health check

---

## 🚀 DEPLOYMENT STEPS

### 1. Pre-deployment Check
```bash
cd /home/itacademy/Desktop/projects/mendeleyev-backend

# Backup current state
docker compose ps > backup_containers_$(date +%Y%m%d).txt
sudo docker inspect mendeleyev_db | grep -A 20 Mounts > backup_volumes_$(date +%Y%m%d).txt

# Verify configuration
docker compose config --quiet && echo "✅ Config valid" || echo "❌ Config error"
```

### 2. Zero-Downtime Deployment (RECOMMENDED)
```bash
# Build new images first
docker compose build --no-cache

# Pull new base images
docker compose pull

# Restart services one by one (keeps others running)
docker compose up -d --no-deps --build mendeleyev_db  # DB first
sleep 5
docker compose up -d --no-deps --build mendeleyev_redis
sleep 5
docker compose up -d --no-deps --build mendeleyev_django
docker compose up -d --no-deps --build mendeleyev_celery
docker compose up -d --no-deps --build mendeleyev_celery_beat
docker compose up -d --no-deps --build mendeleyev_nginx  # Nginx last

# Verify all healthy
docker compose ps
docker compose logs --tail=50
```

### 3. Quick Deployment (1-2 min downtime)
```bash
# Stop all, rebuild, restart
docker compose down
docker compose up -d --build

# Verify
docker compose ps
docker compose logs -f --tail=100
```

### 4. Verification Tests
```bash
# Check all containers running
docker compose ps | grep -q "Up" && echo "✅ Containers up" || echo "❌ Some down"

# Check health
docker inspect mendeleyev_db --format='{{.State.Health.Status}}'  # Should be "healthy"
docker inspect mendeleyev_redis --format='{{.State.Health.Status}}'
docker inspect mendeleyev_django --format='{{.State.Health.Status}}'

# Verify no external DB/Redis ports
sudo ss -tunlp | grep -E ":5533|:6479|:8101" && echo "⚠️ PORTS STILL OPEN!" || echo "✅ Ports closed"

# Test Django via Nginx
curl -I http://localhost:8180/admin/login/ | grep "200\|302"  # Should work

# Try direct Django (should FAIL)
curl -I http://localhost:8101/ 2>&1 | grep -q "Connection refused" && echo "✅ Django isolated" || echo "❌ Still exposed"
```

---

## 🔥 HOST HARDENING (TODO)

### UFW + Docker Integration
**Problem**: Docker bypasses UFW rules by default.

**Solution**: Add DOCKER-USER chain rules
```bash
# Block direct access to published ports from external IPs (allow only from localhost/nginx)
sudo ufw route deny proto tcp from any to any port 8180 comment 'Block direct Docker access'

# Or more granular (allow only your monitoring IP)
# sudo ufw route allow from <YOUR_MONITORING_IP> to any port 8180
# sudo ufw route deny from any to any port 8180
```

**CRITICAL**: After applying, test from external IP:
```bash
# From your local machine
curl http://<SERVER_IP>:8180  # Should work (nginx is public)
curl http://<SERVER_IP>:5533  # Should FAIL (no port published)
curl http://<SERVER_IP>:6479  # Should FAIL (no port published)
```

### Automatic Security Updates
```bash
# Install unattended-upgrades
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades

# Verify enabled
sudo systemctl status unattended-upgrades
```

### Auditd (Optional, for compliance)
```bash
# Install
sudo apt install auditd audispd-plugins -y

# Add rules for sensitive files
sudo auditctl -w /etc/passwd -p wa -k passwd_changes
sudo auditctl -w /etc/ssh/sshd_config -p wa -k sshd_config_changes
sudo auditctl -w /var/log/auth.log -p wa -k auth_log_changes

# Make persistent
sudo cp /etc/audit/rules.d/audit.rules /etc/audit/rules.d/audit.rules.backup
sudo bash -c 'auditctl -l > /etc/audit/rules.d/custom.rules'
sudo systemctl restart auditd
```

---

## 📊 MONITORING CHECKLIST

### Docker Metrics
```bash
# Container health status
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# Resource usage
docker stats --no-stream

# Restart counts (high = problem)
docker inspect mendeleyev_django --format='{{.RestartCount}}'
docker inspect mendeleyev_db --format='{{.RestartCount}}'
```

### Log Monitoring
```bash
# Django errors
docker compose logs mendeleyev_django --tail=100 | grep -i error

# Celery task failures
docker compose logs mendeleyev_celery --tail=100 | grep -i "error\|fail"

# Nginx 4xx/5xx
docker compose logs mendeleyev_nginx | grep -E " (4|5)[0-9]{2} "

# Postgres slow queries (if enabled)
docker compose logs mendeleyev_db | grep "duration:"
```

### Network Monitoring
```bash
# Active connections to containers
sudo ss -tunap | grep docker-proxy

# Suspicious outbound connections (should be minimal)
sudo ss -tunap state established | grep -v "127.0.0.1\|172.17\|172.18"
```

---

## 🚨 INCIDENT RESPONSE RUNBOOK

### Scenario 1: High CPU / Suspicious Process
```bash
# 1. Identify process
docker stats --no-stream
docker top mendeleyev_django
docker top mendeleyev_celery

# 2. Check what it's doing
docker exec mendeleyev_django ps aux | head -20
docker exec mendeleyev_django lsof -p <PID>  # Open files/sockets

# 3. If malicious: isolate container
docker network disconnect nginx_network mendeleyev_django  # Cut off nginx
docker network disconnect internal mendeleyev_django  # Cut off DB

# 4. Snapshot for forensics
docker commit mendeleyev_django forensics_django_$(date +%Y%m%d_%H%M%S)
docker logs mendeleyev_django > incident_logs_$(date +%Y%m%d_%H%M%S).txt

# 5. Stop and investigate
docker compose stop mendeleyev_django
```

### Scenario 2: Database Compromise
```bash
# 1. Immediate: Block all access
docker compose pause mendeleyev_db  # Pauses without killing

# 2. Backup current state
docker exec mendeleyev_db pg_dumpall -U $POSTGRES_USER > incident_backup_$(date +%Y%m%d).sql

# 3. Check connections
docker exec mendeleyev_db psql -U $POSTGRES_USER -c "SELECT * FROM pg_stat_activity;"

# 4. If suspicious connection: kill it
docker exec mendeleyev_db psql -U $POSTGRES_USER -c "SELECT pg_terminate_backend(<pid>);"

# 5. Unpause or restore from clean backup
docker compose unpause mendeleyev_db
```

### Scenario 3: Malware Returns
```bash
# 1. IMMEDIATE: Disconnect from internet
sudo ufw default deny outgoing  # ⚠️ DRASTIC - breaks updates

# 2. Check new cron/systemd entries
sudo crontab -l | diff - /tmp/previous_crontab.txt
sudo systemctl list-unit-files --state=enabled | diff - /tmp/previous_units.txt

# 3. Check new network connections
sudo ss -tunap | grep ESTABLISHED | grep -v "127.0.0.1\|172.17\|172.18"

# 4. Reinstall server (if persistence confirmed)
# Backup data -> Full OS reinstall -> Restore from known-good backup
```

---

## 🔐 SECRETS MANAGEMENT

### .env File Security
```bash
# Correct permissions (only owner read/write)
chmod 600 .env
chown ulugbek:ulugbek .env

# Verify no secrets in git
git ls-files | xargs grep -i "password\|secret\|key" | grep -v ".env.example"

# Rotate secrets regularly (every 90 days)
# Update: POSTGRES_PASSWORD, DJANGO_SECRET_KEY, REDIS_PASSWORD (if used)
```

### Docker Secrets (Future Enhancement)
```bash
# TODO: Migrate to Docker Swarm secrets or external vault (HashiCorp Vault)
# For now, .env with strict permissions is acceptable for single-server setup
```

---

## 📋 MAINTENANCE SCHEDULE

### Daily
- [ ] Check `docker compose ps` - all containers "Up (healthy)"
- [ ] Review logs for errors: `docker compose logs --tail=100 | grep -i error`

### Weekly
- [ ] Check resource usage: `docker stats --no-stream`
- [ ] Review Nginx access logs for unusual traffic
- [ ] Verify backup integrity (restore test)

### Monthly
- [ ] Update base images: `docker compose pull && docker compose up -d`
- [ ] Review and rotate logs: `find logs/ -type f -mtime +30 -delete`
- [ ] Security audit: Re-run persistence checks
- [ ] Review UFW logs: `sudo grep UFW /var/log/syslog | tail -100`

### Quarterly
- [ ] Rotate secrets (.env passwords)
- [ ] Update Django/Python dependencies: `pip list --outdated`
- [ ] Full security audit (external scan if possible)

---

## 📞 CONTACTS

- **DevOps Lead**: Ulugbek
- **Server**: eduapi.mendeleyev.uz (91.92.243.113 - blocked)
- **SSH**: Port 2220 (pubkey only)
- **Monitoring**: Zabbix (if configured)

**Last Updated**: 2026-02-14
