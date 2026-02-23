"""
Push Notification модулі - Web Push API арқылы хабарламалар жіберу
"""

import json
import asyncio
import os
import base64
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from pywebpush import webpush, WebPushException
from py_vapid import Vapid

# VAPID кілттері
VAPID_PRIVATE_KEY_PATH = "vapid_private.pem"
VAPID_CLAIMS = {"sub": "mailto:admin@univer.app"}


def decode_credentials(encoded: str) -> tuple[str, str] | None:
    """Base64-тен credentials-ты дешифрлау"""
    try:
        decoded = base64.b64decode(encoded.encode()).decode()
        if ":" in decoded:
            username, password = decoded.split(":", 1)
            return username, password
    except Exception:
        pass
    return None


# Subscription деректерін сақтау үшін файл
SUBSCRIPTIONS_FILE = "subscriptions.json"
LAST_STATE_FILE = "last_state.json"
NOTIFICATION_HISTORY_FILE = "notification_history.json"


class PushNotificationService:
    """Push хабарламаларды басқаратын сервис"""

    def __init__(self):
        self._init_vapid()
        self.subscriptions: Dict[str, Dict[str, Any]] = self._load_subscriptions()
        self.notification_history: Dict[str, List[Dict[str, Any]]] = (
            self._load_notification_history()
        )

    def _init_vapid(self):
        """VAPID кілттерін жүктеу немесе генерациялау"""
        if os.path.exists(VAPID_PRIVATE_KEY_PATH):
            try:
                self.vapid = Vapid.from_file(VAPID_PRIVATE_KEY_PATH)
            except Exception:
                self.vapid = Vapid()
                self.vapid.generate_keys()
                self.vapid.save_key(VAPID_PRIVATE_KEY_PATH)
        else:
            self.vapid = Vapid()
            self.vapid.generate_keys()
            self.vapid.save_key(VAPID_PRIVATE_KEY_PATH)

        # Public key-ді де сақтап қояйық (клиентке керек болуы мүмкін)
        if not os.path.exists("vapid_public.pem"):
            self.vapid.save_public_key("vapid_public.pem")

    def _load_subscriptions(self) -> Dict[str, Dict[str, Any]]:
        """Файлдан жазылуларды жүктеу"""
        try:
            with open(SUBSCRIPTIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_subscriptions(self):
        """Жазылуларды файлға сақтау"""
        try:
            with open(SUBSCRIPTIONS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.subscriptions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving subscriptions: {e}")

    def subscribe(
        self,
        user_id: str,
        subscription_info: Dict[str, Any],
        univer_code: str = "kstu",
        encoded_creds: Optional[str] = None,
        language: str = "kk",
        settings: Optional[Dict[str, bool]] = None,
    ) -> bool:
        """Пайдаланушыны хабарламаларға жазу"""
        # Default settings - барлық хабарламалар қосулы
        default_settings = {
            "new_grades": True,  # Жаңа бағалар
            "lesson_reminders": True,  # Сабаққа ескерту
            "tomorrow_schedule": True,  # Ертеңгі кесте
            "exam_reminders": True,  # Емтихан ескертулері
        }

        # Default time settings - икемді уақыт параметрлері
        default_time_settings = {
            "lesson_reminder_minutes": 10,  # Сабаққа қанша минут қалғанда
            "evening_schedule_time": "22:00",  # Ертеңгі кесте уақыты
            "quiet_hours": {
                "enabled": False,
                "start": "23:00",
                "end": "07:00",
            },
        }

        self.subscriptions[user_id] = {
            "subscription": subscription_info,
            "univer_code": univer_code,
            "creds": encoded_creds,
            "lang": language,
            "settings": settings or default_settings,
            "time_settings": default_time_settings,
            "updated_at": datetime.now().isoformat(),
        }
        self._save_subscriptions()
        return True

    def unsubscribe(self, user_id: str) -> bool:
        """Пайдаланушыны хабарламалардан шығару"""
        if user_id in self.subscriptions:
            del self.subscriptions[user_id]
            self._save_subscriptions()
            return True
        return False

    def update_settings(self, user_id: str, settings: Dict[str, bool]) -> bool:
        """Хабарлама параметрлерін жаңарту"""
        if user_id in self.subscriptions:
            self.subscriptions[user_id]["settings"] = settings
            self.subscriptions[user_id]["updated_at"] = datetime.now().isoformat()
            self._save_subscriptions()
            return True
        return False

    def get_settings(self, user_id: str) -> Optional[Dict[str, bool]]:
        """Пайдаланушының хабарлама параметрлерін алу"""
        if user_id in self.subscriptions:
            return self.subscriptions[user_id].get(
                "settings",
                {
                    "new_grades": True,
                    "lesson_reminders": True,
                    "tomorrow_schedule": True,
                    "exam_reminders": True,
                },
            )
        return None

    def is_subscribed(self, user_id: str) -> bool:
        """Пайдаланушы жазылған ба тексеру"""
        return user_id in self.subscriptions

    def _load_notification_history(self) -> Dict[str, List[Dict[str, Any]]]:
        """Хабарлама тарихын жүктеу"""
        try:
            with open(NOTIFICATION_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_notification_history(self):
        """Хабарлама тарихын сақтау"""
        try:
            with open(NOTIFICATION_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.notification_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving notification history: {e}")

    def _add_to_history(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Хабарламаны тарихқа қосу"""
        import uuid

        notification_id = str(uuid.uuid4())

        if user_id not in self.notification_history:
            self.notification_history[user_id] = []

        notification = {
            "id": notification_id,
            "type": notification_type,
            "title": title,
            "body": body,
            "data": data or {},
            "sent_at": datetime.now().isoformat(),
            "read": False,
            "clicked": False,
        }

        self.notification_history[user_id].insert(0, notification)

        # Тек соңғы 100 хабарламаны сақтау
        if len(self.notification_history[user_id]) > 100:
            self.notification_history[user_id] = self.notification_history[user_id][
                :100
            ]

        self._save_notification_history()
        return notification_id

    def get_notification_history(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Пайдаланушының хабарлама тарихын алу"""
        history = self.notification_history.get(user_id, [])
        return history[offset : offset + limit]

    def mark_notification_read(self, user_id: str, notification_id: str) -> bool:
        """Хабарламаны оқылған деп белгілеу"""
        if user_id not in self.notification_history:
            return False

        for notification in self.notification_history[user_id]:
            if notification["id"] == notification_id:
                notification["read"] = True
                self._save_notification_history()
                return True
        return False

    def mark_notification_clicked(self, user_id: str, notification_id: str) -> bool:
        """Хабарламаны басылған деп белгілеу"""
        if user_id not in self.notification_history:
            return False

        for notification in self.notification_history[user_id]:
            if notification["id"] == notification_id:
                notification["clicked"] = True
                notification["read"] = True  # Басылса автоматты оқылған
                self._save_notification_history()
                return True
        return False

    def delete_notification(self, user_id: str, notification_id: str) -> bool:
        """Хабарламаны жою"""
        if user_id not in self.notification_history:
            return False

        original_length = len(self.notification_history[user_id])
        self.notification_history[user_id] = [
            n for n in self.notification_history[user_id] if n["id"] != notification_id
        ]

        if len(self.notification_history[user_id]) < original_length:
            self._save_notification_history()
            return True
        return False

    def clear_notification_history(self, user_id: str) -> bool:
        """Барлық хабарлама тарихын тазалау"""
        if user_id in self.notification_history:
            self.notification_history[user_id] = []
            self._save_notification_history()
            return True
        return False

    def get_notification_stats(self, user_id: str) -> Dict[str, Any]:
        """Хабарлама статистикасын алу"""
        history = self.notification_history.get(user_id, [])

        if not history:
            return {
                "total_sent": 0,
                "total_read": 0,
                "total_clicked": 0,
                "read_rate": 0.0,
                "click_rate": 0.0,
                "by_type": {},
            }

        total_sent = len(history)
        total_read = sum(1 for n in history if n["read"])
        total_clicked = sum(1 for n in history if n["clicked"])

        # Түрі бойынша статистика
        by_type: Dict[str, Dict[str, int]] = {}
        for notification in history:
            n_type = notification["type"]
            if n_type not in by_type:
                by_type[n_type] = {"sent": 0, "read": 0, "clicked": 0}

            by_type[n_type]["sent"] += 1
            if notification["read"]:
                by_type[n_type]["read"] += 1
            if notification["clicked"]:
                by_type[n_type]["clicked"] += 1

        return {
            "total_sent": total_sent,
            "total_read": total_read,
            "total_clicked": total_clicked,
            "read_rate": (
                round((total_read / total_sent) * 100, 2) if total_sent > 0 else 0.0
            ),
            "click_rate": (
                round((total_clicked / total_sent) * 100, 2) if total_sent > 0 else 0.0
            ),
            "by_type": by_type,
        }

    def update_time_settings(self, user_id: str, time_settings: Dict[str, Any]) -> bool:
        """Уақыт параметрлерін жаңарту"""
        if user_id in self.subscriptions:
            self.subscriptions[user_id]["time_settings"] = time_settings
            self.subscriptions[user_id]["updated_at"] = datetime.now().isoformat()
            self._save_subscriptions()
            return True
        return False

    def get_time_settings(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Уақыт параметрлерін алу"""
        if user_id in self.subscriptions:
            return self.subscriptions[user_id].get(
                "time_settings",
                {
                    "lesson_reminder_minutes": 10,
                    "evening_schedule_time": "22:00",
                    "quiet_hours": {"enabled": False, "start": "23:00", "end": "07:00"},
                },
            )
        return None

    def is_quiet_hours(self, user_id: str) -> bool:
        """Тыныш сағаттар уақыты ма тексеру"""
        time_settings = self.get_time_settings(user_id)
        if not time_settings:
            return False

        quiet_hours = time_settings.get("quiet_hours", {})
        if not quiet_hours.get("enabled", False):
            return False

        now = datetime.now()
        current_time = now.strftime("%H:%M")

        start_time = quiet_hours.get("start", "23:00")
        end_time = quiet_hours.get("end", "07:00")

        # Түнгі уақытты тексеру (мысалы 23:00 - 07:00)
        if start_time > end_time:
            return current_time >= start_time or current_time < end_time
        else:
            return start_time <= current_time < end_time

    async def send_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        icon: str = "/images/icons.svg",
        badge: str = "/images/badge.png",
        tag: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        actions: Optional[List[Dict[str, str]]] = None,
        vibrate: Optional[List[int]] = None,
        require_interaction: bool = False,
        notification_type: str = "general",
    ) -> bool:
        """Бір пайдаланушыға хабарлама жіберу"""

        sub_data = self.subscriptions.get(user_id)
        if not sub_data:
            return False

        # Тыныш сағаттарды тексеру
        if self.is_quiet_hours(user_id):
            print(f"Quiet hours active for {user_id}, skipping notification")
            # Тарихқа қосамыз, бірақ жібермейміз
            self._add_to_history(user_id, notification_type, title, body, data)
            return False

        subscription = sub_data["subscription"]

        payload = {
            "title": title,
            "body": body,
            "icon": icon,
            "badge": badge,
            "timestamp": int(datetime.now().timestamp() * 1000),
            "requireInteraction": require_interaction,
        }

        if tag:
            payload["tag"] = tag
        if data:
            payload["data"] = data
        if actions:
            payload["actions"] = actions
        if vibrate:
            payload["vibrate"] = vibrate

        try:
            webpush(
                subscription_info=subscription,
                data=json.dumps(payload),
                vapid_private_key=VAPID_PRIVATE_KEY_PATH,
                vapid_claims=VAPID_CLAIMS,
            )
            # Тарихқа қосу
            self._add_to_history(user_id, notification_type, title, body, data)
            return True
        except WebPushException as e:
            print(f"Push error for {user_id}: {e}")
            # Subscription жарамсыз болса, өшіру
            if e.response and e.response.status_code in [404, 410]:
                self.unsubscribe(user_id)
            return False

    async def send_to_all(self, title: str, body: str, **kwargs) -> Dict[str, bool]:
        """Барлық жазылған пайдаланушыларға хабарлама жіберу"""
        results = {}
        for user_id in list(self.subscriptions.keys()):
            results[user_id] = await self.send_notification(
                user_id, title, body, **kwargs
            )
        return results

    # Арнайы хабарлама түрлері
    async def send_new_grade_notification(
        self, user_id: str, subject: str, grade: str, grade_type: str = "АБ"
    ) -> bool:
        """Жаңа баға туралы хабарлама"""
        return await self.send_notification(
            user_id=user_id,
            title=f"📝 Жаңа баға: {subject}",
            body=f"{grade_type}: {grade} балл",
            tag=f"grade-{subject}",
            data={
                "type": "new_grade",
                "subject": subject,
                "grade": grade,
                "url": "/attestation",
            },
            actions=[
                {"action": "view", "title": "Қарау"},
                {"action": "dismiss", "title": "Жабу"},
            ],
            vibrate=[200, 100, 200],
            require_interaction=True,
            notification_type="new_grade",
        )

    async def send_lesson_reminder(
        self,
        user_id: str,
        subject: str,
        teacher: str,
        room: str,
        minutes_left: int = 10,
    ) -> bool:
        """Сабаққа 10 минут қалды деген хабарлама"""
        return await self.send_notification(
            user_id=user_id,
            title=f"⏰ Сабаққа {minutes_left} минут қалды!",
            body=f"{subject}\n📍 {room} | 👨‍🏫 {teacher}",
            tag=f"lesson-reminder-{subject}",
            data={"type": "lesson_reminder", "subject": subject, "url": "/schedule"},
            actions=[{"action": "view_schedule", "title": "Кестені ашу"}],
            vibrate=[300, 100, 300, 100, 300],
            notification_type="lesson_reminder",
        )

    async def send_tomorrow_schedule(
        self, user_id: str, lessons: List[Dict[str, str]]
    ) -> bool:
        """Ертеңгі кестені кешкі уақытта жіберу"""
        if not lessons:
            body = "Ертең сабақ жоқ! 🎉"
        else:
            body = "\n".join(
                [
                    f"• {l['time']} - {l['subject']}"
                    for l in lessons[:5]  # Ең көбі 5 сабақ
                ]
            )
            if len(lessons) > 5:
                body += f"\n... және тағы {len(lessons) - 5} сабақ"

        return await self.send_notification(
            user_id=user_id,
            title="📅 Ертеңгі кесте",
            body=body,
            tag="tomorrow-schedule",
            data={"type": "tomorrow_schedule", "url": "/schedule"},
            actions=[{"action": "view", "title": "Толық кестені көру"}],
            notification_type="tomorrow_schedule",
        )

    async def send_exam_reminder(
        self, user_id: str, subject: str, date: str, time: str, room: str
    ) -> bool:
        """Емтихан туралы ескерту"""
        return await self.send_notification(
            user_id=user_id,
            title=f"🎓 Емтихан: {subject}",
            body=f"📅 {date} | ⏰ {time}\n📍 {room}",
            tag=f"exam-{subject}",
            data={"type": "exam_reminder", "subject": subject, "url": "/exams"},
            actions=[
                {"action": "view", "title": "Толығырақ"},
                {"action": "add_calendar", "title": "Күнтізбеге қосу"},
            ],
            vibrate=[500, 200, 500],
            require_interaction=True,
        )


# Глобал сервис инстанциясы
push_service = PushNotificationService()


# Фондық тапсырмалар (Background Tasks)
class ScheduledNotifications:
    """Жоспарланған хабарламалар"""

    def __init__(self, push_service: PushNotificationService):
        self.push_service = push_service
        self.running = False

    async def start(self):
        """Фондық тапсырмаларды бастау"""
        self.running = True
        asyncio.create_task(self._check_lessons_loop())
        asyncio.create_task(self._evening_schedule_loop())
        asyncio.create_task(self._check_grades_loop())

    async def stop(self):
        """Фондық тапсырмаларды тоқтату"""
        self.running = False

    async def _check_lessons_loop(self):
        """Сабаққа 10 минут қалды ма тексеру (минут сайын)"""
        while self.running:
            try:
                await self._check_upcoming_lessons()
            except Exception as e:
                print(f"Lesson check error: {e}")
            await asyncio.sleep(60)  # Минут сайын

    async def _check_grades_loop(self):
        """Жаңа бағаларды тексеру (30 минут сайын)"""
        while self.running:
            try:
                await self._check_new_grades()
            except Exception as e:
                print(f"Grade check error: {e}")
            await asyncio.sleep(1800)  # 30 минут

    async def _evening_schedule_loop(self):
        """Кешкі уақытта ертеңгі кестені жіберу (икемді уақыт)"""
        while self.running:
            now = datetime.now()

            # Барлық пайдаланушылардың уақытын тексеру
            # Ең ерте уақытты табу
            earliest_time = "22:00"  # Default
            for sub_data in self.push_service.subscriptions.values():
                time_settings = sub_data.get("time_settings", {})
                user_time = time_settings.get("evening_schedule_time", "22:00")
                if user_time < earliest_time:
                    earliest_time = user_time

            # Келесі уақытты есептеу
            hour, minute = map(int, earliest_time.split(":"))
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if now >= target:
                target += timedelta(days=1)

            wait_seconds = (target - now).total_seconds()
            print(
                f"Evening schedule waiter: waiting {wait_seconds} seconds until {earliest_time}"
            )
            await asyncio.sleep(wait_seconds)

            if self.running:
                try:
                    await self._send_tomorrow_schedules()
                except Exception as e:
                    print(f"Evening schedule error: {e}")
                # Келесі күнді күту үшін сәл кідіріс
                await asyncio.sleep(60)

    async def _get_univer_instance(self, sub_data: Dict[str, Any]):
        """Пайдаланушыға сәйкес Univer инстанциясын алу"""
        from univers import get_univer, KSTU

        univer_code = sub_data.get("univer_code", "kstu")
        creds = decode_credentials(sub_data.get("creds", ""))

        if not creds:
            return None

        username, password = creds
        UniverClass = get_univer(univer_code) or KSTU
        univer = UniverClass()
        try:
            await univer.login(username, password)
            return univer
        except Exception:
            return None

    async def _check_upcoming_lessons(self):
        """Жақын сабақтарды тексеру"""
        now = datetime.now()
        weekday = now.weekday()  # 0-6 (Дүйсенбі-Жексенбі)

        for user_id, sub_data in self.push_service.subscriptions.items():
            # Сабаққа хабарлама қосулы ма тексеру
            settings = sub_data.get("settings", {})
            if not settings.get("lesson_reminders", True):
                continue

            # Икемді уақытты алу
            time_settings = sub_data.get("time_settings", {})
            reminder_minutes = time_settings.get("lesson_reminder_minutes", 10)

            univer = await self._get_univer_instance(sub_data)
            if not univer:
                continue

            try:
                # Кестені алу
                schedule_data = await univer.get_schedule()
                # Бүгінгі сабақтар
                today_lessons = [l for l in schedule_data.lessons if l.day == weekday]

                for lesson in today_lessons:
                    # Сабақтың басталу уақыты
                    l_start = lesson.time.split("-")[0].strip()
                    l_time = datetime.strptime(l_start, "%H:%M")
                    l_datetime = now.replace(
                        hour=l_time.hour, minute=l_time.minute, second=0, microsecond=0
                    )

                    diff = (l_datetime - now).total_seconds() / 60

                    # Икемді уақытпен тексеру (мысалы 10 минут ± 0.5)
                    if (reminder_minutes - 0.5) <= diff <= (reminder_minutes + 0.5):
                        await self.push_service.send_lesson_reminder(
                            user_id=user_id,
                            subject=lesson.subject,
                            teacher=lesson.teacher,
                            room=lesson.audience,
                            minutes_left=reminder_minutes,
                        )
            except Exception as e:
                print(f"Error checking schedule for {user_id}: {e}")

    async def _check_new_grades(self):
        """Жаңа бағаларды тексеру"""
        states = self._load_states()

        for user_id, sub_data in self.push_service.subscriptions.items():
            # Бағалар хабарламасы қосулы ма тексеру
            settings = sub_data.get("settings", {})
            if not settings.get("new_grades", True):
                continue

            univer = await self._get_univer_instance(sub_data)
            if not univer:
                continue

            univer.language = sub_data.get("lang", "kk")

            try:
                attestations = await univer.get_attestation()
                current_grades = {}

                for att in attestations:
                    # Пән мен бағаларды жинақтау
                    key = att.subject
                    grades_dict = {}
                    for i, mark in enumerate(att.attestation):
                        grades_dict[f"att_{i+1}"] = mark.value
                    current_grades[key] = grades_dict

                last_user_state = states.get(user_id, {})

                # Салыстыру
                for subject, grades in current_grades.items():
                    old_grades = last_user_state.get(subject, {})

                    # АБ1 өзгерсе
                    if grades["ab1"] != old_grades.get("ab1") and grades["ab1"]:
                        await self.push_service.send_new_grade_notification(
                            user_id, subject, str(grades["ab1"]), "АБ1"
                        )

                    # АБ2 өзгерсе
                    elif grades["ab2"] != old_grades.get("ab2") and grades["ab2"]:
                        await self.push_service.send_new_grade_notification(
                            user_id, subject, str(grades["ab2"]), "АБ2"
                        )

                    # Емтихан өзгерсе
                    elif grades["exam"] != old_grades.get("exam") and grades["exam"]:
                        await self.push_service.send_new_grade_notification(
                            user_id, subject, str(grades["exam"]), "Емтихан"
                        )

                # Жаңа күйді сақтау
                states[user_id] = current_grades

            except Exception as e:
                print(f"Error checking grades for {user_id}: {e}")

        self._save_states(states)

    async def _send_tomorrow_schedules(self):
        """Барлық пайдаланушыларға ертеңгі кестені жіберу"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        tomorrow_weekday = (now.weekday() + 1) % 7

        for user_id, sub_data in self.push_service.subscriptions.items():
            # Ертеңгі кесте хабарламасы қосулы ма тексеру
            settings = sub_data.get("settings", {})
            if not settings.get("tomorrow_schedule", True):
                continue

            # Пайдаланушының уақытын тексеру
            time_settings = sub_data.get("time_settings", {})
            user_schedule_time = time_settings.get("evening_schedule_time", "22:00")

            # Тек пайдаланушының уақыты келсе жіберу
            if current_time < user_schedule_time or current_time >= (
                datetime.strptime(user_schedule_time, "%H:%M") + timedelta(minutes=1)
            ).strftime("%H:%M"):
                continue

            univer = await self._get_univer_instance(sub_data)
            if not univer:
                continue

            try:
                schedule_data = await univer.get_schedule()
                tomorrow_lessons = [
                    {"time": l.time, "subject": l.subject}
                    for l in schedule_data.lessons
                    if l.day == tomorrow_weekday
                ]

                await self.push_service.send_tomorrow_schedule(
                    user_id, tomorrow_lessons
                )
            except Exception as e:
                print(f"Error sending tomorrow schedule for {user_id}: {e}")

    def _load_states(self) -> Dict[str, Any]:
        """Соңғы күйлерді (бағаларды) файлдан жүктеу"""
        try:
            with open(LAST_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_states(self, states: Dict[str, Any]):
        """Күйлерді файлға сақтау"""
        try:
            with open(LAST_STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(states, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving states: {e}")


scheduled_notifications = ScheduledNotifications(push_service)
