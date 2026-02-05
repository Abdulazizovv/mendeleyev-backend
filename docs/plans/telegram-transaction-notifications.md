# Telegram Transaction Notifications - To'liq Reja

## 🎯 Maqsad
Har bir moliyaviy tranzaksiya haqida belgilangan Telegram chatlarga avtomatik xabar yuborish tizimini yaratish.

## 📊 Arxitektura Overview

```
Transaction yaratildi
    ↓
Signal/Hook triggered
    ↓
Celery Task (async)
    ↓
Filter by Branch Settings
    ↓
Format Message
    ↓
Send to Telegram Chats
```

## 🗂️ Database Models

### 1. TelegramChat
Bot admin bo'lgan va xabar yuborish mumkin bo'lgan chatlarni saqlash.

```python
class TelegramChat(BaseModel):
    """
    Telegram chat ma'lumotlari va bot huquqlari.
    Bot /start yoki /register command orqali chat'ni ro'yxatdan o'tkazadi.
    """
    chat_id = models.BigIntegerField(unique=True)  # Telegram chat ID
    chat_type = models.CharField(
        max_length=20,
        choices=[
            ('private', 'Shaxsiy'),
            ('group', 'Guruh'),
            ('supergroup', 'Superguruh'),
            ('channel', 'Kanal'),
        ]
    )
    title = models.CharField(max_length=255, blank=True)  # Guruh/kanal nomi
    username = models.CharField(max_length=255, blank=True, null=True)  # @username
    
    # Bot huquqlari (tekshirish uchun)
    is_bot_admin = models.BooleanField(default=False)
    can_post_messages = models.BooleanField(default=True)
    
    # Verification
    verification_code = models.CharField(max_length=32, blank=True)  # Tasdiqlash kodi
    is_verified = models.BooleanField(default=False)  # Admin tomonidan tasdiqlangan
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    
    # Status
    is_active = models.BooleanField(default=True)
    last_check_at = models.DateTimeField(auto_now=True)  # Bot huquqi oxirgi tekshirilgan vaqt
    last_message_at = models.DateTimeField(null=True, blank=True)  # Oxirgi xabar yuborilgan vaqt
    
    # Metadata
    description = models.TextField(blank=True)  # Chat haqida izoh
    
    class Meta:
        db_table = 'telegram_chat'
        verbose_name = 'Telegram Chat'
        verbose_name_plural = 'Telegram Chats'
        indexes = [
            models.Index(fields=['chat_id']),
            models.Index(fields=['is_active', 'is_verified']),
        ]
```

### 2. BranchNotificationSettings
Branch uchun qaysi turdagi tranzaksiyalarni qaysi chatlarga yuborish.

```python
class BranchNotificationSettings(BaseModel):
    """
    Branch uchun notification sozlamalari.
    Qaysi transaction turlarini qaysi chatlarga yuborish.
    """
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='notification_settings')
    
    # Qaysi chatlarga yuborish
    telegram_chats = models.ManyToManyField(TelegramChat, related_name='branch_settings')
    
    # Transaction turlari (finance app'dan)
    TRANSACTION_TYPES = [
        ('payment', 'To\'lov'),
        ('expense', 'Xarajat'),
        ('salary', 'Ish haqi'),
        ('refund', 'Qaytarish'),
        ('transfer', 'O\'tkazma'),
        ('adjustment', 'Tuzatish'),
    ]
    
    transaction_types = models.JSONField(
        default=list,
        help_text="Qaysi transaction turlarini yuborish. Empty = hammasi"
    )
    
    # Kategoriyalar filter (optional)
    categories = models.ManyToManyField(
        'school.FinanceCategory',
        blank=True,
        related_name='notification_settings',
        help_text="Faqat belgilangan kategoriyalar uchun yuborish"
    )
    
    # Minimal summa (optional)
    min_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Faqat shu summadan katta tranzaksiyalar uchun"
    )
    
    # Xabar template (optional)
    custom_template = models.TextField(
        blank=True,
        help_text="Custom xabar template (bo'sh bo'lsa default ishlatiladi)"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'branch_notification_settings'
        verbose_name = 'Branch Notification Setting'
        verbose_name_plural = 'Branch Notification Settings'
        unique_together = [['branch']]
```

### 3. NotificationLog (optional, lekin tavsiya etiladi)
Yuborilgan xabarlar tarixi va xatolarni kuzatish.

```python
class NotificationLog(BaseModel):
    """
    Yuborilgan notificationlar tarixi.
    Debug va monitoring uchun.
    """
    # Link to transaction
    transaction = models.ForeignKey(
        'school.Transaction',
        on_delete=models.CASCADE,
        related_name='notification_logs'
    )
    
    # Where sent
    telegram_chat = models.ForeignKey(TelegramChat, on_delete=models.CASCADE)
    
    # Message details
    message_text = models.TextField()
    telegram_message_id = models.BigIntegerField(null=True, blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('sent', 'Yuborildi'),
        ('failed', 'Xato'),
        ('retry', 'Qayta urinish'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Error details
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    # Timestamps
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'notification_log'
        verbose_name = 'Notification Log'
        verbose_name_plural = 'Notification Logs'
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['telegram_chat', 'created_at']),
        ]
```

