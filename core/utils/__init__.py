import re

from utils.get_subject_translations import get_subject_translations
from utils.fetch import fetch
from utils.merge_attestation_attendance import merge_attestation_attendance
from utils.storage import Storage
from utils.logger import create_logger


def to_initials(fullname: str):
    fullname = re.sub(r"\s+", " ", fullname).strip()
    if " " not in fullname:
        return fullname
    firstname, *lostnames = fullname.split(" ")
    return " ".join([firstname] + [f"{name[0]}." for name in lostnames])


def compare_str_without_spaces(a: str, b: str):
    return a.lower().replace(" ", "") == b.lower().replace(" ", "")
