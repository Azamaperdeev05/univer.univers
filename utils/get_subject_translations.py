from bs4 import BeautifulSoup
from ..functions.login import UserCookies
from ..type import Translation
from .auth import check_auth
from .fetch import fetch
from .logger import get_default_logger
from .text import text


async def _get_subject(cookies: UserCookies, education_plan_url: str, lang_url: str):
    html = await fetch(lang_url, cookies.as_dict(), {"referer": education_plan_url})
    soup = BeautifulSoup(html, "html.parser")
    check_auth(soup)
    for row in soup.select("tr.link"):
        _, title, *_ = row.select("td")
        yield text(title)


async def get_subject_translations(
    cookies: UserCookies,
    education_plan_url: str,
    lang_urls: Translation,
    logger=get_default_logger(__name__),
) -> list[Translation]:
    translations: dict[str, list[str]] = {}
    for i, lang_url in enumerate(lang_urls):
        logger.info(f"get EDUCATION_PLAN_URL {i+1}/{len(lang_urls)}")
        async for subject in _get_subject(cookies, education_plan_url, lang_url):
            if lang_url not in translations:
                translations[lang_url] = []
            translations[lang_url].append(subject)
        logger.info(f"got EDUCATION_PLAN_URL {i+1}/{len(lang_urls)}")

    result = []
    for index, ru_subject in enumerate(translations[lang_urls.ru]):
        result.append(
            Translation(
                ru=ru_subject,
                en=translations[lang_urls.en][index],
                kk=translations[lang_urls.kk][index],
            )
        )
    return result
