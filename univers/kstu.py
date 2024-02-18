from bs4 import BeautifulSoup
from dataclasses import replace
from datetime import date

from ..utils.fetch import fetch
from ..utils import compare_str_without_spaces, to_initials
from .base import Univer, Urls


def _get_factor():
    FIRST_WEEK = "2024-01-15"
    year, month, day = map(int, FIRST_WEEK.split("-"))
    first = date(year, month, day)
    now = date.today()
    weekday = 1 if now.weekday() > 4 else 0
    week = (now - first).days // 7 + 1 + weekday
    return week % 2 == 0


KSTUUrls = Urls(
    ATTENDANCE_URL="https://univer.kstu.kz/student/attendance/full/",
    LOGIN_URL="https://univerapi.kstu.kz/",
    LANG_RU_URL="https://univer.kstu.kz/lang/change/ru/",
    LANG_KK_URL="https://univer.kstu.kz/lang/change/kz/",
    LANG_EN_URL="https://univer.kstu.kz/lang/change/en/",
    ATTESTATION_URL="https://univer.kstu.kz/student/attestation/",
    SCHEDULE_URL=(
        "https://univer.kstu.kz/student/myschedule/2023/2/22.01.2024/28.01.2024/"
    ),
    EXAMS_URL="https://univer.kstu.kz/student/myexam/schedule/",
    TRANSCRIPT_URL_RU="https://univer.kstu.kz/student/transcript/2",
    TRANSCRIPT_URL_KK="https://univer.kstu.kz/student/transcript/1/",
    TRANSCRIPT_URL_EN="https://univer.kstu.kz/student/transcript/6/",
    UMKD_URL="https://univer.kstu.kz/student/umkd/",
)
PERSON_URL = "https://person.kstu.kz/?s={}"


class KSTU(Univer):
    def __init__(
        self,
        cookies: dict[str, str] = None,
        language="ru",
        storage=None,
    ) -> None:
        super().__init__(
            urls=KSTUUrls,
            cookies=cookies,
            language=language,
            univer="kstu",
            storage=storage,
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

        schedule.lessons = lessons
        return schedule

    async def get_teacher(self, name: str = None):
        if name is None:
            return name, None
        firstname, *_ = name.split(" ")
        html = await fetch(PERSON_URL.format(firstname))
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
