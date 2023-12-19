import aiohttp
from ..exceptions import TimeoutError

timeout = aiohttp.ClientTimeout(total=10)


async def fetch(url: str, cookies: dict[str, str], headers: dict[str, str] = {}):
    try:
        async with aiohttp.ClientSession(cookies=cookies, timeout=timeout) as session:
            async with session.get(
                url, timeout=timeout, headers=headers, allow_redirects=True
            ) as response:
                return await response.text()
    except:
        raise TimeoutError
