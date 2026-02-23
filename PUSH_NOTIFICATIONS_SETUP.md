# 🔔 Push Notifications орнату нұсқаулығы

## 🎯 Жаңа мүмкіндіктер!

### ✨ Қосылған функциялар:

1. ✅ **Хабарлама параметрлері** - пайдаланушы қандай хабарламаларды алғысы келетінін таңдай алады
   - Жаңа бағалар туралы хабарламалар
   - Сабаққа 10 минут қалғанда ескерту
   - Ертеңгі кесте (кешке 22:00)
   - Емтихан ескертулері

2. ✅ **Тестілеу функциясы** - хабарламаларды тестілеу батырмасы
   - Settings бетінде "Тестілік хабарлама жіберу" батырмасы
   - Тілге сәйкес хабарлама жіберіледі

3. ✅ **Статус тексеру** - жазылу статусын көру
   - Пайдаланушы жазылған ба тексеру
   - Қандай хабарламалар қосулы екенін көру

---

## 🚀 Қалай жұмыс істейді:

### 1️⃣ Пайдаланушы Settings-ке өтеді
- `/settings` бетін ашады

### 2️⃣ "Хабарламаларды қосу" батырмасын басады
- Браузер рұқсат сұрайды
- Пайдаланушы "Allow" басады

### 3️⃣ Frontend subscription жасайды
```typescript
// Service Worker арқылы
const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: VAPID_PUBLIC_KEY
})
```

### 4️⃣ Subscription серверге жіберіледі
```typescript
POST /api/push/subscribe?lang=kk
Body: { endpoint, keys: { p256dh, auth } }
Cookies: _uc (credentials), univer_code
```

### 5️⃣ Backend subscription-ды сақтайды
```python
# subscriptions.json файлына жазылады
{
    "username": {
        "subscription": {...},
        "univer_code": "kstu",
        "creds": "base64_encoded",
        "lang": "kk",
        "updated_at": "2026-02-23T..."
    }
}
```

### 6️⃣ Background tasks іске қосылады
```python
# server.py-де
app.on_startup.append(on_startup)

async def on_startup(app):
    await scheduled_notifications.start()
```

---

## 📊 Background tasks:

### 1. Сабаққа ескерту (минут сайын)
- Сабаққа 10 минут қалғанда хабарлама жіберіледі
- Тек ағымдағы күнгі сабақтар тексеріледі
- **Параметр:** `lesson_reminders` (қосулы/өшірулі)

### 2. Жаңа бағалар (30 минут сайын)
- Бағалар өзгерсе хабарлама жіберіледі
- АБ1, АБ2, Емтихан бағалары тексеріледі
- **Параметр:** `new_grades` (қосулы/өшірулі)

### 3. Ертеңгі кесте (кешке 22:00)
- Ертеңгі сабақтар туралы хабарлама
- Барлық жазылған пайдаланушыларға
- **Параметр:** `tomorrow_schedule` (қосулы/өшірулі)

### 4. Емтихан ескертулері
- Емтихан туралы хабарламалар
- **Параметр:** `exam_reminders` (қосулы/өшірулі)

---

## 🎛️ Жаңа API endpoint-тар:

### 1. Статус тексеру
```http
GET /api/push/status
Response: {
    "subscribed": true,
    "settings": {
        "new_grades": true,
        "lesson_reminders": true,
        "tomorrow_schedule": true,
        "exam_reminders": true
    }
}
```

### 2. Параметрлерді жаңарту
```http
POST /api/push/settings
Body: {
    "settings": {
        "new_grades": true,
        "lesson_reminders": false,
        "tomorrow_schedule": true,
        "exam_reminders": true
    }
}
Response: {
    "status": "ok",
    "settings": {...}
}
```

### 3. Тестілік хабарлама
```http
POST /api/push/test?lang=kk
Response: {
    "status": "ok"
}
```

---

## 🧪 Тестілеу:

### 1. Settings бетінде хабарлама параметрлері
```typescript
// Жазылу статусын тексеру
const status = await checkSubscriptionStatus()
console.log(status) // { subscribed: true, settings: {...} }

// Параметрлерді жаңарту
await updatePushSettings({
    new_grades: true,
    lesson_reminders: false,
    tomorrow_schedule: true,
    exam_reminders: true
})
```

### 2. Тестілік хабарлама жіберу
```typescript
// Settings бетінде "Тестілік хабарлама жіберу" батырмасы
await sendTestNotification('kk') // тілді көрсету
```

### 3. Backend-тен қолмен жіберу (тестілеу үшін)
```python
# Python console-де
from core.push_notifications import push_service
import asyncio

asyncio.run(push_service.send_notification(
    user_id="username",
    title="Тест хабарлама",
    body="Backend-тен жіберілді"
))
```

---

## 🔧 Қажетті файлдар:

### Backend:
- ✅ `vapid_private.pem` - VAPID private key
- ✅ `vapid_public.pem` - VAPID public key
- ✅ `subscriptions.json` - Жазылулар (автоматты жасалады)
- ✅ `last_state.json` - Соңғы бағалар күйі (автоматты)

### Frontend:
- ✅ `VAPID_PUBLIC_KEY` - push-notifications.ts-те
- ✅ Service Worker - sw.ts
- ✅ Settings беті - settings.svelte

---

## ⚠️ Маңызды ескертулер:

1. **HTTPS қажет** - Push notifications тек HTTPS-те жұмыс істейді
   - Локальді тестілеу үшін: `localhost` жұмыс істейді
   - Production: SSL сертификаты қажет

2. **Service Worker тіркелуі керек**
   - PWA орнатылған болуы керек
   - `/sw.js` қолжетімді болуы керек

3. **Браузер қолдауы**
   - Chrome/Edge: ✅ Толық қолдау
   - Firefox: ✅ Толық қолдау
   - Safari (iOS): ⚠️ Шектеулі (iOS 16.4+)

4. **Background tasks іске қосылуы керек**
   ```bash
   python server.py
   # Логта көрінуі керек:
   # Background tasks started
   ```

---

## 🐛 Қателерді шешу:

### Хабарлама келмейді:

1. **Браузер консолін тексеру**
   ```javascript
   // DevTools Console
   navigator.serviceWorker.ready.then(reg => 
       reg.pushManager.getSubscription()
   ).then(sub => console.log(sub))
   ```

2. **Backend логтарын тексеру**
   ```bash
   # Subscription сақталды ма?
   cat subscriptions.json
   
   # Background tasks жұмыс істеп тұр ма?
   # Логта "Background tasks started" болуы керек
   ```

3. **VAPID кілттері дұрыс па?**
   ```bash
   # Public key тексеру
   cat vapid_public.pem
   
   # Frontend-тегі key сәйкес келуі керек
   ```

---

## ✅ Дайын!

Push Notifications енді жұмыс істеуі керек! 🎉

Егер мәселелер болса:
1. Браузер консолін тексеріңіз
2. Backend логтарын қараңыз
3. `subscriptions.json` файлын тексеріңіз
