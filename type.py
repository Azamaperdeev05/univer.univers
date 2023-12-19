from typing import NamedTuple


class Mark(NamedTuple):
    title: str
    value: int


class ActiveMark(NamedTuple):
    title: str
    value: int
    active: int = 1
