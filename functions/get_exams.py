from pprint import pprint
from bs4 import BeautifulSoup
from ..utils.logger import getDefaultLogger
from ..utils.fetch import fetch
from ..urls import EXAMS_URL
from ..exceptions import ForbiddenException

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Exam:
    subject: str
    teacher: str
    audience: str
    date: int


def text(element):
    return element.text.strip()


async def get_exams(cookies, getLogger=getDefaultLogger):
    logger = getLogger(__name__)
    logger.info("get EXAMS_URL")
    html = await fetch(EXAMS_URL, cookies)
    logger.info("got EXAMS_URL")

    soup = BeautifulSoup(html, "html.parser")
    exams_table = soup.select("#scheduleList tr[id]")

    exams: list[Exam] = []

    for row in exams_table:
        date, time = row["id"].split(" ")
        hour, minute, *_ = map(int, time.split(":"))
        day, month, year = map(int, date.split("."))
        _date = datetime(year, month, day, hour, minute)

        subject, teacher, _, audience, *_ = row.select("td")

        exams.append(
            Exam(
                subject=text(subject),
                teacher=text(teacher),
                audience=text(audience).split(":")[-1].strip(),
                date=int(_date.timestamp()),
            )
        )

    exams.sort(key=lambda e: e.date)
    if len(exams) < 1:
        raise ForbiddenException
    return exams
