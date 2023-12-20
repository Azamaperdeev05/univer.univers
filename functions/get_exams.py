from bs4 import BeautifulSoup

from ..utils.auth import check_auth
from ..utils.logger import getDefaultLogger
from ..utils.fetch import fetch
from ..utils.text import text
from ..urls import EXAMS_URL, LANG_RU_URL

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Exam:
    subject: str
    teacher: str
    audience: str
    date: int


def __get_date(text: str):
    datestring = text.strip().split("\n")[0].strip()
    date, time = datestring.split(" ")
    hour, minute, *_ = map(int, time.split(":"))
    for symbol in "-/.":
        if symbol in date:
            separator = symbol
            break
    day, month, year = map(int, date.split(separator))
    return int(datetime(year, month, day, hour - 6, minute).timestamp())


async def get_exams(
    cookies, getLogger=getDefaultLogger, exams_url=EXAMS_URL, lang_url=LANG_RU_URL
):
    logger = getLogger(__name__)
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
            )
        )

    exams.sort(key=lambda e: e.date)
    return exams
