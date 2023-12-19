from dataclasses import dataclass
import asyncio
from bs4 import BeautifulSoup

from ..utils.fetch import fetch
from ..utils.auth import check_auth
from ..type import Mark, ActiveMark
from ..urls import ATTESTATION_URL, ATTENDANCE_URL, LANG_RU_URL
from ..utils.logger import getDefaultLogger
from .get_attendance import get_attendance


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
    cookies,
    getLogger=getDefaultLogger,
    attestation_url=ATTESTATION_URL,
    lang_url=LANG_RU_URL,
):
    logger = getLogger(__name__)
    logger.info("get ATTESTATION_URL")
    html = await fetch(lang_url, cookies, {"referer": attestation_url})
    logger.info("got ATTESTATION_URL")
    soup = BeautifulSoup(html, "html.parser")
    check_auth(soup)

    attendance_table = soup.select("#tools + table + table .mid table.inner > tr")[:-1]
    attestation: list[Attestation] = []
    if len(attendance_table) < 1:
        return attestation

    _, _, *header_marks, _, _, _, _ = map(
        lambda td: td.text, attendance_table[0].select("th")
    )
    for row in attendance_table[1:]:
        subject, _, *marks, _, _, _, _ = map(lambda td: td.text, row.select("td"))
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

    is_active_setted = False
    for a_mark in a:
        b_mark = _find_element_by_key(b, lambda b_mark: a_mark.title == b_mark.title)
        result_mark = b_mark or a_mark
        if not is_active_setted and a_mark.value == 0:
            result_mark = ActiveMark(title=result_mark.title, value=result_mark.value)
            is_active_setted = tuple
        result.append(result_mark)
    return result


async def get_attestation(
    cookies,
    getLogger=getDefaultLogger,
    attestation_url=ATTESTATION_URL,
    attendance_url=ATTENDANCE_URL,
    lang_url=LANG_RU_URL,
):
    attestations, attendances = await asyncio.gather(
        _get_attestation(cookies, getLogger, attestation_url, lang_url=lang_url),
        get_attendance(cookies, getLogger, attendance_url, lang_url=lang_url),
    )
    for index, attendance in enumerate(attendances):
        attestation: Attestation = attestations[index]
        attestation.attestation = _join_marks(
            attestation.attestation, attendance.summary
        )
        attestation.attendance = attendance.attendance

    return attestations
