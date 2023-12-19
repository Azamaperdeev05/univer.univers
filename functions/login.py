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
    lang_ru_url=LANG_RU_URL,
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

    await page.goto(lang_ru_url)

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
    title = await page.title()
    if "Бакалавр" not in title:
        raise InvalidCredential

    _cookies = await context.cookies()
    logger.info("got cookies")
    cookies = {}
    for cookie in _cookies:
        name = cookie["name"]
        value = cookie["value"]
        cookies[name] = value
    __logining_user = None
    if ".ASPXAUTH" not in cookies:
        logger.info("bad cookies")
        raise InvalidCredential
    await context.close()
    return cookies
