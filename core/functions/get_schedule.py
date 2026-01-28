from bs4 import BeautifulSoup, Tag
from dataclasses import dataclass, field
from datetime import date, timedelta
from hashlib import md5

from utils.logger import get_default_logger
from utils.fetch import fetch
from utils.auth import check_auth
from utils.text import text
from functions.login import UserCookies


@dataclass
class Lesson:
    subject: str
    teacher: str
    audience: str
    period: str
    day: int
    time: str
    factor: bool
    teacher_link: str = field(default=None)
    id: str = field(default=None)

    def get_id(self):
        data = (
            self.subject,
            self.day,
            self.time,
            self.factor,
            self.teacher,
            self.audience,
            self.period,
            self.teacher_link,
        )
        return hash("-".join(map(str, data)))


@dataclass
class Schedule:
    lessons: list[Lesson]
    factor: bool | None
    week: int

    def with_id(self):
        for lesson in self.lessons:
            lesson.id = lesson.get_id()
        return self


def get_week():
    # 2025-2026 оқу жылы, апта санауды дұрыстау үшін 25 тамыздан бастаймыз
    FIRST_WEEK = "2025-08-25"
    year, month, day = map(int, FIRST_WEEK.split("-"))
    first = date(year, month, day)
    now = date.today()
    weekday = 1 if now.weekday() > 4 else 0
    week = (now - first).days // 7 + 1 + weekday
    return week


def get_current_week_dates():
    """Ағымдағы аптаның дүйсенбі және жексенбі күндерін қайтарады"""
    today = date.today()
    # Аптаның басы (дүйсенбі)
    monday = today - timedelta(days=today.weekday())
    # Аптаның соңы (жексенбі)
    sunday = monday + timedelta(days=6)
    return monday, sunday


def get_semester():
    """Ағымдағы семестрді анықтау (1 - күз, 2 - көктем)"""
    today = date.today()
    # Қыркүйек-желтоқсан = 1 семестр, қаңтар-мамыр = 2 семестр
    if today.month >= 9:
        return today.year, 1  # Күз семестрі
    else:
        return today.year - 1, 2  # Көктем семестрі


def build_schedule_url(base_url: str):
    """Динамикалық кесте URL құрастыру"""
    year, semester = get_semester()
    monday, sunday = get_current_week_dates()

    # URL форматы: /student/myschedule/{year}/{semester}/{start_date}/{end_date}/
    # Мысал: /student/myschedule/2025/2/27.01.2026/02.02.2026/
    start_date = monday.strftime("%d.%m.%Y")
    end_date = sunday.strftime("%d.%m.%Y")

    # base_url-дан домен алу
    from urllib.parse import urlparse

    parsed = urlparse(base_url)
    return f"{parsed.scheme}://{parsed.netloc}/student/myschedule/{year}/{semester}/{start_date}/{end_date}/"


def hash(text: str):
    return md5(text.encode()).hexdigest()


def get_lessons(row: Tag):
    time = text(row.select_one(".time"))
    days = row.select("td.field")
    for day, field in enumerate(days):
        lessons = field.select("div[style]")
        if len(lessons) == 0:
            continue

        for lesson in lessons:
            subject_element = lesson.select_one("p")
            denominator = lesson.select_one(".denominator")
            factor = (
                None
                if denominator is None
                else text(denominator).lower() != "числитель"
            )

            yield Lesson(
                subject=text(subject_element).replace("(", " (").replace("  (", " ("),
                day=day,
                time=time,
                factor=factor,
                teacher=text(subject_element.next_sibling),
                audience=text(lesson.select_one(".aud_faculty").next_sibling),
                period=text(lesson.select_one(".dateStartLbl")),
            )


async def get_schedule(
    cookies: UserCookies,
    schedule_url: str,
    lang_url: str,
    logger=get_default_logger(__name__),
):
    # Динамикалық URL құрастыру (ағымдағы апта күндері)
    dynamic_url = build_schedule_url(schedule_url)
    logger.info(f"get SCHEDULE_URL: {dynamic_url}")
    html = await fetch(lang_url, cookies.as_dict(), {"referer": dynamic_url})
    logger.info("got SCHEDULE_URL")

    soup = BeautifulSoup(html, "html.parser")
    check_auth(soup)
    schedule_table = soup.select(".schedule tr")[1:]
    lessons = []
    for row in schedule_table:
        lessons += list(get_lessons(row))
    return Schedule(lessons=lessons, factor=None, week=get_week())
