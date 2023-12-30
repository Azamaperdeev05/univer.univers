from playwright.async_api import (
    async_playwright,
    Playwright,
    Browser,
    Route,
    BrowserContext,
)
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from urllib.parse import urlparse
import asyncio

from ..exceptions import InvalidCredential, AuthorizationError, TimeoutError
from ..utils.logger import get_default_logger, Logger
from dataclasses import dataclass, field
from datetime import datetime


def get_now():
    return datetime.now().timestamp()


@dataclass
class UserCookies:
    cookies: dict[str, str]
    timestamp: float = field(default_factory=get_now)


def string_has_one_substring(string: str, substrings: list[str]):
    for substring in substrings:
        if substring in string:
            return True
    return False


browser: Browser = None
apw: Playwright = None


logger = get_default_logger(__name__)

__is_browser_locked = False


async def ensure_browser():
    global browser
    global apw
    global __is_browser_locked

    while __is_browser_locked:
        logger.info("Waiting browser")
        await asyncio.sleep(1)

    __is_browser_locked = True
    if browser is not None:
        if browser.is_connected():
            __is_browser_locked = False
            return
        logger.info("Stopping browser")
        await browser.close()
        logger.info("Browser stopped")

    if apw is not None:
        logger.info("Stopping apw")
        await apw.stop()
        logger.info("apw stopped")

    apw = await async_playwright().start()
    browser = await apw.firefox.launch(headless=True)
    __is_browser_locked = False


queue: dict[tuple, UserCookies] = {}


async def __login(
    username: str,
    password: str,
    login_url: str,
    context: BrowserContext,
    logger=get_default_logger(__name__),
):
    page = await context.new_page()

    url = urlparse(login_url)

    async def handler(route: Route):
        if url.netloc not in route.request.url or route.request.url.endswith(".png"):
            await route.abort()
            return
        await route.continue_()

    await page.route("**/*", handler)

    logger.info("get LOGIN_URL")
    await page.goto(login_url)
    logger.info("got LOGIN_URL")

    await page.fill("label[for='login'] + input", username)
    await page.fill("[type='password']", password)
    await page.keyboard.press("Enter")
    logger.info("sent form")

    news_url = f"//{url.netloc}/news"
    login_url = f"//{url.netloc}/user/login?ReturnUrl="

    sleep_counter = 0
    while sleep_counter < 30:
        await asyncio.sleep(1)
        if login_url in page.url:
            raise InvalidCredential
        if news_url in page.url:
            break
        sleep_counter += 1
    else:
        raise TimeoutError

    await page.wait_for_url("**/news/**")
    if await page.query_selector("#login_form") is not None:
        raise InvalidCredential

    _cookies = await context.cookies()
    logger.info("got cookies")
    cookies = {}
    for cookie in _cookies:
        name = cookie["name"]
        value = cookie["value"]
        cookies[name] = value
    if ".ASPXAUTH" not in cookies:
        logger.info("bad cookies")
        raise InvalidCredential

    return cookies


__current_user = None


async def login(
    username: str,
    password: str,
    login_url: str,
    logger: Logger,
):
    global __current_user
    context = None

    for key in queue:
        user = queue[key]
        if user is None:
            continue
        if now - user.timestamp > 600:
            del queue[key]

    tries = 0
    while __current_user is not None:
        if tries > 20:
            raise AuthorizationError
        logger.info(f"waiting for {__current_user} login")
        tries += 1
        await asyncio.sleep(1)

    key = (username, password, login_url)
    if key in queue:
        while queue[key] is None:
            logger.info(f"waiting for another login")
            await asyncio.sleep(1)
        now = get_now()
        user = queue[key]
        if now - user.timestamp <= 600:
            return user.cookies

    queue[key] = None

    try:
        __current_user = username
        await ensure_browser()
        context = await browser.new_context()
        user = await __login(
            username, password, login_url, context=context, logger=logger
        )
        queue[key] = UserCookies(user)
        return user
    except PlaywrightTimeoutError:
        raise TimeoutError
    except Exception as e:
        raise e
    finally:
        __current_user = None
        if context:
            await context.close()
