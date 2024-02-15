from .kaznu import KazNU
from .kstu import KSTU

univers = {"kstu": KSTU, "kaznu": KazNU}


def get_univer(key: str) -> type[KazNU | KSTU]:
    return univers[key.lower()]
