import aiohttp
from utils.logger import get_default_logger
from functions.login import UserCookies


async def download_file(
    cookies: UserCookies, file_url: str, logger=get_default_logger(__name__)
):
    async with aiohttp.ClientSession(cookies=cookies.as_dict()) as session:
        async with session.get(file_url) as response:
            if response.status != 200:
                return
            yield response.headers
            async for chunk in response.content.iter_chunked(1024):
                yield chunk
