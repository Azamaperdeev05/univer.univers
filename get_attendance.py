from dataclasses import dataclass
from bs4 import BeautifulSoup

from .utils import fetch
from .urls import ATTENDANCE_URL
from .exceptions import ForbiddenException
from .logger import getDefaultLogger
from .types import Mark


@dataclass
class Attendance:
    subject: str
    summary: list[Mark]


def get_subject(line: str):
    index = line.index("(")
    return line[:index].strip()


def get_summary(line: str):
    def summary(line: str):
        line = line.replace("\xa0\xa0\xa0\xa0", "").strip()
        title, value = line.split(":")
        return Mark(get_subject(title.strip()), int(value.strip()))

    lines = line.split("\n")
    return [summary(s) for s in filter(lambda l: l.strip(), lines)]


async def get_attendance(cookies, getLogger=getDefaultLogger):
    logger = getLogger(__name__)
    logger.info("get ATTENDANCE_URL")
    html = await fetch(ATTENDANCE_URL, cookies)
    soup = BeautifulSoup(html, "html.parser")
    attendance_table = soup.select("#tools + table + table > tr")
    if len(attendance_table) < 1:
        attendance_table = soup.select("#tools + table + table > tbody > tr")
    if len(attendance_table) < 1:
        raise ForbiddenException
    prev = None
    attendances: list[Attendance] = []
    for tr in attendance_table:
        c, *_ = tr.attrs.get("class")
        if prev is None:
            prev = tr
            continue
        if c in ["top", "bot"]:
            if len(attendances) > 0:
                attendances[-1].summary = get_summary(prev.text)
        if c == "top":
            subject = get_subject(tr.text)
            attendances.append(Attendance(subject, []))
        prev = tr
    return attendances