## 🔧 Implementation Plan

### Phase 1: Models va Admin (1-2 kun)
1. ✅ Models yaratish (yuqoridagi 3ta model)
2. ✅ Migrations
3. ✅ Django Admin configuration (inline, filters, actions)
4. ✅ Bot chat registration command (`/register` va `/verify`)

### Phase 2: Telegram Bot Integration (2-3 kun)
1. ✅ Chat registration handler
2. ✅ Bot permissions checker (celery periodic task)
3. ✅ Message formatter (template engine)
4. ✅ Send message utility function

### Phase 3: Notification System (2-3 kun)
1. ✅ Celery task: `send_transaction_notification`
2. ✅ Signal/Hook: transaction yaratilganda trigger
3. ✅ Filter logic (settings bo'yicha)
4. ✅ Retry mechanism (Celery retry)
5. ✅ Error handling va logging

### Phase 4: Testing va Optimization (1-2 kun)
1. ✅ Unit tests
2. ✅ Integration tests
3. ✅ Load testing (ko'p tranzaksiya)
4. ✅ Performance optimization

### Phase 5: API (keyinroq)
1. ⏳ GET/POST endpoints for settings
2. ⏳ Chat management API
3. ⏳ Logs API

## 🎨 Message Template

```python
DEFAULT_TEMPLATE = """
🏦 <b>{transaction_type_display}</b>

📍 Filial: {branch_name}
💰 Summa: {amount} so'm
📊 Kategoriya: {category_name}
👤 Yaratuvchi: {created_by}

📝 Izoh: {description}

⏰ {created_at}
🔗 ID: {transaction_id}
"""
```

## 📈 Performance Considerations

### 1. Celery Task Optimization
```python
@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 daqiqa
    rate_limit='10/m',  # minutiga 10ta (Telegram rate limit uchun)
)
def send_transaction_notification(self, transaction_id):
    pass
```

### 2. Batching (optional, keyin)
Bir nechta xabarni birlashtirib yuborish (masalan, har 5 daqiqada yig'ib):
- Server yuklamasini kamaytiradi
- Telegram API rate limit muammosini oldini oladi

### 3. Database Indexing
- `telegram_chat.chat_id` - unique index
- `notification_log.status + created_at` - composite index
- `branch_notification_settings.branch_id` - foreign key index

### 4. Caching
```python
# Branch settings'ni cache'lash (15 daqiqa)
@cache_result(timeout=900)
def get_branch_notification_settings(branch_id):
    return BranchNotificationSettings.objects.filter(
        branch_id=branch_id,
        is_active=True
    ).first()
```

## 🔒 Security

1. **Chat Verification**: Admin tasdiqlashisiz xabar yuborilmaydi
2. **Sensitive Data**: Xabarda to'liq ma'lumot emas, ID orqali link
3. **Rate Limiting**: Telegram API limitlarini hurmat qilish
4. **Error Handling**: Xatolar loglanadi, lekin tranzaksiya yaratishni to'xtatmaydi

## 🚀 Implementation Order

**Bugun:**
1. Models yaratamiz (3ta)
2. Migrations
3. Django Admin basic config

**Ertaga:**
1. Bot registration command
2. Message formatter
3. Celery task

**Keyingi kun:**
1. Signal/Hook integration
2. Testing
3. Bug fixes

## 💡 Qo'shimcha Tavsiyalar

1. **Graceful Degradation**: Telegram xato bersa, transaction baribir yaratilishi kerak
2. **Monitoring**: Celery task muvaffaqiyat/xato statistikasi
3. **Admin Dashboard**: Yuborilgan xabarlar soni, xatolar
4. **Notification Queue**: Tezkor yuborish uchun Celery priority queue
5. **Message Templates**: Har xil til uchun templatelar (uz/ru/en)

## 📝 Migration Strategy

```bash
# 1. Models yaratish
python manage.py makemigrations

# 2. Migrate
python manage.py migrate

# 3. Admin'da test qilish
python manage.py createsuperuser  # agar yo'q bo'lsa

# 4. Bot test qilish
# - Bot'ni guruhga qo'shish
# - /register command
# - Admin'da verify qilish
# - Test transaction yaratish
```

---

**Xulosa**: Bu yechim scalable, maintainable va production-ready. Server yuklamasi minimal (Celery async), xatolar handle qilinadi, va admin interface qulay. 

Qanday ko'rinadi? Boshlay-mi? 🚀
