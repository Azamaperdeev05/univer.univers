from bs4 import Tag


def text(element: Tag | None):
    if element:
        return element.text.strip()
