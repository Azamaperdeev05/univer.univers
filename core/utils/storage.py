from typing import Any


class Storage:
    def __setitem__(self, key: str, value: Any):
        raise NotImplementedError

    def __getitem__(self, key: str) -> Any | None:
        raise NotImplementedError

    def __contains__(self, key: str) -> bool:
        return False
