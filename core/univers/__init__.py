from univers.kaznu import KazNU
from univers.kstu import KSTU

univers = {"kstu": KSTU, "kaznu": KazNU}


def get_univer(key: str) -> type[KazNU | KSTU]:
    return univers[key.lower()]
