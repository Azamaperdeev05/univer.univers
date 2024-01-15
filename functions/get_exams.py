from pprint import pprint
from bs4 import BeautifulSoup
from typing import Literal

from ..utils.auth import check_auth
from ..utils.logger import get_default_logger
from ..utils.fetch import fetch
from ..utils.text import text

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta


@dataclass
class Exam:
    subject: str
    teacher: str
    audience: str
    date: int
    type: Literal["consultation", "exam"]
    teacher_link: str | None = field(default=None)


tz = timezone(timedelta(hours=6))


def __get_date(text: str):
    datestring = text.strip().split("\n")[0].strip()
    date, time = datestring.split(" ")
    hour, minute, *_ = map(int, time.split(":"))
    for symbol in "-/.":
        if symbol in date:
            separator = symbol
            break
    day, month, year = map(int, date.split(separator))

    return int(datetime(year, month, day, hour, minute, tzinfo=tz).timestamp())


async def get_exams(
    cookies, exams_url: str, lang_url: str, logger=get_default_logger(__name__)
):
    logger.info("get EXAMS_URL")
    html = await fetch(lang_url, cookies, {"referer": exams_url})
    logger.info("got EXAMS_URL")

    soup = BeautifulSoup(html, "html.parser")
    check_auth(soup)
    exams_table = soup.select("#scheduleList tr")
    exams: list[Exam] = []
    if len(exams_table) < 1:
        return exams

    for index, row in enumerate(exams_table):
        if row.get("id") is None:
            continue
        prev = exams_table[max(index - 1, 0)]
        subject, teacher, _, audience, *_ = row.select("td")

        exams.append(
            Exam(
                subject=text(subject),
                teacher=text(teacher),
                audience=text(audience).split(":")[-1].strip(),
                date=__get_date(prev.text),
                type="exam",
            )
        )

    groups: dict[str, list[Exam]] = {}
    for exam in exams:
        if exam.subject not in groups:
            groups[exam.subject] = []
        groups[exam.subject].append(exam)

    for group in groups.values():
        if len(group) < 2:
            continue
        group[0].type = "consultation"

    exams.sort(key=lambda e: e.date)
    return exams
