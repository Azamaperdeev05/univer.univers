from dataclasses import dataclass, field


@dataclass
class Mark:
    title: str
    value: int
    active: bool = field(default=False)
