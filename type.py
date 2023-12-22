from typing import NamedTuple
from .functions.get_schedule import Lesson, Schedule
from .functions.get_exams import Exam


class Mark(NamedTuple):
    title: str
    value: int


class ActiveMark(NamedTuple):
    title: str
    value: int
    active: int = 1
