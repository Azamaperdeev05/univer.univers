import aiohttp
from ..exceptions import TimeoutError

timeout = aiohttp.ClientTimeout(total=5)


async def fetch(url: str, cookies: dict[str, str]):
    try:
        async with aiohttp.ClientSession(cookies=cookies, timeout=timeout) as session:
            async with session.get(url, timeout=timeout) as response:
                return await response.text()
    except:
        raise TimeoutError
