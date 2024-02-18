from typing import NamedTuple
from .functions.get_schedule import Lesson, Schedule
from .functions.get_exams import Exam
from .utils.storage import Storage


class Mark(NamedTuple):
    title: str
    value: int


class ActiveMark(NamedTuple):
    title: str
    value: int
    active: int = 1


class Translation(NamedTuple):
    ru: str
    en: str
    kk: str
