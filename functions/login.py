from playwright.async_api import async_playwright, Playwright, Browser
from urllib.parse import urlparse
from asyncio import sleep

from ..exceptions import InvalidCredential, AuthorisationError
from ..utils.logger import get_default_logger


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
        await sleep(1)

    __is_browser_locked = True
    if browser is not None:
        if browser.is_connected():
            __is_browser_locked = False
            return
        logger.info("Stoping browser")
        await browser.close()
        logger.info("Browser stopped")

    if apw is not None:
        logger.info("Stoping apw")
        await apw.stop()
        logger.info("apw stopped")

    apw = await async_playwright().start()
    browser = await apw.firefox.launch(headless=True)
    __is_browser_locked = False


__logining_user = None


async def login(
    username: str,
    password: str,
    login_url: str,
    get_logger=get_default_logger,
):
    try:
        logger = get_logger(__name__)
        global __logining_user
        tries = 0
        while __logining_user is not None:
            logger.info(f"{__logining_user} is logging")
            if tries > 10:
                raise AuthorisationError
            tries += 1
            await sleep(1)
        __logining_user = username
        await ensure_browser()
        context = await browser.new_context()
        page = await context.new_page()

        netloc = urlparse(login_url).netloc

        async def handler(route):
            if netloc not in route.request.url:
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

        await sleep(1)
        if await page.query_selector("#tools") is None:
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
    except Exception as e:
        print(e)
        raise e
    finally:
        __logining_user = None
        await context.close()
