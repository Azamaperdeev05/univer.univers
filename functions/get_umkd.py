from bs4 import BeautifulSoup, Tag
from dataclasses import dataclass, field
from datetime import datetime

from ..utils.auth import check_auth
from ..utils.logger import get_default_logger
from ..utils.fetch import fetch
from ..utils.text import text
from .login import UserCookies


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
    cookies: UserCookies,
    umkd_url: str,
    lang_url: str,
    logger=get_default_logger(__name__),
) -> list[UmkdFolder]:
    logger.info("get UMKD_URL")
    html = await fetch(lang_url, cookies.as_dict(), {"referer": umkd_url})
    logger.info("got UMKD_URL")

    soup = BeautifulSoup(html, "html.parser")
    check_auth(soup)

    result: list[UmkdFolder] = []
    for link in soup.select(".link[id]"):
        _, subject, type = link.select("td")
        result.append(UmkdFolder(type=text(type), id=link["id"], subject=text(subject)))

    return sorted(result, key=lambda f: f.id)


def parse_links(table: Tag, teacher: str):
    type = None
    for child in table.select_one("table").children:
        if not isinstance(child, Tag):
            continue
        tds = child.select("td")

        downloads_count = 0
        length = len(tds)
        if length == 6:
            icon, name, description, language, size, date = tds
        elif length >= 9:
            (
                icon,
                name,
                description,
                type_element,
                language,
                size,
                date,
                downloads_element,
                *_,
            ) = tds
            downloads_count = int(text(downloads_element))
            type = text(type_element)
        else:
            continue

        url = name.select_one("a").get("href")
        day, month, year = map(int, text(date).split("."))
        language_text = text(language)
        yield UmkdFile(
            name=text(name),
            description=text(description),
            type=type,
            language=language_text if language_text != "-" else None,
            downloads_count=downloads_count,
            date=int(datetime(year, month, day).timestamp()),
            size=text(size),
            teacher=teacher,
            url=url,
        )


async def get_umkd_files(
    cookies: UserCookies,
    umkd_url: str,
    subject_id: str,
    lang_url: str,
    logger=get_default_logger(__name__),
):
    logger.info(f"get UMKD_URL_FILES {subject_id}")
    html = await fetch(
        lang_url, cookies.as_dict(), {"referer": f"{umkd_url}/{subject_id}"}
    )
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
