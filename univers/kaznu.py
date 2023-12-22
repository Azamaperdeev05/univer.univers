from .base import Univer, Urls


KazNUUrls = Urls(
    ATTENDANCE_URL="http://univer.kaznu.kz/student/attendance/full/",
    LOGIN_URL="http://univer.kaznu.kz/user/login",
    LANG_RU_URL="http://univer.kaznu.kz/lang/change/ru/",
    LANG_KK_URL="http://univer.kaznu.kz/lang/change/kz/",
    LANG_EN_URL="http://univer.kaznu.kz/lang/change/en/",
    ATTESTATION_URL="http://univer.kaznu.kz/student/attestation/",
    SCHEDULE_URL=(
        "https://univer.kaznu.kz/student/myschedule/2023/1/04.12.2023/10.12.2023/"
    ),
    EXAMS_URL="http://univer.kaznu.kz/student/myexam/schedule/",
)


class KazNU(Univer):
    def __init__(
        self,
        username: str,
        password: str,
        cookies: dict[str, str] = None,
        language="ru",
    ) -> None:
        super().__init__(
            username,
            password,
            cookies=cookies,
            urls=KazNUUrls,
            language=language,
            univer="kaznu",
        )
