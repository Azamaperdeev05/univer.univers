from bs4 import BeautifulSoup, Tag
from typing import Iterable
from ..utils.logger import get_default_logger
from ..utils.fetch import fetch
from ..utils.auth import check_auth

from dataclasses import dataclass


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
    factor: bool | None


def text(element):
    if element:
        return element.text.strip()


def get_lessons(row: Tag):
    time = text(row.select_one(".time"))
    days = row.select("td.field")
    for day, field in enumerate(days):
        lessons = field.select("div[style]")
        if len(lessons) == 0:
            continue

        for lesson in lessons:
            subject_element = lesson.select_one("p")
            audience = text(lesson.select_one(".aud_faculty").next_sibling)
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
                audience=audience,
                period=text(lesson.select_one(".dateStartLbl")),
            )


async def get_schedule(
    cookies,
    schedule_url: str,
    lang_url: str,
    factor: bool | None = None,
    get_logger=get_default_logger,
):
    logger = get_logger(__name__)
    logger.info("get SCHEDULE_URL")
    html = await fetch(lang_url, cookies, {"referer": schedule_url})
    logger.info("got SCHEDULE_URL")

    soup = BeautifulSoup(html, "html.parser")
    check_auth(soup)
    schedule_table = soup.select(".schedule tr")[1:]
    lessons = []
    for row in schedule_table:
        lessons += list(get_lessons(row))

    return Schedule(lessons=lessons, factor=factor)
