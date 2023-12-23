import asyncio
from dataclasses import dataclass
from ..exceptions import ForbiddenException
from ..utils.logger import create_logger
from ..functions.login import login
from ..functions.get_attendance import get_attendance
from ..functions.get_attestation import get_attestation
from ..functions.get_schedule import get_schedule
from ..functions.get_exams import get_exams
from ..utils.storage import Storage


@dataclass
class Urls:
    ATTENDANCE_URL: str
    LOGIN_URL: str
    LANG_RU_URL: str
    LANG_KK_URL: str
    LANG_EN_URL: str
    ATTESTATION_URL: str
    SCHEDULE_URL: str
    EXAMS_URL: str


def auth(function):
    async def f(*args):
        univer: "Univer" = args[0]
        if univer.cookies is None:
            await univer.login()
        while 1:
            try:
                return await function(*args)
            except ForbiddenException:
                univer.logger.info("relogin")
                await univer.login()

    return f


def _get_lang_url(urls: Urls, lang: str):
    return getattr(urls, f"LANG_{lang.upper()}_URL", urls.LANG_RU_URL)


_teachers = {}
_working_teachers = set()


class Univer:
    def __init__(
        self,
        username: str,
        password: str,
        urls: Urls,
        cookies: dict[str, str] = None,
        language="ru",
        univer="",
        storage: Storage = None,
    ) -> None:
        self.username = username
        self.password = password
        self.cookies = cookies
        self.language = language
        self.lang_url = _get_lang_url(urls, language)
        self.urls = urls
        self.univer = univer
        self.storage = _teachers if storage is None else storage

        self.logger = self.get_logger(__name__)

    def get_logger(self, name):
        logger = create_logger(
            name,
            format=f"[%(asctime)s] %(name)s | {self.univer} | {self.username} ({self.language}) - %(message)s",
        )
        return logger

    async def login(self):
        self.cookies = await login(
            self.username,
            self.password,
            login_url=self.urls.LOGIN_URL,
            get_logger=self.get_logger,
        )
        return self.cookies

    @auth
    async def get_attendance(self):
        return await get_attendance(
            self.cookies,
            attendance_url=self.urls.ATTENDANCE_URL,
            lang_url=self.lang_url,
            get_logger=self.get_logger,
        )

    @auth
    async def get_attestation(self):
        lang_urls = [
            self.urls.LANG_RU_URL,
            self.urls.LANG_EN_URL,
            self.urls.LANG_KK_URL,
        ]
        return await get_attestation(
            self.cookies,
            get_logger=self.get_logger,
            attendance_url=self.urls.ATTENDANCE_URL,
            attestation_url=self.urls.ATTESTATION_URL,
            lang_url=self.lang_url,
            lang_urls=lang_urls,
        )

    @auth
    async def get_schedule(self, factor=None):
        schedule = await get_schedule(
            self.cookies,
            self.urls.SCHEDULE_URL,
            get_logger=self.get_logger,
            lang_url=self.lang_url,
            factor=factor,
        )
        if await self.get_teacher() is NotImplemented:
            return schedule

        async def set_teacher(lesson):
            teacher = await self.__get_teacher(lesson.teacher)
            fullname, href = teacher
            lesson.teacher = fullname
            lesson.teacher_link = href

        await asyncio.gather(*(set_teacher(lesson) for lesson in schedule.lessons))
        return schedule

    @auth
    async def get_exams(self):
        exams = await get_exams(
            self.cookies,
            self.urls.EXAMS_URL,
            lang_url=self.lang_url,
            get_logger=self.get_logger,
        )
        if await self.get_teacher() is NotImplemented:
            return exams

        async def set_teacher(exam):
            teacher = await self.__get_teacher(exam.teacher)
            fullname, href = teacher
            exam.teacher = fullname
            exam.teacher_link = href

        await asyncio.gather(*(set_teacher(exam) for exam in exams))
        return exams

    async def __get_teacher(self, name: str):
        teacher_id = f"teacher-{self.univer}-{name}"
        while teacher_id in _working_teachers:
            await asyncio.sleep(1)

        if teacher_id in self.storage:
            return self.storage[teacher_id]

        _working_teachers.add(teacher_id)
        self.logger.info(f"get PERSON_URL {name}")
        try:
            teacher = await self.get_teacher(name)
            self.logger.info(f"got PERSON_URL {name}")
            self.storage[teacher_id] = teacher
            return teacher
        except:
            self.logger.info(f"error PERSON_URL {name}")
            return name, None
        finally:
            _working_teachers.remove(teacher_id)

    async def get_teacher(self, name: str = None) -> tuple[str, str]:
        return NotImplemented
