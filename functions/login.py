from playwright.async_api import async_playwright, Playwright, Browser
from asyncio import sleep

from ..exceptions import InvalidCredential
from ..urls import LANG_RU_URL, LOGIN_URL
from ..utils.logger import getDefaultLogger


def string_has_one_substring(string: str, substrings: list[str]):
    for substring in substrings:
        if substring in string:
            return True
    return False


browser: Browser = None
apw: Playwright = None


logger = getDefaultLogger(__name__)

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
    username,
    password,
    getLogger=getDefaultLogger,
    login_url=LOGIN_URL,
):
    logger = getLogger(__name__)
    global __logining_user
    while __logining_user is not None:
        logger.info(f"{__logining_user} is logging")
        await sleep(1)
    __logining_user = username
    await ensure_browser()
    context = await browser.new_context()
    page = await context.new_page()

    logger.info("get LOGIN_URL")
    await page.goto(login_url)
    logger.info("got LOGIN_URL")

    await page.fill("label[for='login'] + input", username)
    await page.fill("[type='password']", password)
    await page.keyboard.press("Enter")
    logger.info("sent form")

    async def handler(route):
        if "univer.kstu.kz" not in route.request.url:
            await route.abort()
            return
        await route.continue_()

    await page.route("**/*", handler)
    await sleep(1)
    if await page.query_selector("#tools") is None:
        __logining_user = None
        raise InvalidCredential

    _cookies = await context.cookies()
    logger.info("got cookies")
    cookies = {}
    for cookie in _cookies:
        name = cookie["name"]
        value = cookie["value"]
        cookies[name] = value
    __logining_user = None
    await context.close()
    if ".ASPXAUTH" not in cookies:
        logger.info("bad cookies")
        raise InvalidCredential
    return cookies
