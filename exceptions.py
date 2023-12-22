from asyncio import TimeoutError


class ForbiddenException(Exception):
    pass


class InvalidCredential(Exception):
    pass


class AuthorisationError(Exception):
    pass
