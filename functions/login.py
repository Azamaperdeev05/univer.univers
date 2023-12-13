import aiohttp
from playwright.async_api import async_playwright

# from selenium import webdriver
# from selenium.webdriver import FirefoxOptions
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.common.by import By
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
        browser = await p.firefox.launch(headless=False)
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


# async def login2(username, password, getLogger=getDefaultLogger):
#     logger = getLogger(__name__)
#     options = FirefoxOptions()
#     options.add_argument("--headless")
#     driver = webdriver.Firefox(options=options)

#     logger.info("get LOGIN_URL")
#     driver.get(LOGIN_URL)
#     logger.info("got LOGIN_URL")

#     username_element = driver.find_element(
#         By.CSS_SELECTOR, "label[for='login'] + input"
#     )
#     username_element.clear()
#     username_element.send_keys(username)

#     password_element = driver.find_element(By.CSS_SELECTOR, "[type='password']")
#     password_element.clear()
#     password_element.send_keys(password)

#     password_element.send_keys(Keys.RETURN)
#     logger.info("sent form")

#     while "Бакалавр" not in driver.title:
#         try:
#             error = driver.find_element(By.CSS_SELECTOR, ".ct.warning")
#             if error:
#                 raise InvalidCredential
#         except InvalidCredential as e:
#             raise e
#         except:
#             pass
#         await sleep(0.5)

#     logger.info("got cookies")
#     cookies = driver.get_cookies()
#     driver.close()

#     result = {}
#     for cookie in cookies:
#         result[cookie["name"]] = cookie["value"]

#     if ".ASPXAUTH" not in result:
#         raise InvalidCredential

#     async with aiohttp.ClientSession(cookies=result) as session:
#         async with session.get(LANG_RU_URL):
#             return result
