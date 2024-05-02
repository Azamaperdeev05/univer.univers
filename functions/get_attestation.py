from dataclasses import dataclass
from bs4 import BeautifulSoup

from ..utils.fetch import fetch
from ..utils.auth import check_auth
from ..utils.text import text
from ..type import Mark
from ..utils.logger import get_default_logger
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
    sum: Mark


async def get_attestation(
    cookies: UserCookies,
    attestation_url: str,
    lang_url: str,
    logger=get_default_logger(__name__),
):
    """ Текущая аттестация """
    logger.info("get ATTESTATION_URL")
    html = await fetch(lang_url, cookies.as_dict(), {"referer": attestation_url})
    logger.info("got ATTESTATION_URL")
    soup = BeautifulSoup(html, "html.parser")
    check_auth(soup)

    table = soup.select("#tools + table + table .mid table.inner > tr")
    attestation: list[Attestation] = []
    if len(table) < 1:
        return attestation

    _, _, *header_marks, sum_header, _, _, _ = map(text, table[0].select("th"))
    for row in table[1:-1]:
        subject, _, *marks, sum, _, _, _ = map(text, row.select("td"))
        marks_list: list[Mark] = []
        for i, mark in enumerate(marks):
            marks_list.append(
                Mark(title=header_marks[i].replace("*", ""), value=int(mark))
            )
        attestation.append(
            Attestation(subject=subject.strip(), attestation=marks_list, attendance=[], sum=Mark(
                title=sum_header,
                value=int(sum)
            ))
        )
    return attestation
