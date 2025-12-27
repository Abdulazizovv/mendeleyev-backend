# Load Testing Guide - Moliya API

## Race Condition Test

Parallel tranzaksiyalar yaratib, balans to'g'ri hisoblanishini tekshirish.

### Test Script (Python + Threading)

```python
import concurrent.futures
import requests
import time

BASE_URL = "http://localhost:8000"
BRANCH_ID = "your-branch-uuid"
CASH_REGISTER_ID = "your-cash-register-uuid"
CATEGORY_ID = "your-category-uuid"
TOKEN = "your-jwt-token"

def create_transaction(amount):
    """Bitta tranzaksiya yaratish."""
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "X-Branch-Id": BRANCH_ID,
        "Content-Type": "application/json"
    }
    
    data = {
        "cash_register": CASH_REGISTER_ID,
        "transaction_type": "income",
        "category": CATEGORY_ID,
        "amount": amount,
        "payment_method": "cash",
        "description": f"Load test - {amount}"
    }
    
    start = time.time()
    response = requests.post(
        f"{BASE_URL}/api/v1/school/finance/transactions/",
        json=data,
        headers=headers
    )
    latency = (time.time() - start) * 1000  # ms
    
    return {
        "status": response.status_code,
        "latency": latency,
        "amount": amount
    }

def load_test(num_requests=100):
    """Parallel tranzaksiyalar yaratish."""
    print(f"Starting load test: {num_requests} parallel requests...")
    
    # Initial balance
    headers = {"Authorization": f"Bearer {TOKEN}"}
    initial_response = requests.get(
        f"{BASE_URL}/api/v1/school/finance/cash-registers/{CASH_REGISTER_ID}/",
        headers=headers
    )
    initial_balance = initial_response.json()['balance']
    print(f"Initial balance: {initial_balance:,} so'm")
    
    # Parallel requests
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        # Har biri 10,000 so'm
        futures = [executor.submit(create_transaction, 10000) for _ in range(num_requests)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    duration = time.time() - start_time
    
    # Results
    success_count = sum(1 for r in results if r['status'] == 201)
    failed_count = num_requests - success_count
    avg_latency = sum(r['latency'] for r in results) / len(results)
    
    print(f"\n=== RESULTS ===")
    print(f"Duration: {duration:.2f}s")
    print(f"Requests/sec: {num_requests / duration:.2f}")
    print(f"Success: {success_count}/{num_requests}")
    print(f"Failed: {failed_count}")
    print(f"Avg latency: {avg_latency:.2f}ms")
    
    # Final balance check
    time.sleep(2)  # Wait for async processing
    final_response = requests.get(
        f"{BASE_URL}/api/v1/school/finance/cash-registers/{CASH_REGISTER_ID}/",
        headers=headers
    )
    final_balance = final_response.json()['balance']
    expected_balance = initial_balance + (success_count * 10000)
    
    print(f"\n=== BALANCE CHECK ===")
    print(f"Initial: {initial_balance:,} so'm")
    print(f"Expected: {expected_balance:,} so'm")
    print(f"Actual: {final_balance:,} so'm")
    print(f"Difference: {abs(expected_balance - final_balance):,} so'm")
    
    if expected_balance == final_balance:
        print("✅ PASS: Balance is correct!")
    else:
        print("❌ FAIL: Balance mismatch (race condition detected)")

if __name__ == "__main__":
    load_test(num_requests=100)
```

### Run Test

```bash
pip install requests
python load_test.py
```

### Expected Output

```
Starting load test: 100 parallel requests...
Initial balance: 5,000,000 so'm

=== RESULTS ===
Duration: 2.45s
Requests/sec: 40.82
Success: 100/100
Failed: 0
Avg latency: 48.32ms

=== BALANCE CHECK ===
Initial: 5,000,000 so'm
Expected: 6,000,000 so'm
Actual: 6,000,000 so'm
Difference: 0 so'm
✅ PASS: Balance is correct!
```

---

## Apache JMeter Test

### 1. Install JMeter
```bash
# Ubuntu/Debian
sudo apt install jmeter

# macOS
brew install jmeter
```

### 2. Test Plan

