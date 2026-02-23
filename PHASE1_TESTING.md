# 🧪 Фаза 1 - Тестілеу нұсқаулығы

## ✅ Құрастыру сәтті өтті!

Frontend құрастыру сәтті аяқталды. Бірнеше ескертулер бар, бірақ олар критикалық емес.

---

## 🚀 Серверді іске қосу:

```bash
# Негізгі папкада
python server.py
```

Сервер порт 7435-те іске қосылады: http://localhost:7435

---

## 🧪 Тестілеу қадамдары:

### 1. Жазылу (Subscribe)
1. Браузерде http://localhost:7435 ашыңыз
2. Login жасаңыз
3. Settings бетіне өтіңіз
4. "Хабарламаларды қосу" батырмасын басыңыз
5. Браузер рұқсат сұрайды - "Allow" басыңыз

### 2. Тестілік хабарлама
Settings бетінде "Тестілік хабарлама жіберу" батырмасын басыңыз.

**API арқылы:**
```bash
curl -X POST "http://localhost:7435/api/push/test?lang=kk" \
  --cookie "_uc=YOUR_COOKIE"
```

### 3. Хабарлама тарихы

**Тарихты алу:**
```bash
curl "http://localhost:7435/api/push/history?limit=10" \
  --cookie "_uc=YOUR_COOKIE"
```

**Оқылған деп белгілеу:**
```bash
curl -X POST "http://localhost:7435/api/push/history/{notification_id}/mark-read" \
  --cookie "_uc=YOUR_COOKIE"
```

**Статистика:**
```bash
curl "http://localhost:7435/api/push/stats" \
  --cookie "_uc=YOUR_COOKIE"
```

### 4. Уақыт параметрлері

**Параметрлерді жаңарту:**
```bash
curl -X POST "http://localhost:7435/api/push/time-settings" \
  -H "Content-Type: application/json" \
  --cookie "_uc=YOUR_COOKIE" \
  -d '{
    "time_settings": {
      "lesson_reminder_minutes": 15,
      "evening_schedule_time": "21:00",
      "quiet_hours": {
        "enabled": true,
        "start": "23:00",
        "end": "07:00"
      }
    }
  }'
```

**Статусты тексеру:**
```bash
curl "http://localhost:7435/api/push/status" \
  --cookie "_uc=YOUR_COOKIE"
```

### 5. Python Console арқылы тестілеу

```python
# Python console ашыңыз
python

# Импорттар
from core.push_notifications import push_service
import asyncio

# Жазылу статусын тексеру
print(push_service.is_subscribed("your_username"))

# Тарихты алу
history = push_service.get_notification_history("your_username", limit=10)
print(f"Хабарламалар саны: {len(history)}")

# Статистика
stats = push_service.get_notification_stats("your_username")
print(f"Жіберілген: {stats['total_sent']}")
print(f"Оқылған: {stats['total_read']}")
print(f"Оқылу пайызы: {stats['read_rate']}%")

# Уақыт параметрлері
time_settings = push_service.get_time_settings("your_username")
print(time_settings)

# Тыныш сағаттарды тексеру
is_quiet = push_service.is_quiet_hours("your_username")
print(f"Тыныш сағаттар: {is_quiet}")

# Тестілік хабарлама жіберу
asyncio.run(push_service.send_notification(
    user_id="your_username",
    title="Тест хабарлама",
    body="Python console-ден жіберілді",
    notification_type="test"
))
```

---

## 📊 Деректер файлдарын тексеру:

### 1. subscriptions.json
```bash
cat subscriptions.json
```

Көруіңіз керек:
```json
{
  "username": {
    "subscription": {...},
    "settings": {
      "new_grades": true,
      "lesson_reminders": true,
      "tomorrow_schedule": true,
      "exam_reminders": true
    },
    "time_settings": {
      "lesson_reminder_minutes": 10,
      "evening_schedule_time": "22:00",
      "quiet_hours": {
        "enabled": false,
        "start": "23:00",
        "end": "07:00"
      }
    }
  }
}
```

### 2. notification_history.json
```bash
cat notification_history.json
```

Көруіңіз керек:
```json
{
  "username": [
    {
      "id": "uuid",
      "type": "test",
      "title": "Тест хабарлама",
      "body": "...",
      "sent_at": "2026-02-23T...",
      "read": false,
      "clicked": false
    }
  ]
}
```

---

## 🔍 Background Tasks тексеру:

Сервер іске қосылғанда логта көруіңіз керек:
```
Background tasks started
Evening schedule waiter: waiting ... seconds until 22:00
```

### Сабаққа ескерту тестілеу:
1. Уақыт параметрлерін 1 минутқа қойыңыз
2. Кестеде 1 минуттан кейін сабақ болуы керек
3. 1 минут күтіңіз
4. Хабарлама келуі керек

### Ертеңгі кесте тестілеу:
1. Уақытты ағымдағы уақыттан 1 минут кейінге қойыңыз
2. 1 минут күтіңіз
3. Хабарлама келуі керек

---

## ⚠️ Жиі кездесетін мәселелер:

### 1. Хабарлама келмейді
**Себептер:**
- Браузер рұқсат бермеген
- Service Worker тіркелмеген
- Тыныш сағаттар қосулы
- Subscription жарамсыз

**Шешім:**
```python
# Python console
from core.push_notifications import push_service

# Жазылу бар ма?
print(push_service.is_subscribed("username"))

# Тыныш сағаттар ма?
print(push_service.is_quiet_hours("username"))

# Subscription деректері
print(push_service.subscriptions.get("username"))
```

### 2. Тарих сақталмайды
**Себеп:** Файлға жазу рұқсаты жоқ

**Шешім:**
```bash
# Файл бар ма тексеру
ls -la notification_history.json

# Рұқсаттарды тексеру
# Windows-та:
icacls notification_history.json
```

### 3. Background tasks жұмыс істемейді
**Себеп:** Сервер дұрыс іске қоспаған

**Шешім:**
```python
# server.py-де тексеру
# on_startup функциясы шақырылды ма?
print("Background tasks started")  # Логта болуы керек
```

---

## ✅ Сәтті тестілеу белгілері:

1. ✅ Тестілік хабарлама келді
2. ✅ Хабарлама тарихында көрінді
3. ✅ Статистика дұрыс көрсетіледі
4. ✅ Уақыт параметрлері сақталды
5. ✅ Тыныш сағаттар жұмыс істейді
6. ✅ Background tasks іске қосылды

---

## 📝 Келесі қадамдар:

1. Settings бетінде UI жасау:
   - Хабарлама тарихы көрсету
   - Уақыт параметрлерін басқару
   - Тыныш сағаттарды қосу/өшіру
   - Статистика көрсету

2. Фаза 2-ге өту:
   - Ақылды хабарламалар
   - Топтық хабарламалар
   - Статистика дашборды

---

## 🎉 Дайын!

Барлық функциялар жұмыс істеуі керек. Егер мәселелер болса, логтарды тексеріңіз:
```bash
# Сервер логтары
python server.py

# Браузер консолі
F12 -> Console
```
