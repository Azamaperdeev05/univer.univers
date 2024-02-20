import asyncio

from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlparse

from ..functions.login import login, UserCookies
from ..functions.transcript import get_transcript
from ..functions.get_attendance import get_attendance
from ..functions.get_attestation import get_attestation
from ..functions.get_schedule import get_schedule
from ..functions.get_exams import get_exams
from ..functions.get_umkd import get_umkd, get_umkd_files
from ..functions.download import download_file
from ..type import Translation
from ..utils import (
    merge_attestation_attendance,
    get_subject_translations,
    Storage,
    create_logger,
)


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
    EDUCATION_PLAN_URL: str


def _get_lang_url(urls: Urls, lang: str):
    return getattr(urls, f"LANG_{lang.upper()}_URL", urls.LANG_RU_URL)


def _get_transcript_url(urls: Urls, lang: str):
    return getattr(urls, f"TRANSCRIPT_URL_{lang.upper()}", urls.TRANSCRIPT_URL_RU)


_storage = {}
_working_teachers = set()


def SubjectId(subject: str):
    return f"subject-{subject}"


class Univer:
    def __init__(
        self,
        urls: Urls,
        cookies: UserCookies = None,
        language="ru",
        univer="",
        storage: Storage = None,
    ) -> None:
        self.language = language
        self.lang_url = _get_lang_url(urls, language)
        self.urls = urls
        self.univer = univer
        self.storage = _storage if storage is None else storage
        self.__apply_cookies(cookies)

    def __apply_cookies(self, cookies: UserCookies | None):
        self.username = "<unknown>"
        if cookies is not None:
            self.username = cookies.username
            self.cookies = cookies
        self.logger = self.get_logger(__name__)

    def get_logger(self, name):
        logger = create_logger(
            name,
            format=f"[%(asctime)s] {self.univer} | {self.username} ({self.language}) - %(message)s",
        )
        return logger

    async def get_subject_translations(
        self, subjects: Iterable[str]
    ) -> list[Translation]:
        subjects = tuple(subjects)
        if not all((SubjectId(subject) in self.storage) for subject in subjects):
            all_subjects = await get_subject_translations(
                cookies=self.cookies,
                education_plan_url=self.urls.EDUCATION_PLAN_URL,
                lang_urls=Translation(
                    ru=self.urls.LANG_RU_URL,
                    en=self.urls.LANG_EN_URL,
                    kk=self.urls.LANG_KK_URL,
                ),
                logger=self.logger,
            )
            for subject in all_subjects:
                for translation in subject:
                    self.storage[SubjectId(translation)] = subject
            return all_subjects

        return [self.storage[SubjectId(subject)] for subject in subjects]

    async def get_attendance(self):
        attendances = await get_attendance(
            self.cookies,
            attendance_url=self.urls.ATTENDANCE_URL,
            lang_url=self.lang_url,
            logger=self.logger,
        )
        all_subjects = await self.get_subject_translations(
            (a.subject for a in attendances)
        )

        for a in attendances:
            for subjects in all_subjects:
                if a.subject in subjects:
                    a.subject = str(getattr(subjects, self.language, a.subject))
                    break
        return attendances

    async def login(self, username: str, password: str):
        cookies = await login(username, password, self.urls.LOGIN_URL)
        self.__apply_cookies(cookies)
        return cookies

    async def get_attestation(self):
        attestation, attendance = await asyncio.gather(
            get_attestation(
                self.cookies,
                logger=self.logger,
                attestation_url=self.urls.ATTESTATION_URL,
                lang_url=self.lang_url,
            ),
            self.get_attendance(),
        )
        return merge_attestation_attendance(attestation, attendance)

    async def get_schedule(self):
        schedule = await get_schedule(
            self.cookies,
            self.urls.SCHEDULE_URL,
            logger=self.logger,
            lang_url=self.lang_url,
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
        path = urlparse(self.urls.EXAMS_URL).path
        base = self.urls.EXAMS_URL.replace(path, "")
        url = f"{base}{file_url}"
        async for chunk in download_file(self.cookies, url, self.logger):
            yield chunk
