from .exceptions import ForbiddenException
from .utils.logger import createLogger
from .functions.login import login
from .functions.get_attendance import get_attendance
from .functions.get_attestation import get_attestation


def auth(function):
    async def f(*args):
        self: "Univer" = args[0]
        if self.cookies is None:
            await self.login()
        while 1:
            try:
                return await function(*args)
            except ForbiddenException:
                self.logger.info("relogin")
                await self.login()

    return f


class Univer:
    def __init__(self, username, password, cookies=None) -> None:
        self.username = username
        self.password = password
        self.cookies = cookies

        self.logger = self.get_logger(__name__)

    def get_logger(self, name):
        logger = createLogger(
            name, format=f"[%(asctime)s] %(name)s | {self.username} - %(message)s"
        )
        return logger

    async def login(self):
        self.cookies = await login(self.username, self.password, self.get_logger)
        return self.cookies

    @auth
    async def get_attendance(self):
        return await get_attendance(self.cookies, self.get_logger)

    @auth
    async def get_attestation(self):
        return await get_attestation(self.cookies, self.get_logger)
