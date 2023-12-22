import aiohttp

timeout = aiohttp.ClientTimeout(total=10)


async def fetch(
    url: str,
    cookies: dict[str, str] = {},
    headers: dict[str, str] = {},
    method="get",
    data=None,
):
    async with aiohttp.ClientSession(cookies=cookies, timeout=timeout) as session:
        if method == "get":
            async with session.get(
                url,
                timeout=timeout,
                headers=headers,
                allow_redirects=True,
            ) as response:
                return await response.text()
        elif method == "post":
            async with session.post(
                url, data=data, timeout=timeout, headers=headers
            ) as response:
                return await response.text()
