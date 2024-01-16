from bs4 import BeautifulSoup, Tag
from dataclasses import dataclass, field
from datetime import datetime

from ..utils.auth import check_auth
from ..utils.logger import get_default_logger
from ..utils.fetch import fetch
from ..utils.text import text


@dataclass
class UmkdFolder:
    subject: str
    id: int
    type: str


@dataclass
class UmkdFile:
    name: str
    description: str
    type: str
    language: str | None
    size: str
    date: int
    downloads_count: int
    teacher: str
    url: str
    teacher_link: str = field(default=None)


async def get_umkd(
    cookies, umkd_url: str, lang_url: str, logger=get_default_logger(__name__)
) -> list[UmkdFolder]:
    logger.info("get UMKD_URL")
    html = await fetch(lang_url, cookies, {"referer": umkd_url})
    logger.info("got UMKD_URL")

    soup = BeautifulSoup(html, "html.parser")
    check_auth(soup)

    result: list[UmkdFolder] = []
    for link in soup.select(".link[id]"):
        _, subject, type = link.select("td")
        result.append(UmkdFolder(type=text(type), id=link["id"], subject=text(subject)))

    return sorted(result, key=lambda f: f.id)


def parse_links(row: Tag, teacher: str):
    for link in row.select(".file[id]"):
        (
            icon,
            name,
            description,
            type,
            language,
            size,
            date,
            downloads_count,
            *_,
        ) = link.select("td")

        url = name.select_one("a").get("href")
        day, month, year = map(int, text(date).split("."))
        language_text = text(language)
        yield UmkdFile(
            name=text(name),
            description=text(description),
            type=text(type),
            language=language_text if language_text != "-" else None,
            downloads_count=int(text(downloads_count)),
            date=int(datetime(year, month, day).timestamp()),
            size=text(size),
            teacher=teacher,
            url=url,
        )


async def get_umkd_files(
    cookies,
    umkd_url: str,
    subject_id: str,
    lang_url: str,
    logger=get_default_logger(__name__),
):
    logger.info(f"get UMKD_URL_FILES {subject_id}")
    html = await fetch(lang_url, cookies, {"referer": f"{umkd_url}/{subject_id}"})
    logger.info(f"got UMKD_URL_FILES {subject_id}")

    soup = BeautifulSoup(html, "html.parser")
    check_auth(soup)

    result: list[UmkdFile] = []

    teacher = None
    for row in soup.select_one(".brk").parent.children:
        if not isinstance(row, Tag):
            continue

        class_ = "".join(row["class"])
        if class_ == "brk":
            t = text(row)
            teacher = t[t.find(":") + 1 :].strip()
            continue
        if teacher is None:
            continue
        if class_ == "mid":
            result.extend(parse_links(row, teacher))
            teacher = None
    return sorted(result, key=lambda f: f.date, reverse=True)
