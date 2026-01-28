from pprint import pprint
import re
from bs4 import BeautifulSoup, Tag

from utils.logger import get_default_logger
from utils.fetch import fetch
from utils.auth import check_auth
from utils.text import text

from dataclasses import dataclass
from functions.login import UserCookies


@dataclass
class Transcript:
    fullname: str
    faculty: str
    level_of_the_qualification: str
    level_of_education: str
    education_program: str
    education_program_group: str
    language: str
    year_of_study: int
    length_of_program: float
    graid_point: float
    avarage_point: float
    form_of_study: str


def remove_spaces(text: str):
    return re.sub(r"\s+", " ", re.sub(r"\s", " ", text)).strip()


def _get_even_cell_text(row: Tag):
    for cell in row.select("td")[1::2]:
        yield remove_spaces(text(cell))


def parse_float(text: str):
    return float(text.replace(",", "."))


async def get_transcript(
    cookies: UserCookies, transcript_url: str, logger=get_default_logger(__name__)
):
    logger.info("get TRANSCRIPT_URL")
    html = await fetch(transcript_url, cookies.as_dict())
    logger.info("got TRANSCRIPT_URL")

    soup = BeautifulSoup(html, "html.parser")
    check_auth(soup)

    table = soup.select_one("td table")

    transcript = Transcript(
        fullname="",
        avarage_point=0,
        education_program="",
        education_program_group="",
        faculty="",
        graid_point=0,
        language="",
        length_of_program=0,
        level_of_the_qualification=0,
        year_of_study=0,
        form_of_study="",
        level_of_education="",
    )

    for index, row in enumerate(table.select("tr")):
        cells = _get_even_cell_text(row)
        if index == 0:
            transcript.fullname = next(cells)
        elif index == 1:
            transcript.faculty = next(cells)
            transcript.level_of_the_qualification = next(cells)
        elif index == 2:
            transcript.education_program_group = next(cells)
        elif index == 3:
            transcript.education_program = next(cells)
            transcript.form_of_study = next(cells)
        elif index == 4:
            transcript.year_of_study = int(next(cells))
            transcript.level_of_education = next(cells)
        elif index == 5:
            transcript.language = next(cells)
            transcript.length_of_program = float(next(cells).replace(",", "."))

    spaces = 0

    rows = soup.select(".noprint + table > tr")
    for index, child in enumerate(rows):
        content = remove_spaces(text(child))

        if len(content) == 0:
            spaces += 1
            continue
        if spaces <= 0:
            continue
        *_, value = content.split(" ")
        transcript.graid_point = parse_float(value)
        *_, next_value = remove_spaces(text(rows[index + 1])).split(" ")
        transcript.avarage_point = parse_float(next_value)
        break
    return transcript
