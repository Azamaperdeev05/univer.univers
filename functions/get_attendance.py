from dataclasses import dataclass
from pprint import pprint
from bs4 import BeautifulSoup, Tag
import re

from ..utils.fetch import fetch
from ..utils.auth import check_auth
from ..urls import ATTENDANCE_URL
from ..utils.logger import getDefaultLogger
from ..utils.text import text
from ..type import Mark


@dataclass
class Part:
    part: str
    type: str
    marks: list[Mark]


@dataclass
class Attendance:
    subject: str
    summary: list[Mark]
    attendance: list[Part]


def get_subject(line: str):
    index = line.index("(")
    return re.sub(" +", " ", line[:index].strip())


def parse_table(table: Tag):
    headings = table.select("th")
    values = table.select("td")
    marks: list[Mark] = []
    for heading, value in zip(headings[1:], values[:-1]):
        v = text(value)
        if v:
            marks.append(
                Mark(title=text(heading), value=int(v) if not v.isalpha() else v)
            )
    return text(headings[0]), marks


def get_summary(line: str):
    def summary(line: str):
        line = line.replace("\xa0\xa0\xa0\xa0", "").strip()
        title, value = line.split(":")
        return Mark(get_subject(title.strip()), int(value.strip()))

    lines = line.split("\n")
    return [summary(s) for s in filter(lambda l: l.strip(), lines)]


async def get_attendance(
    cookies, getLogger=getDefaultLogger, attendance_url=ATTENDANCE_URL
):
    logger = getLogger(__name__)
    logger.info("get ATTENDANCE_URL")
    html = await fetch(attendance_url, cookies)
    logger.info("got ATTENDANCE_URL")
    soup = BeautifulSoup(html, "html.parser")
    check_auth(soup)
    attendance_table = soup.select("#tools + table + table > tr")[1:]
    attendances: list[Attendance] = []
    if len(attendance_table) < 1:
        return attendances

    ignore = True

    attendance = Attendance(None, None, [])
    part = Part(None, None, [])
    for index, row in enumerate(attendance_table):
        c, *_ = row.attrs.get("class")
        if c == "top":
            ignore = False
        if ignore:
            continue

        if c == "top":
            attendance.subject = get_subject(row.text)
            continue

        button = row.select_one("a")
        if button is not None:
            part.type = get_subject(button.text)
            continue
        table = row.select_one("table")
        if table is not None:
            part.part, part.marks = parse_table(table)
            if part.type is None:
                part.type = attendance.attendance[-1].type
            attendance.attendance.append(part)
            part = Part(None, None, [])
            continue

        next = attendance_table[(index + 1) % len(attendance_table)]
        if next.attrs.get("class")[0] in ["top", "bot"]:
            summary = get_summary(text(row))
            attendance.summary = summary
            attendances.append(attendance)
            part = Part(None, None, [])
            attendance = Attendance(None, None, [])
    return attendances
