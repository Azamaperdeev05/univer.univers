from dataclasses import dataclass
from bs4 import BeautifulSoup, Tag
from typing import Iterable
import re

from ..utils.fetch import fetch
from ..utils.auth import check_auth
from ..utils.logger import get_default_logger
from ..utils.text import text
from ..type import Mark
from .login import UserCookies


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
    if len(headings) == 0:
        return None
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


def capitalize(text: str):
    return text[0].upper() + text[1:]


async def _get_subject(cookies: UserCookies, umkd_url: str, lang_url: str):
    html = await fetch(lang_url, cookies.as_dict(), {"referer": umkd_url})
    soup = BeautifulSoup(html, "html.parser")
    check_auth(soup)
    for row in soup.select(".link[id]"):
        _, title, *_ = row.select("td")
        yield text(title)


async def _get_subjects(
    cookies: UserCookies,
    umkd_url: str,
    lang_urls: Iterable[str],
    logger=get_default_logger(__name__),
):
    result: dict[str, list[str]] = {}
    for i, lang_url in enumerate(lang_urls):
        async for subject in _get_subject(cookies, umkd_url, lang_url):
            if lang_url not in result:
                result[lang_url] = []
            result[lang_url].append(subject)
        logger.info(f"got UMKD_URL {i+1}/{len(lang_urls)}")
    return result


async def get_attendance(
    cookies: UserCookies,
    attendance_url: str,
    lang_url: str,
    logger=get_default_logger(__name__),
    umkd_url: str = None,
    lang_urls: Iterable[str] = None,
):
    logger.info("get ATTENDANCE_URL")
    html = await fetch(lang_url, cookies.as_dict(), {"referer": attendance_url})
    logger.info("got ATTENDANCE_URL")
    soup = BeautifulSoup(html, "html.parser")
    check_auth(soup)
    attendance_table = soup.select("#tools + table + table tr")[1:]
    attendances: list[Attendance] = []
    if len(attendance_table) < 1:
        return attendances

    ignore = True

    attendance = Attendance(None, None, [])
    part = Part(None, None, [])
    for index, row in enumerate(attendance_table):
        c, *_ = row.attrs.get("class", ["mid"])
        if c == "top":
            ignore = False
        if ignore:
            continue

        if c == "top":
            attendance.subject = get_subject(row.text)
            continue

        button = row.select_one("a")
        if button is not None:
            part.type = capitalize(get_subject(button.text))
            continue
        table = row.select_one("table")
        if table is not None:
            marks = parse_table(table)
            if marks is None:
                continue
            part.part, part.marks = marks
            if part.type is None:
                part.type = attendance.attendance[-1].type
            attendance.attendance.append(part)
            part = Part(None, None, [])
            continue

        next = attendance_table[(index + 1) % len(attendance_table)]
        if next.attrs.get("class", ["mid"])[0] in ["top", "bot"]:
            summary = get_summary(text(row))
            attendance.summary = summary
            attendances.append(attendance)
            part = Part(None, None, [])
            attendance = Attendance(None, None, [])

    all_subjects = await _get_subjects(cookies, umkd_url, lang_urls)

    for a in attendances:
        for subjects in all_subjects.values():
            if a.subject in subjects:
                a.subject = all_subjects[lang_url][subjects.index(a.subject)]
                break

    return attendances
