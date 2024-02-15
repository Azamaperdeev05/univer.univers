from asyncio import TimeoutError


class ForbiddenException(Exception):
    pass


class InvalidCredential(Exception):
    pass
