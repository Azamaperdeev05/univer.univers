"""
Push Notification модулі - Web Push API арқылы хабарламалар жіберу
"""

import json
import asyncio
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


class PushNotificationService:
    """Push хабарламаларды басқаратын сервис"""

    def __init__(self):
        self.vapid = Vapid.from_file(VAPID_PRIVATE_KEY_PATH)
        self.subscriptions: Dict[str, Dict[str, Any]] = self._load_subscriptions()

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
    ) -> bool:
        """Пайдаланушыны хабарламаларға жазу"""
        self.subscriptions[user_id] = {
            "subscription": subscription_info,
            "univer_code": univer_code,
            "creds": encoded_creds,
            "lang": language,
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
    ) -> bool:
        """Бір пайдаланушыға хабарлама жіберу"""

        sub_data = self.subscriptions.get(user_id)
        if not sub_data:
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
        """Кешкі 22:00-де ертеңгі кестені жіберу"""
        while self.running:
            now = datetime.now()

            # Келесі 22:00-ді есептеу
            target = now.replace(hour=22, minute=0, second=0, microsecond=0)
            if now >= target:
                target += timedelta(days=1)

            wait_seconds = (target - now).total_seconds()
            print(
                f"Evening schedule waiter: waiting {wait_seconds} seconds until 22:00"
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
        # JS-тегідей 0-6 конвертациясы (біздің кестелерде 0 - Дүйсенбі)

        current_time = now.strftime("%H:%M")

        for user_id, sub_data in self.push_service.subscriptions.items():
            # Сабаққа хабарлама қосулы ма?
            # settings жоқ болса default True деп алайық
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

                    # 10 минут қалса (9.5-тен 10.5-ке дейін, қайталанбау үшін)
                    if 9.5 <= diff <= 10.5:
                        await self.push_service.send_lesson_reminder(
                            user_id=user_id,
                            subject=lesson.subject,
                            teacher=lesson.teacher,
                            room=lesson.audience,
                            minutes_left=10,
                        )
            except Exception as e:
                print(f"Error checking schedule for {user_id}: {e}")

    async def _check_new_grades(self):
        """Жаңа бағаларды тексеру"""
        states = self._load_states()

        for user_id, sub_data in self.push_service.subscriptions.items():
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
                    current_grades[key] = {
                        "ab1": att.first_att,
                        "ab2": att.second_att,
                        "exam": att.exam,
                    }

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
        tomorrow_weekday = (now.weekday() + 1) % 7

        for user_id, sub_data in self.push_service.subscriptions.items():
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
