from dataclasses import dataclass
import asyncio
from typing import Iterable
from bs4 import BeautifulSoup

from ..utils.fetch import fetch
from ..utils.auth import check_auth
from ..utils.text import text
from ..type import Mark, ActiveMark
from ..utils.logger import get_default_logger
from .get_attendance import get_attendance, Attendance as _Attendance
from .login import UserCookies


@dataclass
class Attendance:
    part: str
    type: str
    marks: list[Mark]


@dataclass
class Attestation:
    subject: str
    attestation: list[Mark]
    attendance: list[Attendance]


async def _get_attestation(
    cookies: UserCookies,
    attestation_url: str,
    lang_url: str,
    logger=get_default_logger(__name__),
):
    logger.info("get ATTESTATION_URL")
    html = await fetch(lang_url, cookies.as_dict(), {"referer": attestation_url})
    logger.info("got ATTESTATION_URL")
    soup = BeautifulSoup(html, "html.parser")
    check_auth(soup)

    table = soup.select("#tools + table + table .mid table.inner > tr")
    attestation: list[Attestation] = []
    if len(table) < 1:
        return attestation

    _, _, *header_marks, _, _, _, _ = map(text, table[0].select("th"))
    for row in table[1:-1]:
        subject, _, *marks, _, _, _, _ = map(text, row.select("td"))
        marks_list: list[Mark] = []
        for i, mark in enumerate(marks):
            marks_list.append(
                Mark(title=header_marks[i].replace("*", ""), value=int(mark))
            )
        attestation.append(
            Attestation(subject=subject.strip(), attestation=marks_list, attendance=[])
        )
    return attestation


def _find_element_by_key(elements: list, predicate):
    for element in elements:
        if predicate(element):
            return element


def _join_marks(a: list[Mark], b: list[Mark]) -> list[Mark]:
    result: list[Mark] = []
    is_active_set = False
    for a_mark in a:
        b_mark = _find_element_by_key(b, lambda b_mark: a_mark.title == b_mark.title)
        result_mark = b_mark or a_mark
        if not is_active_set and a_mark.value == 0:
            result_mark = ActiveMark(title=result_mark.title, value=result_mark.value)
            is_active_set = tuple
        result.append(result_mark)
    return result


async def _get_attestation_subject(
    cookies: UserCookies, attestation_url: str, lang_url: str
):
    html = await fetch(lang_url, cookies.as_dict(), {"referer": attestation_url})
    soup = BeautifulSoup(html, "html.parser")
    check_auth(soup)
    table = soup.select("#tools + table + table .mid table.inner > tr")
    for row in table[1:-1]:
        yield text(row.select_one("td"))


async def _get_attestation_subjects(
    cookies: UserCookies,
    attestation_url: str,
    lang_urls: Iterable[str],
    logger=get_default_logger(__name__),
):
    result = []
    for i, lang_url in enumerate(lang_urls):
        index = 0
        async for subject in _get_attestation_subject(
            cookies, attestation_url, lang_url
        ):
            while len(result) <= index:
                result.append([])
            result[index].append(subject)
            index += 1
        logger.info(f"got ATTESTATION_URL {i+1}/{len(lang_urls)}")
    return result


def _get_attestation_by_subject(
    attestations: list[Attestation], subject: str, subjects: list[str]
) -> Attestation:
    if len(subjects) < 1:
        return None
    for current_subject in subjects:
        if subject in current_subject:
            break
    for attestation in attestations:
        if attestation.subject in current_subject:
            return attestation
    return None


def _join(
    attestations: list[Attestation], attendances: list[_Attendance], subjects: list[str]
):
    no_attestation = len(attestations) < 1
    for attendance in attendances:
        attestation = _get_attestation_by_subject(
            attestations, attendance.subject, subjects
        )
        if no_attestation:
            new_attestation = [Mark(title, 0) for title, _ in attendance.summary]
            attestation = Attestation(
                subject=attendance.subject,
                attestation=new_attestation + [Mark(title="", value=0)],
                attendance=[],
            )
            attestations.append(attestation)
        if attestation is None:
            continue
        attestation.attestation = _join_marks(
            attestation.attestation, attendance.summary
        )
        attestation.attendance = attendance.attendance
    return attestations


async def get_attestation(
    cookies: UserCookies,
    attestation_url: str,
    attendance_url: str,
    lang_url: str,
    lang_urls: Iterable[str],
    logger=get_default_logger(__name__),
):
    attestations, attendances = await asyncio.gather(
        _get_attestation(cookies, attestation_url, lang_url=lang_url, logger=logger),
        get_attendance(cookies, attendance_url, lang_url=lang_url, logger=logger),
    )
    subjects = await _get_attestation_subjects(
        cookies, attestation_url, lang_urls, logger=logger
    )
    return sorted(_join(attestations, attendances, subjects), key=lambda a: a.subject)
