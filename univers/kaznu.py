import asyncio
from logging import Logger
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


class KazNU(Univer):
    def __init__(
        self,
        username: str,
        password: str,
        cookies: dict[str, str] = None,
        language="ru",
        storage=None,
    ) -> None:
        super().__init__(
            username,
            password,
            cookies=cookies,
            urls=KazNUUrls,
            language=language,
            univer="kaznu",
            storage=storage,
        )

    async def get_teacher(self, name: str = None):
        if name is None:
            return name, None
        firstname, *_ = name.split(" ")
        data = urlencode({"searchname": firstname, "searchtype": "personal_sname"})
        html = await fetch(
            PERSON_URL,
            method="post",
            data=data.encode(),
            headers={
                "content-type": "application/x-www-form-urlencoded",
            },
        )
        soup = BeautifulSoup(html, "html.parser")
        for anchor in soup.select(".admin .item-bg a"):
            fullname = remove_spaces(anchor.select_one("h6").text)
            href = anchor["href"]
            if not compare_str_without_spaces(name, to_initials(fullname)):
                continue
            return fullname, f"https://pps.kaznu.kz{href}"

        return name, None
