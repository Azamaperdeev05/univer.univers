import asyncio
from bs4 import BeautifulSoup
from dataclasses import replace
from datetime import date
from logging import Logger

from ..functions.get_schedule import Lesson
from .base import Univer, Urls
from ..utils.fetch import fetch
from ..utils import compare_str_without_spaces, to_initials


def _get_factor():
    FIRST_WEEK = "2023-09-04"
    year, month, day = map(int, FIRST_WEEK.split("-"))
    first = date(year, month, day)
    now = date.today()
    weekday = 1 if now.weekday() > 4 else 0
    week = (now - first).days // 7 + 1 + weekday
    return week % 2 == 0


KSTUUrls = Urls(
    ATTENDANCE_URL="http://univer.kstu.kz/student/attendance/full/",
    LOGIN_URL="http://univer.kstu.kz/user/login",
    LANG_RU_URL="http://univer.kstu.kz/lang/change/ru/",
    LANG_KK_URL="http://univer.kstu.kz/lang/change/kz/",
    LANG_EN_URL="http://univer.kstu.kz/lang/change/en/",
    ATTESTATION_URL="http://univer.kstu.kz/student/attestation/",
    SCHEDULE_URL=(
        "http://univer.kstu.kz/student/myschedule/2023/2/22.01.2024/28.01.2024/"
    ),
    EXAMS_URL="http://univer.kstu.kz/student/myexam/schedule/",
)
PERSON_URL = "https://person.kstu.kz/?s={}"


async def get_teacher(name: str, logger: Logger):
    firstname, *_ = name.split(" ")
    logger.info(f"get PERSON_URL {firstname}")
    try:
        html = await fetch(PERSON_URL.format(firstname))
    except:
        logger.info(f"error PERSON_URL {firstname}")
        return name, None
    logger.info(f"got PERSON_URL {firstname}")

    soup = BeautifulSoup(html, "html.parser")
    for article in soup.select("article[id]"):
        anchor = article.select_one("h1 a")
        if anchor is None:
            continue
        fullname = anchor.text.strip()
        href = anchor["href"]
        if not compare_str_without_spaces(name, to_initials(fullname)):
            continue
        return fullname, href

    return name, None


teachers = {}


class KSTU(Univer):
    def __init__(
        self,
        username: str,
        password: str,
        cookies: dict[str, str] = None,
        language="ru",
    ) -> None:
        super().__init__(
            username,
            password,
            urls=KSTUUrls,
            cookies=cookies,
            language=language,
            univer="kstu",
        )

    async def get_schedule(self):
        schedule = await super().get_schedule(_get_factor())
        lessons = []
        for lesson in schedule.lessons:
            if lesson.factor is None:
                lessons.append(replace(lesson, factor=True))
                lessons.append(replace(lesson, factor=False))
                continue
            lessons.append(lesson)

        async def set_teacher(lesson: Lesson):
            teacher = lesson.teacher
            if teacher not in teachers:
                teachers[teacher] = None, None
                link = await get_teacher(teacher, self.logger)
                teachers[teacher] = link
            while teachers[teacher][0] is None:
                await asyncio.sleep(1)
            fullname, href = teachers[teacher]
            lesson.teacher = fullname
            lesson.teacher_link = href

        await asyncio.gather(*[set_teacher(lesson) for lesson in lessons])

        schedule.lessons = lessons
        return schedule
