import aiohttp


async def fetch(url: str, cookies: dict[str, str]):
    async with aiohttp.ClientSession(cookies=cookies) as session:
        async with session.get(url, timeout=10) as response:
            return await response.text()
