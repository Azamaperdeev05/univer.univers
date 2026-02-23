from bs4 import BeautifulSoup
from utils.fetch import fetch
from utils import compare_str_without_spaces, to_initials
from univers.base import Univer, Urls
import re
from urllib.parse import urlencode

KazNUUrls = Urls(
    ATTENDANCE_URL="https://univer.kaznu.kz/student/attendance/full/",
    LOGIN_URL="https://univerapi.kaznu.kz/",
    LANG_RU_URL="https://univer.kaznu.kz/lang/change/ru/",
    LANG_KK_URL="https://univer.kaznu.kz/lang/change/kz/",
    LANG_EN_URL="https://univer.kaznu.kz/lang/change/en/",
    ATTESTATION_URL="https://univer.kaznu.kz/student/attestation/",
    SCHEDULE_URL=(
        "https://univer.kaznu.kz/student/myschedule/2025/2/13.01.2026/19.01.2026/"
    ),
    EXAMS_URL="https://univer.kaznu.kz/student/myexam/schedule/",
    TRANSCRIPT_URL_RU="https://univer.kaznu.kz/student/transcript/2",
    TRANSCRIPT_URL_KK="https://univer.kaznu.kz/student/transcript/1/",
    TRANSCRIPT_URL_EN="https://univer.kaznu.kz/student/transcript/6/",
    UMKD_URL="https://univer.kaznu.kz/student/umkd/",
    EDUCATION_PLAN_URL="https://univer.kaznu.kz/student/educplan/",
)
PERSON_URL = "https://pps.kaznu.kz/ru/Main/Search/"


def remove_spaces(text: str):
    return re.sub(r"\s+", " ", text).strip()


class KazNU(Univer):
    def __init__(
        self,
        cookies: dict[str, str] = None,
        language="ru",
        storage=None,
    ) -> None:
        super().__init__(
            cookies=cookies,
            urls=KazNUUrls,
            language=language,
            univer="kaznu",
            storage=storage,
        )

    async def get_schedule(self):
        """KazNU кестесін алу - тақ/жұп апта жүйесін тексеру"""
        schedule = await super().get_schedule()
        
        # Тақ/жұп апта бар ма тексеру
        has_factor = any(lesson.factor is not None for lesson in schedule.lessons)
        
        if has_factor:
            # Егер тақ/жұп апта болса, KSTU-дегідей логика қолдану
            from dataclasses import replace
            lessons = []
            for lesson in schedule.lessons:
                if lesson.factor is None:
                    # Екі аптаға да қосу
                    lessons.append(replace(lesson, factor=True))
                    lessons.append(replace(lesson, factor=False))
                    continue
                lessons.append(lesson)
            
            schedule.lessons = lessons
            schedule.factor = schedule.week % 2 == 0
        else:
            # Тақ/жұп апта жоқ - factor=None қалдыру
            schedule.factor = None
        
        return schedule.with_id()

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
