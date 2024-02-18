import re

from .get_subject_translations import get_subject_translations
from .fetch import fetch
from .merge_attestation_attendance import merge_attestation_attendance
from .storage import Storage
from .logger import create_logger


def to_initials(fullname: str):
    fullname = re.sub("\s+", " ", fullname).strip()
    if " " not in fullname:
        return fullname
    firstname, *lostnames = fullname.split(" ")
    return " ".join([firstname] + [f"{name[0]}." for name in lostnames])


def compare_str_without_spaces(a: str, b: str):
    return a.lower().replace(" ", "") == b.lower().replace(" ", "")
