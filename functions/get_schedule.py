from bs4 import BeautifulSoup, Tag
from dataclasses import dataclass, field
from datetime import date
from hashlib import md5

from ..utils.logger import get_default_logger
from ..utils.fetch import fetch
from ..utils.auth import check_auth
from ..utils.text import text
from .login import UserCookies


@dataclass
class Lesson:
    subject: str
    teacher: str
    audience: str
    period: str
    day: int
    time: str
    factor: bool
    teacher_link: str = field(default=None)
    id: str = field(default=None)

    def get_id(self):
        data = (
            self.subject,
            self.day,
            self.time,
            self.factor,
            self.teacher,
            self.audience,
            self.period,
            self.teacher_link,
        )
        return hash("-".join(map(str, data)))


@dataclass
class Schedule:
    lessons: list[Lesson]
    factor: bool | None
    week: int

    def with_id(self):
        for lesson in self.lessons:
            lesson.id = lesson.get_id()
        return self


def get_week():
    FIRST_WEEK = "2024-09-2"
    year, month, day = map(int, FIRST_WEEK.split("-"))
    first = date(year, month, day)
    now = date.today()
    weekday = 1 if now.weekday() > 4 else 0
    week = (now - first).days // 7 + 1 + weekday
    return week


def hash(text: str):
    return md5(text.encode()).hexdigest()


def get_lessons(row: Tag):
    time = text(row.select_one(".time"))
    days = row.select("td.field")
    for day, field in enumerate(days):
        lessons = field.select("div[style]")
        if len(lessons) == 0:
            continue

        for lesson in lessons:
            subject_element = lesson.select_one("p")
            denominator = lesson.select_one(".denominator")
            factor = (
                None
                if denominator is None
                else text(denominator).lower() != "числитель"
            )

            yield Lesson(
                subject=text(subject_element).replace("(", " (").replace("  (", " ("),
                day=day,
                time=time,
                factor=factor,
                teacher=text(subject_element.next_sibling),
                audience=text(lesson.select_one(".aud_faculty").next_sibling),
                period=text(lesson.select_one(".dateStartLbl")),
            )


async def get_schedule(
    cookies: UserCookies,
    schedule_url: str,
    lang_url: str,
    logger=get_default_logger(__name__),
):
    logger.info("get SCHEDULE_URL")
    html = await fetch(lang_url, cookies.as_dict(), {"referer": schedule_url})
    logger.info("got SCHEDULE_URL")

    soup = BeautifulSoup(html, "html.parser")
    check_auth(soup)
    schedule_table = soup.select(".schedule tr")[1:]
    lessons = []
    for row in schedule_table:
        lessons += list(get_lessons(row))
    return Schedule(lessons=lessons, factor=None, week=get_week())
