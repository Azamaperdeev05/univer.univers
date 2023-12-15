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

__is_locked = False


async def ensure_browser():
    global browser
    global apw
    global __is_locked

    while __is_locked:
        logger.info("Waiting browser")
        await sleep(1)

    __is_locked = True
    if browser is not None:
        if browser.is_connected():
            __is_locked = False
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
    __is_locked = False


async def login(username, password, getLogger=getDefaultLogger):
    await ensure_browser()
    logger = getLogger(__name__)
    context = await browser.new_context()
    page = await context.new_page()

    await page.goto(LANG_RU_URL)

    logger.info("get LOGIN_URL")
    await page.goto(LOGIN_URL)
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
    title = await page.title()
    if "Бакалавр" not in title:
        raise IndentationError

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
    await context.close()
    return cookies
