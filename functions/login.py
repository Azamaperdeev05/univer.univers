from ..exceptions import InvalidCredential, TimeoutError
from ..utils.logger import get_default_logger, Logger
from aiohttp import ClientSession


async def login(
    username: str,
    password: str,
    login_url: str,
    logger: Logger = None,
):
    if logger is None:
        logger = get_default_logger(__name__)
    url = f"{login_url}?login={username}&password={password}"
    async with ClientSession() as session:
        try:
            logger.info("get LOGIN_URL")
            response = await session.get(url)
            logger.info("got LOGIN_URL")
        except:
            raise TimeoutError

        cookies = {}
        for key, value in response.cookies.items():
            cookies[key] = value.value
        if ".ASPXAUTH" in cookies:
            return cookies
        raise InvalidCredential
