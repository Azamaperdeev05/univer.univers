from typing import NamedTuple
from .functions.get_schedule import Lesson, Schedule
from .functions.get_exams import Exam
from .utils.storage import Storage


class Mark(NamedTuple):
    title: str
    value: float


class ActiveMark(NamedTuple):
    title: str
    value: float
    active: int = 1


class Translation(NamedTuple):
    ru: str
    en: str
    kk: str
