import aiohttp


async def fetch(url: str, cookies: dict[str, str]):
    async with aiohttp.ClientSession(cookies=cookies) as session:
        async with session.get(url) as response:
            return await response.text()
