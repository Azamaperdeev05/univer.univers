from bs4 import BeautifulSoup
from ..utils.logger import getDefaultLogger
from ..utils.fetch import fetch
from ..urls import SCHEDULE_URL
from ..utils.auth import check_auth

from dataclasses import dataclass
from datetime import date


def __get_factor():
    FIRST_WEEK = "2023-09-04"
    year, month, day = map(int, FIRST_WEEK.split("-"))
    first = date(year, month, day)
    now = date.today()
    weekday = 1 if now.weekday() > 4 else 0
    week = (now - first).days // 7 + 1 + weekday
    return week % 2 == 0


@dataclass
class Lesson:
    subject: str
    teacher: str
    audience: str
    period: str
    day: int
    time: str
    factor: bool


@dataclass
class Schedule:
    lessons: list[Lesson]
    factor: bool


def text(element):
    if element:
        return element.text.strip()


async def get_schedule(cookies, getLogger=getDefaultLogger, schedule_url=SCHEDULE_URL):
    logger = getLogger(__name__)
    logger.info("get SCHEDULE_URL")
    html = await fetch(schedule_url, cookies)
    logger.info("got SCHEDULE_URL")

    soup = BeautifulSoup(html, "html.parser")
    check_auth(soup)
    schedule_table = soup.select(".schedule tr")[1:]

    lessons_list: list[Lesson] = []
    for row in schedule_table:
        time = text(row.select_one(".time"))
        days = row.select("td.field")
        for day, field in enumerate(days):
            lessons = field.select("div[style]")
            if len(lessons) == 0:
                continue

            for lesson in lessons:
                subject_element = lesson.select_one("p")

                def get_lesson(factor: bool):
                    audience = text(lesson.select_one(".aud_faculty").next_sibling)
                    return Lesson(
                        subject=text(subject_element)
                        .replace("(", " (")
                        .replace("  (", " ("),
                        day=day,
                        time=time,
                        factor=factor,
                        teacher=text(subject_element.next_sibling),
                        audience=audience,
                        period=text(lesson.select_one(".dateStartLbl")),
                    )

                denominator = lesson.select_one(".denominator")
                if denominator is None:
                    lessons_list.append(get_lesson(True))
                    lessons_list.append(get_lesson(False))
                    continue

                factor = text(denominator).lower() != "числитель"
                lessons_list.append(get_lesson(factor))

    return Schedule(lessons=lessons_list, factor=__get_factor())
