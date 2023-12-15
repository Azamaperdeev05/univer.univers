from dataclasses import dataclass
import asyncio
from bs4 import BeautifulSoup

from ..utils.fetch import fetch
from ..type import Mark
from ..urls import ATTESTATION_URL
from ..exceptions import ForbiddenException
from ..utils.logger import getDefaultLogger
from .get_attendance import get_attendance


@dataclass
class Attestation:
    subject: str
    attestation: list[Mark]


async def _get_attestation(cookies, getLogger=getDefaultLogger):
    logger = getLogger(__name__)
    logger.info("get ATTESTATION_URL")
    html = await fetch(ATTESTATION_URL, cookies)
    logger.info("got ATTESTATION_URL")
    soup = BeautifulSoup(html, "html.parser")
    attendance_table = soup.select("#tools + table + table .mid table.inner > tr")[:-1]
    if len(attendance_table) < 1:
        raise ForbiddenException

    _, _, *header_marks, _, _, _, _ = map(
        lambda td: td.text, attendance_table[0].select("th")
    )
    attestation: list[Attestation] = []
    for row in attendance_table[1:]:
        subject, _, *marks, _, _, _, _ = map(lambda td: td.text, row.select("td"))
        marks_list: list[Mark] = []
        for i, mark in enumerate(marks):
            marks_list.append(
                Mark(title=header_marks[i].replace("*", ""), value=int(mark))
            )
        attestation.append(Attestation(subject=subject.strip(), attestation=marks_list))

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
            result_mark.active = True
            is_active_setted = tuple
        result.append(result_mark)
    return result


async def get_attestation(cookies, getLogger=getDefaultLogger):
    attestations, attendances = await asyncio.gather(
        _get_attestation(cookies, getLogger), get_attendance(cookies, getLogger)
    )
    for attendance in attendances:
        attestation: Attestation = _find_element_by_key(
            attestations, lambda a: a.subject == attendance.subject
        )
        if attestation is None:
            continue
        attestation.attestation = _join_marks(
            attestation.attestation, attendance.summary
        )

    return attestations
