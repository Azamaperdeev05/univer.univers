import asyncio
from logging import Logger
from pprint import pprint
from bs4 import BeautifulSoup
from ..utils.fetch import fetch
from ..utils import compare_str_without_spaces, to_initials
from ..functions.get_schedule import Lesson
from .base import Univer, Urls
import re
from urllib.parse import urlencode

KazNUUrls = Urls(
    ATTENDANCE_URL="http://univer.kaznu.kz/student/attendance/full/",
    LOGIN_URL="http://univer.kaznu.kz/user/login",
    LANG_RU_URL="http://univer.kaznu.kz/lang/change/ru/",
    LANG_KK_URL="http://univer.kaznu.kz/lang/change/kz/",
    LANG_EN_URL="http://univer.kaznu.kz/lang/change/en/",
    ATTESTATION_URL="http://univer.kaznu.kz/student/attestation/",
    SCHEDULE_URL=(
        "https://univer.kaznu.kz/student/myschedule/2023/1/04.12.2023/10.12.2023/"
    ),
    EXAMS_URL="http://univer.kaznu.kz/student/myexam/schedule/",
)
PERSON_URL = "https://pps.kaznu.kz/ru/Main/Search/"
teachers = {}


def remove_spaces(text: str):
    return re.sub("\s+", " ", text).strip()


async def get_teacher(name: str, logger: Logger):
    firstname, *_ = name.split(" ")
    logger.info(f"get PERSON_URL {firstname}")
    try:
        data = urlencode({"searchname": firstname, "searchtype": "personal_sname"})
        html = await fetch(
            PERSON_URL,
            method="post",
            data=data.encode(),
            headers={
                "referer": "https://pps.kaznu.kz/ru/Main/Search/",
                "content-type": "application/x-www-form-urlencoded",
            },
        )
    except:
        logger.info(f"error PERSON_URL {firstname}")
        return name, None
    logger.info(f"got PERSON_URL {firstname}")

    soup = BeautifulSoup(html, "html.parser")
    for anchor in soup.select(".admin .item-bg a"):
        fullname = remove_spaces(anchor.select_one("h6").text)
        href = anchor["href"]
        if not compare_str_without_spaces(name, to_initials(fullname)):
            continue
        return fullname, f"https://pps.kaznu.kz{href}"

    return name, None


class KazNU(Univer):
    def __init__(
        self,
        username: str,
        password: str,
        cookies: dict[str, str] = None,
        language="ru",
    ) -> None:
        super().__init__(
            username,
            password,
            cookies=cookies,
            urls=KazNUUrls,
            language=language,
            univer="kaznu",
        )

    async def get_schedule(self):
        schedule = await super().get_schedule()

        async def set_teacher(lesson: Lesson):
            teacher = lesson.teacher
            if teacher not in teachers:
                teachers[teacher] = None, None
                link = await get_teacher(teacher, self.logger)
                teachers[teacher] = link
            while teachers[teacher][0] is None:
                await asyncio.sleep(1)
            fullname, href = teachers[teacher]
            lesson.teacher = fullname
            lesson.teacher_link = href

        await asyncio.gather(*[set_teacher(lesson) for lesson in schedule.lessons])
        pprint(schedule)
        return schedule
