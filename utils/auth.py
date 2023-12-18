from bs4 import BeautifulSoup

from ..exceptions import ForbiddenException


def is_auth(soup: BeautifulSoup):
    return soup.select_one("#tools") is not None


def check_auth(soup: BeautifulSoup):
    if not is_auth(soup):
        raise ForbiddenException
