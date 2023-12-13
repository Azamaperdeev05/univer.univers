from playwright.async_api import async_playwright
from asyncio import sleep

from ..exceptions import InvalidCredential
from ..urls import LANG_RU_URL, LOGIN_URL
from ..utils.logger import getDefaultLogger


def string_has_one_substring(string: str, substrings: list[str]):
    for substring in substrings:
        if substring in string:
            return True
    return False


async def login(username, password, getLogger=getDefaultLogger):
    logger = getLogger(__name__)
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
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

        while "Бакалавр" not in await page.title():
            error = await page.query_selector(".ct.warning")
            if error:
                raise InvalidCredential
            await sleep(0.5)
        _cookies = await context.cookies()
        logger.info("got cookies")
        cookies = {}
        for cookie in _cookies:
            name = cookie["name"]
            value = cookie["value"]
            cookies[name] = value

        if ".ASPXAUTH" not in cookies:
            raise InvalidCredential
        return cookies
