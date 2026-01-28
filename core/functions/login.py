from exceptions import InvalidCredential, TimeoutError
from utils.logger import get_default_logger, Logger
from aiohttp import ClientSession
from urllib.parse import urlencode

from typing import NamedTuple


class UserCookies(NamedTuple):
    token: str
    session_id: str
    username: str

    def as_dict(self):
        return {
            ".ASPXAUTH": self.token,
            "ASP.NET_SessionId": self.session_id,
            "user_login": self.username,
        }

    def items(self):
        return self.as_dict().items()

    @classmethod
    def from_cookies(cls, cookies: dict):
        return cls(
            token=cookies[".ASPXAUTH"],
            session_id=cookies["ASP.NET_SessionId"],
            username=cookies.get("user_login", "<unknown>"),
        )


async def login(
    username: str,
    password: str,
    login_url: str,
    logger: Logger = None,
) -> UserCookies:
    if logger is None:
        logger = get_default_logger(__name__)
    query_string = urlencode({"login": username, "password": password})
    url = f"{login_url}?{query_string}"
    async with ClientSession() as session:
        try:
            logger.info("get LOGIN_URL")
            response = await session.get(url)
            logger.info("got LOGIN_URL")
        except:
            raise TimeoutError

        if ".ASPXAUTH" not in response.cookies:
            raise InvalidCredential
        return UserCookies(
            token=response.cookies[".ASPXAUTH"].value,
            session_id=response.cookies["ASP.NET_SessionId"].value,
            username=username,
        )