1. **Thread Group**
   - Number of Threads: 100
   - Ramp-up Period: 10s
   - Loop Count: 10

2. **HTTP Request**
   - Method: POST
   - Path: `/api/v1/school/finance/transactions/`
   - Body Data (JSON):
   ```json
   {
     "cash_register": "${CASH_REGISTER_ID}",
     "transaction_type": "income",
     "category": "${CATEGORY_ID}",
     "amount": 10000,
     "payment_method": "cash",
     "description": "JMeter test"
   }
   ```

3. **HTTP Header Manager**
   - Authorization: `Bearer ${TOKEN}`
   - X-Branch-Id: `${BRANCH_ID}`
   - Content-Type: `application/json`

4. **Listeners**
   - View Results Tree
   - Summary Report
   - Graph Results

### 3. Run Test
```bash
jmeter -n -t finance_load_test.jmx -l results.jtl
```

---

## Locust Test (Python)

### Install
```bash
pip install locust
```

### locustfile.py
```python
from locust import HttpUser, task, between

class FinanceUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login va token olish."""
        response = self.client.post("/api/v1/auth/login/", json={
            "phone_number": "+998901234567",
            "password": "password123"
        })
        self.token = response.json()['access']
        self.branch_id = "your-branch-uuid"
        self.cash_register_id = "your-cash-register-uuid"
        self.category_id = "your-category-uuid"
    
    @task(10)
    def create_transaction(self):
        """Tranzaksiya yaratish."""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Branch-Id": self.branch_id
        }
        
        self.client.post(
            "/api/v1/school/finance/transactions/",
            json={
                "cash_register": self.cash_register_id,
                "transaction_type": "income",
                "category": self.category_id,
                "amount": 10000,
                "payment_method": "cash",
                "description": "Locust test"
            },
            headers=headers
        )
    
    @task(1)
    def list_transactions(self):
        """Tranzaksiyalar ro'yxati."""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Branch-Id": self.branch_id
        }
        
        self.client.get(
            "/api/v1/school/finance/transactions/",
            headers=headers
        )
```

### Run
```bash
# Web UI
locust -f locustfile.py

# Headless
locust -f locustfile.py --headless --users 100 --spawn-rate 10 --run-time 60s
```

---

## Monitoring Setup

### 1. Prometheus + Grafana

**docker-compose.yml qo'shimcha:**
```yaml
prometheus:
  image: prom/prometheus:latest
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"

grafana:
  image: grafana/grafana:latest
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
```

**prometheus.yml:**
```yaml
scrape_configs:
  - job_name: 'django'
    static_configs:
      - targets: ['django:8000']
```

### 2. Django Prometheus

```bash
pip install django-prometheus
```

**settings.py:**
```python
INSTALLED_APPS = [
    'django_prometheus',
    # ...
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    # ... existing middleware ...
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]
```

**urls.py:**
```python
urlpatterns = [
    path('metrics/', include('django_prometheus.urls')),
]
```

### 3. Key Metrics

- Request duration
- Request count
- Database query count
- Cache hit/miss rate
- Error rate

---

## Expected Performance

### Current (F() expressions)

| Metric | Value |
|--------|-------|
| Requests/sec | 500-1,000 |
| Avg Latency | 50-100ms |
| P95 Latency | 150ms |
| P99 Latency | 250ms |
| Error Rate | <0.1% |
| Database Connections | 20-30 |

### After Celery

| Metric | Value |
|--------|-------|
| Requests/sec | 5,000-10,000 |
| Avg Latency | 20-50ms |
| P95 Latency | 80ms |
| P99 Latency | 150ms |
| Error Rate | <0.01% |
| Celery Workers | 4-8 |

---

## Troubleshooting

### High Latency
- Check database slow queries
- Enable connection pooling (PgBouncer)
- Add database indexes

### Race Conditions
- ✅ F() expressions atomic
- Add database locks (select_for_update)
- Use transactions

### Memory Leaks
- Monitor Django memory usage
- Enable garbage collection
- Restart workers periodically

### Database Connection Pool Exhausted
- Increase max_connections in PostgreSQL
- Use PgBouncer
- Optimize query count
