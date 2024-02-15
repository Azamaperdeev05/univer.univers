import asyncio

from dataclasses import dataclass
from urllib.parse import urlparse

from ..utils.logger import create_logger
from ..functions.login import login, UserCookies
from ..functions.transcript import get_transcript
from ..functions.get_attendance import get_attendance
from ..functions.get_attestation import get_attestation
from ..functions.get_schedule import get_schedule
from ..functions.get_exams import get_exams
from ..functions.get_umkd import get_umkd, get_umkd_files
from ..functions.download import download_file
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

    TRANSCRIPT_URL_RU: str
    TRANSCRIPT_URL_EN: str
    TRANSCRIPT_URL_KK: str
    UMKD_URL: str


def _get_lang_url(urls: Urls, lang: str):
    return getattr(urls, f"LANG_{lang.upper()}_URL", urls.LANG_RU_URL)


def _get_transcript_url(urls: Urls, lang: str):
    return getattr(urls, f"TRANSCRIPT_URL_{lang.upper()}", urls.TRANSCRIPT_URL_RU)


_teachers = {}
_working_teachers = set()


class Univer:
    def __init__(
        self,
        urls: Urls,
        cookies: UserCookies = None,
        language="ru",
        univer="",
        storage: Storage = None,
    ) -> None:
        self.__apply_cookies(cookies)
        self.language = language
        self.lang_url = _get_lang_url(urls, language)
        self.urls = urls
        self.univer = univer
        self.storage = _teachers if storage is None else storage
        self.lang_urls = [
            self.urls.LANG_RU_URL,
            self.urls.LANG_EN_URL,
            self.urls.LANG_KK_URL,
        ]

        self.logger = self.get_logger(__name__)

    def __apply_cookies(self, cookies: UserCookies | None):
        if cookies is None:
            self.username = "<unknown>"
            return
        self.cookies = cookies
        self.username = cookies.username

    def get_logger(self, name):
        logger = create_logger(
            name,
            format=f"[%(asctime)s] {self.univer} | {self.username} ({self.language}) - %(message)s",
        )
        return logger

    async def get_attendance(self):
        return await get_attendance(
            self.cookies,
            attendance_url=self.urls.ATTENDANCE_URL,
            lang_url=self.lang_url,
            logger=self.logger,
            lang_urls=self.lang_urls,
            umkd_url=self.urls.UMKD_URL,
        )

    async def login(self, username: str, password: str):
        self.cookies = await login(username, password, self.urls.LOGIN_URL)
        return self.cookies

    async def get_attestation(self):
        return await get_attestation(
            self.cookies,
            logger=self.logger,
            attendance_url=self.urls.ATTENDANCE_URL,
            attestation_url=self.urls.ATTESTATION_URL,
            lang_url=self.lang_url,
            lang_urls=self.lang_urls,
            umkd_url=self.urls.UMKD_URL,
        )

    async def get_schedule(self, factor=None):
        schedule = await get_schedule(
            self.cookies,
            self.urls.SCHEDULE_URL,
            logger=self.logger,
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

    async def get_exams(self):
        exams = await get_exams(
            self.cookies,
            self.urls.EXAMS_URL,
            lang_url=self.lang_url,
            logger=self.logger,
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

    async def get_transcript(self):
        return await get_transcript(
            self.cookies,
            transcript_url=_get_transcript_url(self.urls, self.language),
            logger=self.logger,
        )

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

    async def get_umkd(self):
        return await get_umkd(
            self.cookies,
            self.urls.UMKD_URL,
            lang_url=self.lang_url,
            logger=self.logger,
        )

    async def get_umkd_files(self, subject_id: str):
        files = await get_umkd_files(
            self.cookies,
            self.urls.UMKD_URL,
            subject_id=subject_id,
            lang_url=self.lang_url,
            logger=self.logger,
        )
        if await self.get_teacher() is NotImplemented:
            return files

        async def set_teacher(file):
            teacher = await self.__get_teacher(file.teacher)
            fullname, href = teacher
            file.teacher = fullname
            file.teacher_link = href

        await asyncio.gather(*(set_teacher(file) for file in files))
        return files

    async def download_file(self, file_url: str):
        path = urlparse(self.urls.LOGIN_URL).path
        base = self.urls.LOGIN_URL.replace(path, "")
        url = f"{base}{file_url}"
        async for chunk in download_file(self.cookies, url, self.logger):
            yield chunk
