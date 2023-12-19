from .exceptions import *
from .utils.logger import createLogger
from .functions.login import login
from .functions.get_attendance import get_attendance
from .functions.get_attestation import get_attestation
from .functions.get_schedule import get_schedule
from .functions.get_exams import get_exams

from .urls import kstu


def auth(function):
    async def f(*args):
        univer: "Univer" = args[0]
        if univer.cookies is None:
            await univer.login()
        while 1:
            try:
                return await function(*args)
            except ForbiddenException:
                univer.logger.info("relogin")
                await univer.login()

    return f


class Univer:
    def __init__(self, username, password, cookies=None, urls=kstu) -> None:
        self.username = username
        self.password = password
        self.cookies = cookies

        self.urls = urls

        self.logger = self.get_logger(__name__)

    def get_logger(self, name):
        logger = createLogger(
            name, format=f"[%(asctime)s] %(name)s | {self.username} - %(message)s"
        )
        return logger

    async def login(self):
        self.cookies = await login(
            self.username,
            self.password,
            self.get_logger,
            lang_ru_url=self.urls.LANG_RU_URL,
            login_url=self.urls.LOGIN_URL,
        )
        return self.cookies

    @auth
    async def get_attendance(self):
        return await get_attendance(
            self.cookies, self.get_logger, self.urls.ATTENDANCE_URL
        )

    @auth
    async def get_attestation(self):
        return await get_attestation(
            self.cookies,
            self.get_logger,
            attendance_url=self.urls.ATTENDANCE_URL,
            attestation_url=self.urls.ATTESTATION_URL,
        )

    @auth
    async def get_schedule(self):
        return await get_schedule(self.cookies, self.get_logger, self.urls.SCHEDULE_URL)

    @auth
    async def get_exams(self):
        return await get_exams(self.cookies, self.get_logger, self.urls.EXAMS_URL)
